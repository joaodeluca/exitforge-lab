# ExitForge Lab

Free technical sample of a small automation running outside its original editor. Not a universal converter or production equivalence claim. Separate service-scoping enquiries are described below.

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

## Considering a commissioned extraction?

If you have a concrete reason to move a small workflow out of its current automation runtime, you can [request a scope assessment](https://github.com/joaodeluca/exitforge-lab/issues/new?template=service-enquiry.yml). The proposed pilot is an independent Python program, agreed input/output cases, instructions, explicit behavioral differences, and one correction. Initial reference price: **BRL 1,490 for up to eight eligible deterministic nodes**; price and delivery time depend on the actual scope. AI agents perform the work; João de Luca is the accountable owner. No prior customer migrations or full human review are claimed.

This is a **scoping enquiry, not an available checkout or service agreement**. Contracting and settlement are not enabled yet; no order or payment is requested. The current scope excludes OAuth, external writes, dashboards, schedulers, durable state and long waits. An eight-node count alone does not establish eligibility. The sample is free and remains separate from any future commissioned work.

Describe only the runtime, reason for leaving, required behavior and a public or fictional example. Issues are public: do not include emails, phone numbers, secrets, private exports or customer data. Public scoping creates no obligation to buy and does not authorize individual quotation in research.
