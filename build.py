#!/usr/bin/env python3
"""Build index.html (the deployed app) from macro-ledger.html (the source).

    python3 build.py

macro-ledger.html is artifact-shaped: it has no <head>, because when it is
published as a Claude Artifact the publisher supplies one. This wraps it in a
real HTML document with the meta tags, manifest link and service-worker
registration a home-screen web app needs.

Never edit index.html by hand — it is overwritten on every build.

After building, bump CACHE in sw.js (v4 -> v5) or installed phones will keep
serving the old cached copy, then commit and push. GitHub Pages redeploys
automatically, usually within two minutes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "macro-ledger.html")
OUT = os.path.join(HERE, "index.html")

BANNER = """<!--
  GENERATED FILE — DO NOT EDIT.
  Built from macro-ledger.html by build.py. Any change made here is lost on
  the next build. Edit macro-ledger.html instead, then run: python3 build.py
-->
"""

HEAD_OPEN = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Daily macro and training ledger.">
<meta name="theme-color" content="#E9ECEC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1316" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Macros">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
'''

SAFE_AREA = '''
<style>
/* home-screen standalone: keep content clear of the notch and home indicator */
.wrap{
  padding-top: calc(18px + env(safe-area-inset-top));
  padding-bottom: calc(72px + env(safe-area-inset-bottom));
  padding-left: calc(14px + env(safe-area-inset-left));
  padding-right: calc(14px + env(safe-area-inset-right));
}
</style>
'''

SW_REG = '''
<script>
if("serviceWorker" in navigator){
  window.addEventListener("load", ()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));
}
</script>
</body>
</html>
'''

src = open(SRC, encoding="utf-8").read()
split = src.index("</style>") + len("</style>")
head_inner, body = src[:split], src[split:]

out = BANNER + HEAD_OPEN + head_inner + SAFE_AREA + "</head>\n<body>" + body + SW_REG
open(OUT, "w", encoding="utf-8").write(out)

# The head is the part that breaks silently — a build once shipped with the
# whole block missing, which renders at desktop width on a phone. Assert it.
REQUIRED = ["<!doctype html>", 'charset="utf-8"', 'name="viewport"', 'rel="manifest"',
            "apple-touch-icon", "apple-mobile-web-app-capable", "</head>", "<body>",
            "serviceWorker", "</html>"]
missing = [n for n in REQUIRED if n not in out]
if missing:
    sys.exit(f"BUILD FAILED — missing from output: {', '.join(missing)}")

foods = out.count('","Malaysian"],') + out.count('","Franchise"],')
print(f"index.html: {len(out.encode('utf-8')):,} bytes, head verified")
print("Next: bump CACHE in sw.js, then commit and push.")
