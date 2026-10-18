# veylor-landing

The static site for [veylor.cash](https://veylor.cash): the home page and the
privacy policy that Veylor's TestFlight and App Store listings link to. Plain
HTML, no build step.

| File | URL |
| --- | --- |
| `index.html` | https://veylor.cash (support: https://veylor.cash/#support) |
| `privacy/index.html` | https://veylor.cash/privacy/ |
| `icon.png` | favicon, from the app icon |
| `CNAME` | tells GitHub Pages to serve the site on veylor.cash |

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
