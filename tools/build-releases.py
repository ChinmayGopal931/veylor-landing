#!/usr/bin/env python3
"""Builds releases/index.html, https://veylor.cash/releases/, from Veylor's GitHub releases.

Run it from the repository root once a release is published, then commit the page:

    python3 -I tools/build-releases.py

tools/releases.json holds what GitHub can't say: the cards' words, the file
labels and the Android signing certificate. The rest comes from GitHub's API
through `gh`: every release tagged veylor-<platform>/v<version>, its notes, the
commit its tag names, its files with their sizes and SHA-256 digests, and each
file's build attestation. The page is not written when a release's SHA256SUMS
disagrees with GitHub's digests, when an attestation names another repository
or workflow, or when a file's attestations name no build of its tag's commit.

The page loads nothing from GitHub: its links go there only when clicked.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "tools" / "releases.json").read_text())
REPO = CONFIG["repo"]
GITHUB = f"https://github.com/{REPO}"
TAG = re.compile(r"veylor-(android|linux|macos|windows)/v(\d+\.\d+\.\d+)")
PLATFORM_NAMES = {"android": "Android", "linux": "Linux", "macos": "Mac", "windows": "Windows"}
SLSA_PROVENANCE = "https://slsa.dev/provenance/v1"
OUT = ROOT / "releases" / "index.html"


def fail(message: str):
    sys.exit(f"build-releases: {message}")


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def gh_api(path: str):
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if result.returncode != 0:
        if "HTTP 404" in result.stderr:
            return None
        fail(f"gh api {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def fetch(url: str, limit: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "veylor-releases-page"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(limit + 1)
    if len(body) > limit:
        fail(f"{url} is larger than {limit} bytes")
    return body


def unsnappy(data: bytes) -> bytes:
    """Snappy's block format, which GitHub stores attestation bundles in (bundle_url)."""
    pos, size, shift = 0, 0, 0
    while True:
        byte = data[pos]
        pos += 1
        size |= (byte & 0x7F) << shift
        if byte < 0x80:
            break
        shift += 7
    out = bytearray()
    while pos < len(data):
        tag = data[pos]
        pos += 1
        if tag & 3 == 0:  # a literal
            n = tag >> 2
            if n >= 60:
                width = n - 59
                n = int.from_bytes(data[pos:pos + width], "little")
                pos += width
            out += data[pos:pos + n + 1]
            pos += n + 1
            continue
        if tag & 3 == 1:
            n, offset = ((tag >> 2) & 7) + 4, ((tag >> 5) << 8) | data[pos]
            pos += 1
        elif tag & 3 == 2:
            n, offset = (tag >> 2) + 1, int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
        else:
            n, offset = (tag >> 2) + 1, int.from_bytes(data[pos:pos + 4], "little")
            pos += 4
        if not 0 < offset <= len(out):
            fail("an attestation bundle is not valid Snappy")
        for _ in range(n):  # a copy may overlap what it writes
            out.append(out[-offset])
    if len(out) != size:
        fail("an attestation bundle is not valid Snappy")
    return bytes(out)


# ---------------------------------------------------------------- GitHub's data


def file_entry(name: str) -> tuple[int, dict]:
    for order, entry in enumerate(CONFIG["files"]):
        if re.search(entry["match"], name):
            return order, entry
    fail(f"tools/releases.json labels no file like {name}")


def check_sums(tag: str, files: list[dict]) -> None:
    sums = next((f for f in files if f["name"] == "SHA256SUMS"), None)
    if sums is None:
        fail(f"{tag} has no SHA256SUMS")
    body = fetch(sums["url"], 64 * 1024)
    if hashlib.sha256(body).hexdigest() != sums["sha256"]:
        fail(f"{tag}: the SHA256SUMS served is not the one GitHub has a digest of")
    listed = {}
    for line in body.decode("utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](\S+)", line)
        if not match:
            fail(f"{tag}: SHA256SUMS has a line it can't read: {line!r}")
        listed[match.group(2)] = match.group(1)
    names = {f["name"] for f in files} - {"SHA256SUMS"}
    if set(listed) != names:
        fail(f"{tag}: SHA256SUMS lists {sorted(listed)}, but the release has {sorted(names)}")
    for f in files:
        if f["name"] != "SHA256SUMS" and listed[f["name"]] != f["sha256"]:
            fail(f"{tag}: SHA256SUMS and GitHub disagree about {f['name']}")


