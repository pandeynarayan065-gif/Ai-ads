#!/usr/bin/env bash
# Redeploy the lead board to https://misfits-leads.vercel.app (Vercel token is injected by the session proxy;
# locally, export VERCEL_TOKEN). Rebuild first: python3 build_board.py, then regenerate site/index.html.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import json;print(json.dumps({"name":"misfits-leads","target":"production","projectSettings":{"framework":None},"files":[{"file":f,"data":open("site/"+f).read()} for f in ("index.html","robots.txt")]}))' > /tmp/mf-deploy.json
curl -sS -X POST "https://api.vercel.com/v13/deployments?teamId=team_GL8YRqtdJEPWcEzPb3EuOuOL&skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer ${VERCEL_TOKEN:-proxy-injected}" -H "Content-Type: application/json" --data @/tmp/mf-deploy.json \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("readyState"),d.get("alias"),d.get("error"))'
