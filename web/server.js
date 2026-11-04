// Demo Depot starter: the smallest server that follows the depot's runtime contract.
//
// - Every LaunchDarkly key and setting is read from env vars at request time, never at build time.
// - The browser gets its config from /api/config, so one image works for every launch.
// - /healthz is cheap and has no external dependencies. The depot polls it.
// - The server listens on 0.0.0.0 and trusts X-Forwarded-Proto (TLS ends at the load balancer).

import path from "node:path";
import { fileURLToPath } from "node:url";
import express from "express";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT ?? 3000);
const FLAG_KEY = "promo-banner"; // must match ld/seed.json

const app = express();
app.set("trust proxy", true);
app.disable("x-powered-by");

// Health check: 200 as soon as the server is up. No LaunchDarkly, no network.
app.get("/healthz", (_req, res) => res.type("text").send("ok"));

// Runtime config for the browser. The depot injects LD_* and DD_* per launch.
app.get("/api/config", (_req, res) => {
  res.set("Cache-Control", "no-store");
  res.json({
    clientSideId: process.env.LD_CLIENT_SIDE_ID ?? null,
    projectKey: process.env.LD_PROJECT_KEY ?? null,
    envKey: process.env.LD_ENV_KEY ?? null,
    flagKey: FLAG_KEY,
    customerName: process.env.CUSTOMER_NAME || "Acme Corp",
    instanceId: process.env.DD_INSTANCE_ID ?? null,
    demoVersion: process.env.DD_DEMO_VERSION ?? "local",
  });
});

// The LaunchDarkly browser SDK is served from node_modules, so the page has no CDN dependency.
app.use(
  "/vendor",
  express.static(path.join(__dirname, "node_modules/launchdarkly-js-client-sdk/dist"), {
    maxAge: "1d",
  }),
);
app.use(express.static(path.join(__dirname, "public")));

app.listen(PORT, "0.0.0.0", () => {
  console.log(
    JSON.stringify({
      msg: "listening",
      port: PORT,
      flag: FLAG_KEY,
      launchdarklyConfigured: Boolean(process.env.LD_CLIENT_SIDE_ID),
      instance: process.env.DD_INSTANCE_ID ?? null,
    }),
  );
});
