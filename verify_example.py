import json
from pathlib import Path
from aggregate import aggregate
root=Path(__file__).resolve().parent
cases=json.loads((root/'cases.json').read_text())
for c in cases:
    assert aggregate(c['input'])==c['expected'],c['id']
print(json.dumps({'cases_passed':len(cases),'commercial_evidence':False}))
