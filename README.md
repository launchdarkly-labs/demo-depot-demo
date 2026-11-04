# Demo Depot Starter

The smallest LaunchDarkly demo that runs on [Demo Depot](https://demodepot.launchdarklydemos.com): a one-page site, one flag, and a change listener that updates the page live. See [DEMO.md](DEMO.md) for the talk track.

```
demo.yaml                      depot manifest: slug, parameters, container, health check, seed
DEMO.md                        detail page and talk track
ld/seed.json                   the LaunchDarkly project every launch starts from (one flag: promo-banner)
media/cover.png                catalog cover
web/server.js                  Express: /healthz, /api/config, static files
web/public/app.js              browser SDK init, flag evaluation, and the change listener
web/Dockerfile                 arm64-safe, non-root, HEALTHCHECK on /healthz
.github/workflows/publish.yml  tagging vX.Y.Z publishes to the depot
scripts/reset-demo.sh          removes the demo from the depot and the depot files, to run the walkthrough again
docs/setup-slide.html          one-slide setup guide (plugin, CLI, tokens, publish); docs/setup-slide.png is the rendered copy
```

## Run it locally

With the depot CLI (`ddu`), using your own LaunchDarkly project that has a `promo-banner` flag with client-side availability on:

```sh
LD_API_TOKEN=api-… ddu run --ld-project <project-key> --ld-env <env-key>
```

Without the CLI, copy `.env.example` to `.env.local`, fill in `LD_CLIENT_SIDE_ID` (and optionally the project and environment keys for the "Open in LaunchDarkly" link), then:

```sh
cd web && npm install && set -a && . ../.env.local && set +a && npm start
```

Open http://localhost:3000, then toggle `promo-banner` in LaunchDarkly and watch the banner. With no client-side ID set, the page renders in a "not configured" state with the flag at its fallback, which is what the depot's verifier sees.

## Validate and publish

```sh
ddu validate .            # or: python3 <skill>/scripts/validate_demo.py .
git tag v0.1.0 && git push origin v0.1.0
```

The publish workflow builds the image for linux/arm64, uploads the manifest and seed, and the depot verifies the version by launching it once. When it shows as verified, the demo is in the catalog.

## Run the walkthrough again

`scripts/reset-demo.sh` puts the repo back to "just an app": it deletes the demo from Demo Depot (tearing down any running instances), removes the `v*` tags locally and on origin, and deletes `demo.yaml`, `DEMO.md`, `ld/`, `media/`, and the publish workflow. `web/` and this README stay. Use `--dry-run` to see what it would do, `--yes` to skip the prompt. It needs the token from `ddu auth login` (or `DD_TOKEN`).
