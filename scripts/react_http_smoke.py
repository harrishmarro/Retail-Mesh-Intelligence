"""Verify the packaged React shell and static-asset boundary on a temporary DB."""
import os,re,subprocess,sys,tempfile,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temporary:
 p=subprocess.Popen([sys.executable,str(ROOT/'src/main.py'),'--db',str(Path(temporary)/'static.db'),'--port','8098'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  assert p.stdout.readline()
  base='http://127.0.0.1:8098'
  with urllib.request.urlopen(base) as response:
   shell=response.read().decode();assert '<div id="root"></div>' in shell
   assert "script-src 'self'" in response.headers['Content-Security-Policy']
   assert response.headers['X-Content-Type-Options']=='nosniff'
  assets=re.findall(r'(?:src|href)="(/assets/[^\"]+)"',shell);assert assets
  for asset in assets:
   with urllib.request.urlopen(base+asset) as response:
    body=response.read();assert body
    assert response.headers['Content-Type'].startswith('text/javascript' if asset.endswith('.js') else 'text/css')
  font=next((ROOT/'src/ui/react-dist/assets').glob('*.woff2'))
  with urllib.request.urlopen(base+'/assets/'+font.name) as response:assert response.headers['Content-Type']=='font/woff2'
  for path in ['/assets/%2e%2e/portal.html','/assets/%2e%2e/%2e%2e/%2e%2e/data/retail_mesh.db','/assets/missing.js']:
   try:urllib.request.urlopen(base+path);raise AssertionError(path)
   except urllib.error.HTTPError as e:assert e.code==404
  print('PASS: React shell, CSP, JavaScript/CSS/font MIME types, missing assets and encoded path traversal')
 finally:p.terminate();p.wait(timeout=10)
