# veylor-landing

The static site for [veylor.cash](https://veylor.cash): the home page and the
privacy policy that Veylor's TestFlight and App Store listings link to. Plain
HTML, no build step.

| File | What it is |
| --- | --- |
| `index.html` | https://veylor.cash: the animated home page (support: https://veylor.cash/#support) |
| `privacy/index.html` | https://veylor.cash/privacy/ |
| `site.css`, `site.js` | shared look and motion: the tube wordmark, the sun and grid, the scroll's sync line |
| `fonts/` | Montserrat (SIL Open Font License, `fonts/OFL.txt`), self-hosted so the site makes no third-party requests |
| `icon.png` | favicon, from the app icon |
| `CNAME` | tells GitHub Pages to serve the site on veylor.cash |

Every push to `main` redeploys the site. The VEYLOR wordmark is the app's
`VeylorWordmarkPainter` geometry drawn as SVG. Gotham isn't used here: the
app's license doesn't cover websites. All motion stops for visitors who ask
for reduced motion.

When the public TestFlight link exists, point the two "Request beta access"
buttons in `index.html` at it instead of the email.

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