def attestation(tag: str, platform: str, commit: str, f: dict):
    """The build that made this file, from its attestations, or None when it has none."""
    data = gh_api(f"repos/{REPO}/attestations/sha256:{f['sha256']}")
    items = (data or {}).get("attestations") or []
    if not items:
        return None
    workflow = CONFIG["workflows"].get(platform)
    for item in items:
        # GitHub serves a bundle inline, or (lately) compressed at bundle_url.
        bundle = item.get("bundle")
        if not bundle and item.get("bundle_url"):
            bundle = json.loads(unsnappy(fetch(item["bundle_url"], 1 << 20)))
        if not bundle:
            fail(f"{tag}: {f['name']}'s attestation came without its bundle")
        statement = json.loads(base64.b64decode(bundle["dsseEnvelope"]["payload"]))
        if statement.get("predicateType") != SLSA_PROVENANCE:
            continue
        if not any(s.get("digest", {}).get("sha256") == f["sha256"] for s in statement.get("subject", [])):
            continue
        build = statement["predicate"]["buildDefinition"]
        source = build["externalParameters"]["workflow"]
        if source.get("repository") != GITHUB or source.get("path") != workflow:
            fail(f"{tag}: {f['name']} is attested by {source.get('repository')} {source.get('path')}")
        built_from = build["resolvedDependencies"][0]["digest"]["gitCommit"]
        if built_from != commit:
            continue
        run = statement["predicate"]["runDetails"]["metadata"]["invocationId"]
        return {"run": re.sub(r"/attempts/\d+$", "", run), "commit": built_from}
    fail(f"{tag}: {f['name']} is attested, but by no build of {commit[:9]}, the commit its tag names")


def load_releases() -> list[dict]:
    found = []
    for release in gh_api(f"repos/{REPO}/releases?per_page=100") or []:
        match = TAG.fullmatch(release["tag_name"])
        if not match or release["draft"]:
            continue
        tag = release["tag_name"]
        platform, version = match.groups()
        commit = gh_api(f"repos/{REPO}/commits/{tag}")["sha"]
        files = []
        for asset in release["assets"]:
            digest = asset.get("digest") or ""
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                fail(f"{tag}: GitHub has no SHA-256 for {asset['name']}")
            order, entry = file_entry(asset["name"])
            files.append({
                "name": asset["name"], "size": asset["size"], "sha256": digest[7:],
                "url": asset["browser_download_url"], "order": order, "label": entry["label"],
                "signed_from": re.sub(r"\.apk$", entry["signed_from"], asset["name"]) if entry.get("signed_from") else None,
            })
        check_sums(tag, files)
        for f in files:
            f["build"] = None if f["name"] == "SHA256SUMS" else attestation(tag, platform, commit, f)
        by_name = {f["name"]: f for f in files}
        for f in files:
            if f["signed_from"]:
                unsigned = by_name.get(f["signed_from"])
                if not unsigned or not unsigned["build"]:
                    fail(f"{tag}: {f['name']} is signed from {f['signed_from']}, which the release lacks or nothing attests")
        files.sort(key=lambda f: (f["order"], f["name"]))
        found.append({
            "tag": tag, "platform": platform, "version": version, "commit": commit,
            "title": release["name"] or tag, "notes": release["body"] or "",
            "published": release["published_at"], "prerelease": release["prerelease"],
            "url": release["html_url"], "files": files,
        })
    found.sort(key=lambda r: r["published"], reverse=True)
    return found


# ------------------------------------------------------------------ formatting


def day(iso: str) -> str:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{t:%b} {t.day}, {t.year}"


def size(n: int) -> str:
    for unit, scale in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if n >= scale:
            return f"{n / scale:.1f} {unit}"
    return f"{n} bytes"


