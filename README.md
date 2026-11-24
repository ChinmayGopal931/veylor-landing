# veylor-landing

The static site for [veylor.cash](https://veylor.cash): the home page and the
privacy policy that Veylor's TestFlight and App Store listings link to. Plain
HTML, no build step.

| File | What it is |
| --- | --- |
| `index.html` | https://veylor.cash: the home page. The hero leads with the wallet and the bridge built into it; then what the wallet holds, getting paid in 0zkUSDC (a Receive card that switches between USDC and 0zkUSDC), the rest of the app, its languages (pills that switch a line of the app's words), why the bridge needs no trust, private DeFi (coming soon, greyed out), Railgun, open source and attestable (a terminal that types a real `gh attestation verify`), the FAQ (`#faq`), and getting the app (`#beta`). https://veylor.cash/#support, the support URL the App Store listing and the footers use, lands on the FAQ's contact line |
| `how-it-works/index.html` | https://veylor.cash/how-it-works/: the bridge in one animated figure (the stage: four steps when a swap settles, and the same swap stalling), the comparison with NEAR Intents (`#compare`), and what happens if something goes wrong. The protocol's own detail stays in the bridge's README, linked from the page |
| `privacy/index.html` | https://veylor.cash/privacy/ |
| `support-veylor/index.html` | https://veylor.cash/support-veylor/: the ZEC donation address and its QR code (see below), linked from every footer |
| `releases/index.html` | https://veylor.cash/releases/: every release, each file with its size, SHA-256 and build attestation, how to check a download, and each release's notes. Written by `tools/build-releases.py`, never by hand (below) |
| `tools/` | `build-releases.py`, which writes the releases page, and `releases.json`, the words it can't take from GitHub |
| `site.css`, `site.js` | shared look and motion: the tube wordmark, the sun and grid, the packets that shoot along the grid into the distance (the home page's hero, CSS alone), the top bar (frosted once the page scrolls), the film over the page (grain, scanlines, vignette), the cards that tilt toward the pointer, the scroll's sync line, the diagrams that draw in on scroll, the how-it-works stage, the footer's sign, and the press sounds |
| `art/helmet.webp` | the helmet in the footer, cut out of the app icon (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png` in the app's repository) with its visor's light taken out: the footer draws that itself |
| `logos/railgun.svg` | Railgun's mark, for the "Powered by Railgun" section (see below) |
| `fonts/` | Gotham Thin and Light, subset from the app's files (see below), and Montserrat (SIL Open Font License, `fonts/OFL.txt`) behind them; self-hosted so the site makes no third-party requests |
| `icon.png` | favicon, from the app icon |
| `CNAME` | tells GitHub Pages to serve the site on veylor.cash |

Every push to `main` redeploys the site. The VEYLOR wordmark is the app's
`VeylorWordmarkPainter` geometry drawn as SVG. All motion stops for visitors who ask
for reduced motion: the stylesheet draws the still page first and keeps every
animation inside one `prefers-reduced-motion: no-preference` block.

The download links (the hero's platform marks and the `#beta` tiles in
`index.html`; the other pages' buttons go to `/#beta`) point at the iPhone
beta's public TestFlight link
(https://testflight.apple.com/join/D9gw2Kwm) and the Android app's Play listing
(https://play.google.com/store/apps/details?id=com.veylor.app), in production.
When the iPhone app leaves TestFlight, point its buttons at its App Store
listing and drop "beta" from the copy beside them. The bridge itself stays in
beta until it leaves it (below).

## Gotham

Gotham is a commercial typeface (Hoefler & Co., now Monotype). The app's license
doesn't cover websites, so publishing `fonts/gotham-*.woff2` needs a web
license. Without one, delete the two files and their two `@font-face` rules in
`site.css`: everything falls back to Montserrat.

## The footer's sign

Every page ends in the same full-width footer: the app icon's helmet between
the letters of the wordmark. The stylesheet draws it lit. `site.js` then takes
the light over (`.sign.dark`): when the footer arrives the visor opens, the
letters strike outward from it, hold, and cut out, and it starts again. A press
switches it off and on, and the visor follows the pointer. Under reduced motion,
or without JavaScript, it simply stays lit.

## Names

The site says 0zkUSDC (the shielded token) or USDC, never dollars or the app's
feature name. The releases generator renames it in the notes it takes from
GitHub (`NAMES` in `tools/build-releases.py`).

## The releases page

`releases/index.html` is generated. After a release is published on the app's
repository (a tag `veylor-<platform>/v<version>`: `android`, `linux`, `macos`
or `windows`), write the page again and commit it:

```sh
python3 -I tools/build-releases.py
```

It needs `gh`, signed in. From GitHub's API it takes every such release, its
notes, the commit its tag names, its files' sizes and SHA-256 digests, and
each file's build attestation, and it refuses to write the page when:

- a release's `SHA256SUMS` disagrees with GitHub's digests;
- an attestation names another repository or workflow;
- a file's attestations name no build of its tag's commit;
- a signed APK has no attested unsigned build beside it.

`tools/releases.json` holds the rest: each platform card's words and links,
the file labels, a short summary per release, and the Android APK's signing
certificate (its SHA-256, as `apksigner verify --print-certs` prints it). The
page loads nothing from GitHub; its links go there only when clicked. The top
bar, footer and platform icons come from `how-it-works/index.html` and the
home page's tiles, so change them there and run the script again.

## The press sounds

Buttons and links sound like a light cycle: detuned saws through a resonant
filter, a glassy FM ring over them and a short metallic room behind both,
synthesized with the Web Audio API in `site.js`; there are no audio files. The
audio context is made on the visitor's first press, never before. The SOUND
switch in the footer turns it off and on (on by default) and remembers the
choice in `localStorage` under `veylor.sound`; if storage is blocked the page
still works and the sound stays on.

## The donation address

`support-veylor/` shows the owner's Zcash donation address and
`zcash-donation-qr.png`, both from the app's repository: the address is the
one in its README's "Support Veylor" (and `kVizorDonationAddress` in the app),
and the PNG is its `.github/assets/zcash-donation-qr.png` byte for byte, a QR
code of `zcash:` and that address. When the address changes there, change
both here, and decode the new QR code to check it before you push.

## The Railgun mark

`logos/railgun.svg` is the file railgun.org serves at
https://railgun.org/favicon-dark.svg, downloaded on 2026-10-18 and kept byte
for byte (SHA-256
`41da269bcffb887d9ce74c81a6f478618e1dda3cb69fa2e06303265fd2614e0f`). Railgun
publishes no brand kit or logo terms on railgun.org, railgun.ch,
docs.railgun.org or its GitHub organizations, and railgun.org describes
itself as an independent info site. The mark links to railgun.org. Don't
recolor or redraw it.

## The Morpho and Aave marks

The private DeFi cards draw Morpho's butterfly and Aave's ghost ("Logomark
Light.svg" from Aave's own kit, https://aave.com/aave-brand-assets.zip,
SHA-256 `025ee678cc531c0a818424d33d9a8bf061e22353858a5c34ae6373f5c94f1a28`)
inline, in white and dimmed. Don't recolor or redraw them.

## Keeping the copy true

The bridge copy comes from the bridge's own documentation
(https://github.com/ChinmayGopal931/zecSwap) and Railgun's descriptions of itself.
Never claim an audit, a speed or a fee. The
comparison's NEAR Intents column is from its own pages, read on 2026-11-23, and
links to them: [chain support](https://docs.near-intents.org/resources/chain-support)
("ZEC (Zcash, transparent only)") and the [1Click
terms](https://docs.near-intents.org/security-compliance/terms-of-service)
(§12.4, no obligation to refund; Schedule 1 §1.6, what the verifier contract's
administrative roles may do). Its docs also say 1Click takes no custody and that
the verifier contract is open source, so don't claim otherwise. Read them again
before changing that column. The copy calls the swap's market maker
"the bridge": anyone can run one on the contract, and the app uses one. When
the bridge changes (an audit is published, the per-swap caps or units change,
it leaves beta), update the "How it works" page, its comparison and the beta
sections to match.

## Publish on GitHub Pages

1. Push this folder to a GitHub repository's `main` branch.
2. In the repository: **Settings → Pages → Build and deployment**, choose
   "Deploy from a branch", `main`, `/ (root)`. The `CNAME` file sets the
   custom domain.
3. In Porkbun, open veylor.cash's **DNS** records:
   - delete Porkbun's parking records (the `ALIAS` on `veylor.cash` and the
     `*` wildcard `CNAME`, both pointing at `pixie.porkbun.com`);
   - add four `A` records for `veylor.cash`: `185.199.108.153`,
     `185.199.109.153`, `185.199.110.153`, `185.199.111.153`;
   - add a `CNAME` for `www` pointing at `<github-user>.github.io`;
   - **keep** the `MX` and `TXT` records Porkbun created for email forwarding,
     or `hello@veylor.cash` stops receiving mail.
4. Back in **Settings → Pages**, wait for the certificate, then tick
   **Enforce HTTPS**.

## Keeping the privacy policy true

Section 5 of the policy lists every network service the app contacts. When a
Veylor release starts using a new service, add it there and change the
"Last updated" date.
