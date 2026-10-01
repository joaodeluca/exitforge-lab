# ExitForge Lab

Free technical sample of a small automation running outside its original editor. Not a universal converter, paid service, or production equivalence claim.

The Python sample follows the object append/tag subset of the public [Multi Source Aggregation workflow](https://github.com/c4snipes/n8n-transpiler/blob/b996ed54e992700c837c2ae579a893a2c34ce3f7/examples/content_aggregation/workflow.json). Original upstream authored by c4snipes, commit b996ed54e992700c837c2ae579a893a2c34ce3f7; upstream metadata declares MIT. This repository does not redistribute the upstream source code. No affiliation.

## Run offline

Download and extract `exitforge-example.zip`, then run:

```sh
python3 aggregate.py examples/input.json
```

Only Python standard library is required. The browser demo is a JavaScript port of the offline subset; it does not transmit inputs. Inputs and displayed KPI values are fictional. Do not upload customer documents or secrets to public issues.

Verify the local cases with `python3 verify_example.py` and the HTTP adapter with `python3 -m unittest -v test_http_adapter.py`. Twenty cases and six HTTP test methods exercise supported behavior; they are constructed tests, not customer migrations.

## Optional public HTTP example

```sh
python3 live_demo.py https://api.github.com/repos/c4snipes/n8n-transpiler https://api.github.com/repos/n8n-io/n8n
```

This makes two explicit, read-only public GET requests. The small adapter requires public HTTPS and refuses redirects, credentials in URLs and oversized bodies. It reads no credentials or environment/proxy settings. Loopback is a separate explicit opt-in for tests. This is not a production security certification. `public-run.json` records an executed run without republishing provider bodies. Its objects contain repository metadata, **not traffic or revenue**; `daily-kpi` is simply the preserved sample tag. The example.com URLs in the upstream workflow were replaced explicitly. No write or email is performed.

## Boundaries

- Offline inputs replace HTTP acquisition with supplied snapshots; timestamps/status are not authenticated.
- Successful JSON objects are appended and marked `report_type: daily-kpi`.
- Timeout produces UNKNOWN and no partial output. Other failures produce explicit error codes.
- Arrays/null are rejected. Null handling differs from the inspected upstream Merge emitter.
- Neither the transpiler nor n8n was executed. No comparative speed, savings, buyer demand or production acceptance is established.
- JSON numbers follow host-language limits; this is not a financial calculation or reconciler.

Technical differences can be reported in repository issues using public or fictional examples. Running the sample is not participation in a paid commercial study. No checkout, account creation or payment collection.
