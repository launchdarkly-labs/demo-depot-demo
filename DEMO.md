## What this shows

The smallest demo that runs on Demo Depot end to end. A one-page storefront evaluates a single LaunchDarkly flag in the browser and subscribes to changes, so when the SE flips the flag the promo banner appears instantly, with no reload. Use it to show how a depot demo is put together: the manifest, the seed, runtime config, and the publish-by-tag flow.

## LaunchDarkly features

- **Feature flag in the browser**: the JavaScript client SDK evaluates `promo-banner` for a stable user context.
- **Streaming change listener**: `client.on("change:promo-banner", …)` re-renders the banner the moment the flag is saved.
- **Fresh project per launch**: every launch gets its own LaunchDarkly project seeded from `ld/seed.json`, so nothing an SE does leaks into another SE's demo.

## The story (about 5 minutes)

1. **Open the app.** The storefront shows the prospect's name (the `CUSTOMER_NAME` launch parameter) and no banner. The *Flag state* panel on the right shows `promo-banner = false`, the connection as *streaming live*, and the project and environment keys the depot created for this launch. Point out that these keys arrived as env vars at runtime, not at build time.
2. **Toggle `promo-banner` on.** Click *Open flag in LaunchDarkly* in the panel, turn the flag on, save. Within about a second the banner drops in, the value pill turns green, and the event log records the change with a timestamp. Nobody refreshed the page.
3. **Toggle it off, then on again.** The banner leaves and returns each time. Each line in the event log is one streamed change received by the listener.
4. **Show the plumbing (optional).** Open `/api/config` in a new tab to show the client-side ID being served at request time. Open the repo and walk through `demo.yaml`, `ld/seed.json`, and the `change:` listener in `web/public/app.js`.
5. **The aha moment.** The whole demo is six files plus a Dockerfile, and tagging `v0.1.0` is the only publish step. That is the bar for getting a demo into the depot.

## Seeded flags

| Key | Kind | Starts | Why |
| --- | --- | --- | --- |
| `promo-banner` | boolean | off; default rule serves `true` | The code calls `variation("promo-banner", false)` from the browser, so the flag has client-side availability on. The story starts with no banner, and the fallthrough serves `true` so the SE's first toggle is visible without editing rules. |

## Created during the demo

None. Everything the story needs is in `ld/seed.json`.

## Launch parameters

| Parameter | What it does |
| --- | --- |
| `CUSTOMER_NAME` | Shown in the header and the browser tab title. Defaults to Acme Corp. |

## Setup the SE does

None.

## Known limitations

- The flag is evaluated only in the browser. There is no server-side evaluation in this starter.
- The user context key is generated per browser and kept in `localStorage`, so each SE browser is one user in the Contexts list.
- A paused instance comes back with the same LaunchDarkly project and flag state; the event log in the page starts empty because it lives in the browser.
