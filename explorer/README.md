# Morocco Legislation Explorer

This deployment runs the OpenFisca Morocco Web API and the OpenFisca
Legislation Explorer as two Docker Compose services. The Explorer server loads
entities, parameters, variables and the API specification at startup, then
serves server-rendered pages. The browser also calls the API directly.

## Split-horizon API URLs

`EXPLORER_API_URL` is baked into the client bundle at image build time. Browsers
must be able to reach it; locally it defaults to `http://localhost:5000`, and
public hosting should set it to the public API URL. `SERVER_API_URL` is read by
the Explorer's Node server at runtime for its startup fetches and should use
the Compose service address, normally `http://api:5000`. These URLs serve
different network contexts and must both be set correctly.

## Self-host

Copy `.env.example` to `.env` and adjust the values if needed, then run from the
repository root:

```sh
docker compose -f explorer/docker-compose.yml up --build -d
```

Open <http://localhost:2020> for the Explorer and
<http://localhost:5000/spec> for the API specification. To stop the services:

```sh
docker compose -f explorer/docker-compose.yml down
```

The API container installs the package from this checkout. The Explorer image
clones upstream commit `8a93870bd055e3bec2a7dbbe826730b43ec96a4a`, applies
[`patches/legislation-explorer.patch`](patches/legislation-explorer.patch),
and builds with Node 14.

## Public hosting

Use a VPS with Docker Compose and Caddy, or a platform such as Fly or Render
that can run the same two services. Set `EXPLORER_API_URL` to the public API
origin (for example `https://api.example.com`) and keep `SERVER_API_URL` set to
the internal service address (for example `http://api:5000`). Build the
Explorer after changing its build argument. For a VPS, adapt
[`Caddyfile.example`](Caddyfile.example) and direct the two hostnames to ports
2020 and 5000; Caddy can provision TLS once DNS points to that VPS.

The parameter corpus is not copied into this deployment: the API serves the
package's parameter tree. Link curation must prefer the annual SGG gazette,
keep printed Bulletin Officiel pages in titles where known, use a PDF
`#page=N` fragment only for a real PDF page index, use the maintained
[`official-source-allowlist.txt`](official-source-allowlist.txt), and validate
every URL returns HTTP 200 before publication. The full policy is in
[`docs/explorer-links.md`](../docs/explorer-links.md).

Verification checklist:

- The homepage lists parameter and variable trees, and browser requests to the
  public API succeed without CORS errors.
- Parameter pages show descriptions, dated values or bracket tables, and a
  historical timeline.
- Parameters with metadata references show the “Références législatives”
  heading and working SGG links.
- Check both scalar and scale parameters, including
  `impot_revenu.bareme`.

### Tailscale Funnel demo

If the host is already on Tailscale, Funnel can publish a temporary HTTPS demo
without a separate domain:

```sh
export EXPLORER_API_URL=https://<host>.<tailnet>.ts.net:10000
docker compose -f explorer/docker-compose.yml build explorer
docker compose -f explorer/docker-compose.yml up -d
tailscale funnel --bg --https 8443 2020
tailscale funnel --bg --https 10000 5000
```

The Explorer is then at `https://<host>.<tailnet>.ts.net:8443` and the API at
`https://<host>.<tailnet>.ts.net:10000/spec`. TLS is provided by Tailscale.
Stop the public demo with:

```sh
tailscale funnel --https=8443 off
tailscale funnel --https=10000 off
docker compose -f explorer/docker-compose.yml down
```

This is a demo on the operator's machine, not a durable production host.
Public DNS records, TLS hostnames and host credentials are still required for
a permanent deployment; this repository does not create or configure those
external resources.