def inline(text: str) -> str:
    """Markdown's code spans, bold and links, escaped; nothing else."""
    out = []
    for part in re.split(r"(`[^`]+`)", text):
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            out.append(f"<code>{esc(part[1:-1])}</code>")
            continue
        s = esc(part)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\[([^\]]+)\]\((https://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
        out.append(s)
    return "".join(out)


def notes_html(body: str) -> str:
    """The release notes' Markdown (headings, paragraphs, bullets), without the title."""
    blocks, para, items = [], [], None

    def flush():
        nonlocal para, items
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para = []
        if items is not None:
            blocks.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items = None

    for line in body.replace("\r\n", "\n").split("\n"):
        if line.startswith("# "):
            flush()
        elif line.startswith("## "):
            flush()
            blocks.append(f"<h4>{inline(line[3:].strip())}</h4>")
        elif line.startswith("- "):
            if para:
                flush()
            items = (items or []) + [line[2:].strip()]
        elif line.startswith("  ") and line.strip() and items:
            items[-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if items is not None:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(blocks)


def first_bullet(body: str) -> str:
    match = re.search(r"^- (.+(?:\n  .+)*)", body, re.M)
    text = re.sub(r"\s+", " ", match.group(1)) if match else ""
    return re.sub(r"[`*]", "", text)


# ----------------------------------------------------------- the site's chrome


def site_chrome():
    """The top bar, the wordmark's defs, the footer and the platform icons, as the other pages draw them."""
    how = (ROOT / "how-it-works" / "index.html").read_text()
    top = how[how.index('<div class="topbar">'):how.index("<main>")].rstrip()
    defs = re.search(r'<svg class="defs".*?</svg>', how, re.S).group(0)
    footer = how[how.index('<footer class="site-footer">'):how.index("</footer>") + len("</footer>")]
    home = (ROOT / "index.html").read_text()
    icons = dict((name, svg) for svg, name in re.findall(
        r'(<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">.*?</svg>)'
        r'<span class="platform-note">[^<]*</span><span class="platform-name">([^<]+)</span>', home))
    for p in CONFIG["platforms"]:
        if p["icon"] not in icons:
            fail(f"the home page draws no {p['icon']} tile to take its icon from")
    return top, defs, footer, icons


# --------------------------------------------------------------------- the page


def asset(release: dict, pattern: str) -> dict:
    for f in release["files"]:
        if re.search(pattern, f["name"]):
            return f
    fail(f"{release['tag']} has no file like {pattern}")


def card(p: dict, release, icons: dict) -> str:
    soon = p["status"] == "Coming soon"
    if release:
        head = f'<div class="rel-version">v{esc(release["version"])}</div>'
        meta = " · ".join([day(release["published"])] + ([p["requirements"]] if p.get("requirements") else []))
        summary = CONFIG["summaries"].get(release["tag"]) or first_bullet(release["notes"])
    else:
        head = f'<div class="rel-version quiet">{esc(p["headline"])}</div>' if p.get("headline") else ""
        meta = p.get("requirements", "")
        summary = p.get("without_release") or p.get("summary", "")
    actions = []
    if release and p.get("download"):
        f = asset(release, p["download"]["match"])
        actions.append(f'<span class="btn-glow"><a class="btn btn-sm" href="{esc(f["url"])}">{esc(p["download"]["label"])}</a></span>')
    if p.get("store"):
        if actions:
            actions.append(f'<a class="link-hud" href="{esc(p["store"]["href"])}">{esc(p["store"]["label"])}</a>')
        else:
            actions.append(f'<span class="btn-glow"><a class="btn btn-sm" href="{esc(p["store"]["href"])}">{esc(p["store"]["label"])}</a></span>')
    if release:
        actions.append(f'<a class="link-hud" href="#{p["id"]}-files">Files and SHA-256</a>')
    status_class = "rel-status dim" if soon else "rel-status"
    return f"""
      <article class="card rel-card reveal{' soon' if soon else ''}" id="{p['id']}" aria-labelledby="{p['id']}-name"><div class="card-in">
        <div class="rel-head">{icons[p['icon']]}<h3 id="{p['id']}-name">{esc(p['name'])}</h3><span class="{status_class}">{esc(p['status'])}</span></div>
        {head}
        <div class="rel-meta">{esc(meta)}</div>
        <p class="rel-summary">{esc(summary)}</p>
        {'<div class="rel-actions">' + ''.join(actions) + '</div>' if actions else ''}
      </div></article>"""


def file_row(f: dict) -> str:
    if f["build"]:
        badge = f'<a class="badge ok" href="{esc(f["build"]["run"])}" title="The GitHub Actions run that built it">Attested</a>'
    elif f["signed_from"]:
        badge = '<a class="badge" href="#check-apk">Signed by Veylor</a>'
    elif f["name"] == "SHA256SUMS":
        badge = ""
    else:
        badge = '<span class="badge">No build record</span>'
    return f"""
          <li class="file plate">
            <div class="file-top"><a class="file-name" href="{esc(f['url'])}">{esc(f['name'])}</a><span class="file-size">{size(f['size'])}</span>{badge}</div>
            <p class="file-label">{esc(f['label'])}</p>
            <div class="hash"><span class="hash-k">SHA-256</span><code class="hash-v">{f['sha256']}</code><button class="copy" type="button" data-copy="{f['sha256']}" aria-label="Copy the SHA-256 of {esc(f['name'])}" hidden>Copy</button></div>
          </li>"""


def files_block(p: dict, release: dict) -> str:
    commit = release["commit"]
    rows = "".join(file_row(f) for f in release["files"])
    return f"""
    <div class="rel-files reveal" id="{p['id']}-files">
      <div class="rel-files-head">
        <h3 class="sub"><span class="sub-n">{esc(p['name'])}</span> v{esc(release['version'])}</h3>
        <p class="rel-files-meta">{day(release['published'])} · built from <a href="{GITHUB}/commit/{commit}"><code>{commit[:9]}</code></a> · <a href="{esc(release['url'])}">Release on GitHub</a></p>
      </div>
      <ul class="files">{rows}
      </ul>
    </div>"""


def cmd(command: str, label: str = "") -> str:
    os_label = f'<span class="cmd-os">{esc(label)}</span>' if label else ""
    return (f'<div class="cmd plate">{os_label}<code>{esc(command)}</code>'
            f'<button class="copy" type="button" data-copy="{esc(command)}" aria-label="Copy the command" hidden>Copy</button></div>')


def attest_cmd(file_name: str, platform: str, commit: bool = False) -> str:
    command = (f"gh attestation verify {file_name} --repo {REPO} "
               f"--signer-workflow {REPO}/{CONFIG['workflows'][platform]}")
    if commit:
        command += " --format json --jq '.[].verificationResult.signature.certificate.sourceRepositoryDigest'"
    return command


def verify_section(latest: dict) -> str:
    linux = latest.get("linux")
    android = latest.get("android")
    sample = asset(linux, r"_amd64\.deb$")["name"] if linux else "Veylor-linux-x86_64.AppImage"
    # A Mac or a Windows computer checks the APK it's about to put on a phone.
    other = asset(android, r"^veylor-[0-9.]+-[0-9]+\.apk$")["name"] if android else sample
    hashes = (cmd("sha256sum " + sample, "Linux") + cmd("shasum -a 256 " + other, "Mac")
              + cmd("Get-FileHash .\\" + other, "Windows"))
    steps = [f"""
      <div class="vstep reveal" id="check-hash">
        <h3 class="sub"><span class="sub-n">01</span> Is it the file we published?</h3>
        <div class="prose"><p>Work out the file's SHA-256 and compare all 64 characters with the one on this page. If any differ, delete the file. A match shows the file is the one published here; the next check shows where it came from.</p></div>
        {hashes}
      </div>""", f"""
      <div class="vstep reveal" id="check-build">
        <h3 class="sub"><span class="sub-n">02</span> Was it built from the public code?</h3>
        <div class="prose"><p>GitHub Actions builds each file from a public commit of Veylor's code and signs a record of that build: the file's SHA-256, the repository, the workflow and the commit. With <a href="https://cli.github.com/">GitHub's CLI</a>, signed in to any GitHub account, check the record:</p></div>
        {cmd(attest_cmd(sample, "linux"))}
        <div class="prose after"><p>It fails unless GitHub signed a record of this exact file from Veylor's repository and its release workflow. To see the commit the file was built from, ask for the record's commit: it's the one the release is tagged at, listed with the files above.</p></div>
        {cmd(attest_cmd(sample, "linux", commit=True))}
        <div class="prose after"><p>This trusts GitHub's build machines, not us. Linux 0.9.0 came before these records and has none.</p></div>
      </div>"""]
    if android:
        fingerprint = CONFIG.get("android_certificate_sha256") or fail("an Android release is out, but tools/releases.json has no android_certificate_sha256")
        apk = asset(android, r"^veylor-[0-9.]+-[0-9]+\.apk$")["name"]
        unsigned = asset(android, r"-unsigned\.apk$")["name"]
        steps += [f"""
      <div class="vstep reveal" id="check-apk">
        <h3 class="sub"><span class="sub-n">03</span> Is the APK signed by Veylor?</h3>
        <div class="prose"><p>Android installs an update only when it carries the same signing certificate as the installed app. Before you install the APK, check its certificate with <code>apksigner</code>, from Android's build tools, or an app such as AppVerifier:</p></div>
        {cmd(f"apksigner verify --print-certs {apk}")}
        <div class="hash wide"><span class="hash-k">Certificate SHA-256</span><code class="hash-v">{esc(fingerprint)}</code><button class="copy" type="button" data-copy="{esc(fingerprint)}" aria-label="Copy the certificate's SHA-256" hidden>Copy</button></div>
        <div class="prose after"><p>Veylor from Google Play is signed by Google with Play's key instead, so the two never update each other. To switch, write down your recovery phrase, uninstall Veylor, install the other one and restore.</p></div>
      </div>""", f"""
      <div class="vstep reveal" id="check-apk-build">
        <h3 class="sub"><span class="sub-n">04</span> Is the APK the build GitHub made?</h3>
        <div class="prose"><p>The APK is GitHub's attested build with our signature added, on a computer that holds the key and never gives it to GitHub. Check the unsigned build as in step 2, then that the signature is the only difference, with <a href="https://github.com/obfusk/apksigcopier">apksigcopier</a>:</p></div>
        {cmd(attest_cmd(unsigned, "android", commit=True))}
        {cmd(f"apksigcopier compare {apk} --unsigned {unsigned}")}
        <div class="prose after"><p>It prints nothing when they match.</p></div>
      </div>"""]
    return f"""
  <section class="section rel" id="verify" aria-labelledby="verify-title">
    <p class="hud sec">Check</p>
    <h2 class="title" id="verify-title">Check your download.</h2>
    <div class="vsteps">{''.join(steps)}
    </div>
    <ul class="limits">
      <li class="limit plate reveal"><span class="hud">iPhone</span><p>Apple encrypts and re-signs every TestFlight and App Store app, so nobody can compare the app on a phone with its source.</p></li>
      <li class="limit plate reveal"><span class="hud">Mac, coming soon</span><p>Signed by Zapp LLC and notarized by Apple. macOS checks both before it opens the app: keep Gatekeeper on.</p></li>
    </ul>
  </section>"""


def version_item(release: dict, first: bool) -> str:
    builds = [f["build"] for f in release["files"] if f["name"] != "SHA256SUMS" and not f["signed_from"]]
    if builds and all(builds):
        badge = '<span class="badge ok">Attested</span>'
    elif any(builds):
        badge = '<span class="badge">Partly attested</span>'
    else:
        badge = '<span class="badge">No build record</span>'
    commit = release["commit"]
    anchor = f"v-{release['platform']}-{release['version']}"
    return f"""
      <div class="ver plate reveal"><details id="{anchor}"{' open' if first else ''}>
        <summary><span class="ver-plat">{PLATFORM_NAMES[release['platform']]}</span><span class="ver-num">v{esc(release['version'])}</span><span class="ver-date">{day(release['published'])}</span>{badge}</summary>
        <div class="ver-body">
          <p class="ver-links"><a href="{esc(release['url'])}">Release on GitHub</a> · tag <code>{esc(release['tag'])}</code> at <a href="{GITHUB}/commit/{commit}"><code>{commit[:9]}</code></a></p>
          <div class="notes">
{notes_html(release['notes'])}
          </div>
        </div>
      </details></div>"""


def page(releases: list[dict]) -> str:
    top, defs, footer, icons = site_chrome()
    latest = {}
    for r in releases:
        if not r["prerelease"]:
            latest.setdefault(r["platform"], r)
    cards = {"main": [], "more": []}
    files = []
    for p in CONFIG["platforms"]:
        release = latest.get(p.get("release"))
        cards[p["group"]].append(card(p, release, icons))
        if release:
            files.append(files_block(p, release))
    versions = "".join(version_item(r, i == 0) for i, r in enumerate(releases))
    built = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    return f"""<!doctype html>
<!-- Generated by tools/build-releases.py from GitHub's releases ({built}). Edit tools/releases.json and run it again rather than editing this file. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Releases · Veylor</title>
<meta name="description" content="Every Veylor download, with its SHA-256, the signed record of the build that made it from Veylor's public code, and how to check both.">
<meta name="theme-color" content="#000000">
<meta property="og:title" content="Veylor releases">
<meta property="og:description" content="Every Veylor download, with its SHA-256 and the signed record of where it was built.">
<meta property="og:image" content="https://veylor.cash/icon.png">
<meta property="og:url" content="https://veylor.cash/releases/">
<link rel="icon" href="/icon.png">
<link rel="apple-touch-icon" href="/icon.png">
<link rel="preload" href="/fonts/montserrat-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/site.css">
<script>document.documentElement.classList.add('js')</script>
<script src="/site.js" defer></script>
</head>
<body>
{top}

<main>
  {defs}

  <section class="section first rel" id="latest" aria-labelledby="latest-title">
    <p class="hud sec">Releases</p>
    <h1 class="title" id="latest-title">Every download, and how to check it.</h1>
    <p class="lead reveal">Veylor is open source. Each file here lists its SHA-256 and, from Linux 0.9.1 on, a signed record of the build that made it from Veylor's public code.</p>
    <div class="cta left reveal"><span class="btn-glow"><a class="btn" href="#verify">Check a download</a></span><a class="link-hud" href="{GITHUB}">Source code</a></div>
    <div class="cards rel-grid main">{''.join(cards['main'])}
    </div>
    <div class="cards rel-grid more">{''.join(cards['more'])}
    </div>
  </section>

  <section class="section rel" id="files" aria-labelledby="files-title">
    <p class="hud sec">Files</p>
    <h2 class="title" id="files-title">Every file, with its fingerprint.</h2>
    <div class="prose reveal"><p>A file marked attested has a signed record of the GitHub build that made it. Its badge opens that build's run.</p></div>{''.join(files)}
  </section>
{verify_section(latest)}

  <section class="section rel" id="versions" aria-labelledby="versions-title">
    <p class="hud sec">Versions</p>
    <h2 class="title" id="versions-title">Every release, with its notes.</h2>
    <div class="versions">{versions}
    </div>
  </section>

  <section class="section rel" id="source" aria-labelledby="source-title">
    <p class="hud sec">Source</p>
    <h2 class="title" id="source-title">Read the code.</h2>
    <div class="prose reveal"><p>Veylor is a fork of Vizor, open source under the Apache License 2.0. Shielded USD's Railgun page is GPL-3.0 and ships with its notices.</p></div>
    <ul class="links">
      <li class="reveal"><a class="link-card plate" href="{GITHUB}">
        <span class="hud">Wallet</span>
        <span class="link-name">Veylor</span>
        <span class="link-desc">The app for every platform, and the release notes.</span>
        <span class="link-url">github.com/{REPO}</span>
      </a></li>
      <li class="reveal"><a class="link-card plate" href="{GITHUB}/tree/main/.github/workflows">
        <span class="hud">Builds</span>
        <span class="link-name">Workflows</span>
        <span class="link-desc">The GitHub Actions workflows that build, attest and publish each release.</span>
        <span class="link-url">github.com/{REPO}/…/workflows</span>
      </a></li>
      <li class="reveal"><a class="link-card plate" href="https://github.com/ChinmayGopal931/zecSwap">
        <span class="hud">Bridge protocol</span>
        <span class="link-name">zecSwap</span>
        <span class="link-desc">The swap contract and the client the app runs.</span>
        <span class="link-url">github.com/ChinmayGopal931/zecSwap</span>
      </a></li>
    </ul>
  </section>
</main>

{footer}
<script>
(() => {{
  for (const button of document.querySelectorAll('button.copy')) {{
    button.hidden = false;
    button.setAttribute('aria-live', 'polite');
    button.addEventListener('click', async () => {{
      try {{ await navigator.clipboard.writeText(button.dataset.copy); button.textContent = 'Copied'; }}
      catch {{ button.textContent = 'Select it'; }}
      clearTimeout(button.reset);
      button.reset = setTimeout(() => {{ button.textContent = 'Copy'; }}, 1600);
    }});
  }}
  const openTarget = () => {{
    const target = location.hash && document.getElementById(location.hash.slice(1));
    if (target && target.tagName === 'DETAILS') target.open = true;
  }};
  addEventListener('hashchange', openTarget);
  openTarget();
}})();
</script>
</body>
</html>
"""


def main():
    releases = load_releases()
    if not releases:
        fail("GitHub lists no veylor-<platform>/v<version> release")
    html_text = page(releases)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html_text)
    for r in releases:
        attested = sum(1 for f in r["files"] if f["build"])
        print(f"{r['tag']}: {len(r['files'])} files, {attested} attested, tag at {r['commit'][:9]}")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
