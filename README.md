# veylor-landing

The static site for [veylor.cash](https://veylor.cash): the home page and the
privacy policy that Veylor's TestFlight and App Store listings link to. Plain
HTML, no build step.

| File | What it is |
| --- | --- |
| `index.html` | https://veylor.cash: the home page. It leads with the shielded bridge (shielded ZEC to 0zkUSDC and back), then the problem with NEAR Intents routes, why the swap needs no trust, holding dollars, a short how-it-works teaser, Railgun, the rest of the app, the source links, the beta and support (https://veylor.cash/#support) |
| `how-it-works/index.html` | https://veylor.cash/how-it-works/: the bridge in full (the split key, the swap's steps, the two endings, deadlines and locks, what if, the dollars-to-ZEC direction) and the comparison with NEAR Intents (`#compare`) |
| `privacy/index.html` | https://veylor.cash/privacy/ |
| `site.css`, `site.js` | shared look and motion: the tube wordmark, the sun and grid, the scroll's sync line, the diagrams that draw in on scroll, and the click sound |
| `logos/railgun.svg` | Railgun's mark, for the "Powered by Railgun" section (see below) |
| `fonts/` | Montserrat (SIL Open Font License, `fonts/OFL.txt`), self-hosted so the site makes no third-party requests |
| `icon.png` | favicon, from the app icon |
| `CNAME` | tells GitHub Pages to serve the site on veylor.cash |

Every push to `main` redeploys the site. The VEYLOR wordmark is the app's
`VeylorWordmarkPainter` geometry drawn as SVG. Gotham isn't used here: the
app's license doesn't cover websites. All motion stops for visitors who ask
for reduced motion: the stylesheet draws the still page first and keeps every
animation inside one `prefers-reduced-motion: no-preference` block.

The beta buttons ("Join the beta on TestFlight", two in `index.html` and one
in `how-it-works/index.html`) point at the public TestFlight link,
https://testflight.apple.com/join/D9gw2Kwm. Change all three together.

## The click sound

Buttons and links make a short square-wave blip, synthesized with the Web
Audio API in `site.js`; there are no audio files. The audio context is made on
the visitor's first press, never before. The SOUND switch in the top corner
turns it off and on (on by default) and remembers the choice in
`localStorage` under `veylor.sound`; if storage is blocked the page still
works and the sound stays on.

## The Railgun mark

`logos/railgun.svg` is the file railgun.org serves at
https://railgun.org/favicon-dark.svg, downloaded on 2026-10-18 and kept byte
for byte (SHA-256
`41da269bcffb887d9ce74c81a6f478618e1dda3cb69fa2e06303265fd2614e0f`). Railgun
publishes no brand kit or logo terms on railgun.org, railgun.ch,
docs.railgun.org or its GitHub organizations, and railgun.org describes
itself as an independent info site. The mark links to railgun.org. Don't
recolor or redraw it.

## Keeping the copy true

The bridge copy comes from the bridge's own documentation
(https://github.com/JustZappIt/zecSwap) and Railgun's descriptions of itself.
Never claim an audit, a speed or a fee. When the bridge changes (an audit is
published, the per-swap caps or units change, it leaves beta), update the
"How it works" page, its comparison and the beta sections to match.

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
