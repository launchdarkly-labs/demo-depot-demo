// Browser side of the Demo Depot starter.
//
// 1. Fetch runtime config from the server (client-side ID, project, environment, customer name).
// 2. Initialize the LaunchDarkly browser SDK with a stable user context.
// 3. Evaluate the flag once, then subscribe to changes so the page updates without a reload.

(async function main() {
  const $ = (id) => document.getElementById(id);

  function log(text) {
    const li = document.createElement("li");
    const time = new Date().toLocaleTimeString([], { hour12: false });
    li.innerHTML = `<time>${time}</time> ${text}`;
    $("log").prepend(li);
  }

  function setStatus(kind, text) {
    const el = $("status");
    el.className = `pill pill-${kind}`;
    el.textContent = text;
  }

  // Re-render everything the flag controls. Called on first evaluation and on every change.
  function render(value, why) {
    $("promo").hidden = !value;
    const pill = $("flag-value");
    pill.className = `pill ${value ? "pill-on" : "pill-off"}`;
    pill.textContent = value ? "true (banner on)" : "false (banner off)";
    log(`Banner is <b>${value ? "on" : "off"}</b> (${why})`);
  }

  // A stable key per browser keeps percentage rollouts sticky and shows up nicely in Contexts.
  function userContext() {
    let key = localStorage.getItem("dd-user-key");
    if (!key) {
      key = `user-${crypto.randomUUID().slice(0, 8)}`;
      localStorage.setItem("dd-user-key", key);
    }
    return { kind: "user", key, name: "Demo visitor" };
  }

  const cfg = await fetch("/api/config", { cache: "no-store" }).then((r) => r.json());
  document.title = `${cfg.customerName} · Demo Depot Starter`;
  $("customer").textContent = cfg.customerName;
  $("flag-key").textContent = cfg.flagKey;
  $("flag-key-inline").textContent = cfg.flagKey;
  $("project").textContent = cfg.projectKey ?? "—";
  $("env").textContent = cfg.envKey ?? "—";
  $("meta").textContent = [cfg.demoVersion, cfg.instanceId].filter(Boolean).join(" · ");

  if (cfg.projectKey && cfg.envKey) {
    const link = $("ld-link");
    link.href = `https://app.launchdarkly.com/projects/${cfg.projectKey}/flags/${cfg.flagKey}/targeting?env=${cfg.envKey}&selected-env=${cfg.envKey}`;
    link.hidden = false;
  }

  // Fallback path: the depot's verifier and plain `npm start` run without LaunchDarkly keys.
  if (!cfg.clientSideId) {
    setStatus("warn", "LaunchDarkly not configured");
    log("LD_CLIENT_SIDE_ID is not set, so the flag stays at its fallback value.");
    render(false, "fallback");
    return;
  }

  const context = userContext();
  $("context-key").textContent = context.key;
  setStatus("muted", "connecting…");

  const client = LDClient.initialize(cfg.clientSideId, context, { streaming: true });

  client.on("failed", (err) => {
    setStatus("error", "connection failed");
    log(`LaunchDarkly initialization failed: ${err?.message ?? err}`);
    render(false, "fallback");
  });

  try {
    await client.waitForInitialization(10);
  } catch {
    return; // the "failed" handler above already rendered the fallback
  }

  setStatus("on", "streaming live");
  log(`Connected as <code>${context.key}</code>`);
  render(client.variation("promo-banner", false), "initial evaluation");

  // The listener. LaunchDarkly streams the new value the moment the flag is saved;
  // there is no polling and no page reload.
  client.on("change:promo-banner", (current, previous) => {
    log(`<code>promo-banner</code> changed: ${previous} → ${current}`);
    render(current, "live change");
  });
})();
