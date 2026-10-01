"""Optional original stdlib GET adapter; no env, proxy, auth or remote execution.

Public HTTPS only (port 443), or explicit opt-in loopback for local tests.
DNS answers are validated and the connection uses the selected numeric address,
without resolving it again. TLS still verifies the original hostname. All
redirects are refused. This small adapter is not a production security audit.
"""
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import json
from pathlib import Path
import queue
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit

MAX_BYTES = 1_048_576


class Refused(ValueError):
    pass


def is_public_unicast(ip):
    return ip.is_global and not (ip.is_multicast or ip.is_reserved or ip.is_unspecified or getattr(ip, "is_site_local", False))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_url(url, allow_loopback=False):
    if type(url) is not str or len(url) > 2048 or any(ord(c) < 33 or ord(c) > 126 for c in url) or "\\" in url:
        raise Refused("INVALID_URL")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise Refused("UNSUPPORTED_URL")
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise Refused("USERINFO_QUERY_FRAGMENT_FORBIDDEN")
    host = parsed.hostname.lower()
    if host == "metadata" or host.endswith(".internal"):
        raise Refused("METADATA_HOST_FORBIDDEN")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError:
            raise Refused("INVALID_PORT") from None
    is_loopback = literal is not None and literal.is_loopback
    if literal is not None and not is_public_unicast(literal) and not (is_loopback and allow_loopback):
        raise Refused("NON_PUBLIC_ADDRESS")
    # Hostname 'localhost' must still resolve solely to loopback below.
    loopback_candidate = is_loopback or host == "localhost"
    if parsed.scheme != "https" and not (allow_loopback and loopback_candidate):
        raise Refused("HTTPS_REQUIRED")
    if port != 443 and not (allow_loopback and loopback_candidate):
        raise Refused("PUBLIC_PORT_MUST_BE_443")
    return parsed, host, port


def resolve_pinned(host, port, timeout, allow_loopback):
    try:
        explicit_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        explicit_loopback = host == "localhost"
    result = queue.Queue(maxsize=1)

    def resolve():
        try:
            result.put(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
        except OSError as error:
            result.put(error)

    threading.Thread(target=resolve, daemon=True).start()
    try:
        addresses = result.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError("DNS_TIMEOUT") from None
    if isinstance(addresses, Exception):
        raise addresses
    if not addresses:
        raise Refused("NO_ADDRESS")
    for family, _, _, _, address in addresses:
        ip = ipaddress.ip_address(address[0])
        if family not in (socket.AF_INET, socket.AF_INET6) or not (is_public_unicast(ip) or (allow_loopback and explicit_loopback and ip.is_loopback)):
            raise Refused("NON_PUBLIC_DNS_ADDRESS")
        if host == "localhost" and not ip.is_loopback:
            raise Refused("LOCALHOST_NOT_LOOPBACK")
    return addresses[0]


def tls_context():
    # macOS system CA bundle when present; never disable verification.
    system_bundle = Path("/etc/ssl/cert.pem")
    return ssl.create_default_context(cafile=str(system_bundle) if system_bundle.is_file() else None)


def get_json(url, *, timeout=10, allow_loopback=False):
    if not 0 < timeout <= 30:
        raise ValueError("timeout must be >0 and <=30 seconds")
    event = {"url": url, "started_at_utc": utc_now(), "method": "GET", "status": "failed", "http_status": None, "request_count": 0, "body_bytes": 0, "body_sha256": None}
    connection = None
    response = None
    sock = None
    timer = None
    timed_out = threading.Event()
    deadline = time.monotonic() + timeout

    def remaining():
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise TimeoutError("TIMEOUT")
        return seconds

    try:
        parsed, host, port = validate_url(url, allow_loopback)
        family, kind, protocol, _, address = resolve_pinned(host, port, remaining(), allow_loopback)
        event["resolved_ip"] = address[0]
        sock = socket.socket(family, kind, protocol)
        sock.settimeout(remaining())
        sock.connect(address)
        if parsed.scheme == "https":
            sock.settimeout(remaining())
            sock = tls_context().wrap_socket(sock, server_hostname=host)

        def abort_at_deadline():
            timed_out.set()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        timer = threading.Timer(remaining(), abort_at_deadline)
        timer.daemon = True
        timer.start()
        connection = http.client.HTTPConnection(host, port, timeout=remaining())
        connection.sock = sock
        event["request_count"] = 1
        connection.request("GET", parsed.path or "/", headers={"Accept": "application/json", "Accept-Encoding": "identity", "User-Agent": "ExitForge-public-read-demo/1.0", "Connection": "close"})
        # Manage the response directly: HTTPConnection.getresponse() closes its
        # socket for Connection: close responses, preventing deadline updates.
        response = http.client.HTTPResponse(sock)
        response.begin()
        event["http_status"] = response.status
        if 300 <= response.status < 400:
            raise Refused("REDIRECT_FORBIDDEN")
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise Refused("ENCODED_BODY_FORBIDDEN")
        length = response.getheader("Content-Length")
        if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
            raise Refused("BODY_LIMIT_OR_INVALID_LENGTH")
        chunks, count = [], 0
        while True:
            sock.settimeout(remaining())
            chunk = response.read1(min(65_536, MAX_BYTES + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > MAX_BYTES:
                raise Refused("BODY_TOO_LARGE")
        if timed_out.is_set():
            raise TimeoutError("TIMEOUT")
        body = b"".join(chunks)
        event["body_bytes"] = len(body)
        event["body_sha256"] = hashlib.sha256(body).hexdigest()
        if length is not None and len(body) != int(length):
            raise Refused("TRUNCATED_BODY")
        if not 200 <= response.status < 300:
            raise Refused("HTTP_" + str(response.status))
        data = json.loads(body.decode("utf-8"))
        if type(data) is not dict:
            raise Refused("EXPECTED_JSON_OBJECT")
        from aggregate import finite_json
        finite_json(data)
        event.update(status="ok", json=data)
    except (TimeoutError, socket.timeout):
        event.update(status="unknown", error="TIMEOUT")
    except (ValueError, OSError, http.client.HTTPException) as error:
        if timed_out.is_set():
            event.update(status="unknown", error="TIMEOUT")
        else:
            event["error"] = str(error) if isinstance(error, Refused) else type(error).__name__
    finally:
        if timer:
            timer.cancel()
        if response:
            response.close()
        if connection:
            connection.close()
        elif sock:
            sock.close()
        event["finished_at_utc"] = utc_now()
    return event
