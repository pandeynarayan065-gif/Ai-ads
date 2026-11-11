"""Deploy the Avrana pitch site folder to https://misfits-avrana.vercel.app (Vercel token injected by the session proxy;
locally set VERCEL_TOKEN). Usage: python3 deploy_site.py <site_folder>"""
import hashlib, json, os, sys, urllib.request
TEAM = "team_GL8YRqtdJEPWcEzPb3EuOuOL"; TOKEN = os.environ.get("VERCEL_TOKEN", "proxy-injected")
root = sys.argv[1]; files = []
for d, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(d, f); rel = os.path.relpath(p, root); b = open(p, "rb").read(); sha = hashlib.sha1(b).hexdigest()
        urllib.request.urlopen(urllib.request.Request(f"https://api.vercel.com/v2/files?teamId={TEAM}", data=b, method="POST",
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/octet-stream", "x-vercel-digest": sha}), timeout=120).read()
        files.append({"file": rel, "sha": sha, "size": len(b)})
body = json.dumps({"name": "misfits-avrana", "target": "production", "projectSettings": {"framework": None}, "files": files}).encode()
r = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://api.vercel.com/v13/deployments?teamId={TEAM}&skipAutoDetectionConfirmation=1",
    data=body, method="POST", headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}), timeout=120).read())
print(r.get("readyState"), r.get("alias"))
