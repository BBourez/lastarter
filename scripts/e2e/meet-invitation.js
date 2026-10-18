/* Debug E2E : ouvre le lien d'invitation dans Edge headless et capture TOUT. */
const { chromium } = require("playwright-core");

const URL = "https://meet.localhost:8443/room/#/pour?password=61_r3yQBzFicKUXgL3ZBRA&roomId=%21rkq9Co__CcHnDmklWnBjFTlFSBDy9fsho4mRgZ3gps0";

(async () => {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--ignore-certificate-errors"],
  });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  const logs = [];
  page.on("console", (m) => {
    const t = m.type();
    if (t === "error" || t === "warning") logs.push(`[${t}] ${m.text().slice(0, 300)}`);
  });
  page.on("pageerror", (e) => logs.push(`[PAGEERROR] ${String(e).slice(0, 400)}`));
  page.on("requestfailed", (r) => logs.push(`[NET-FAIL] ${r.method()} ${r.url().slice(0, 120)} : ${r.failure()?.errorText}`));
  page.on("response", (r) => {
    if (r.status() >= 400) logs.push(`[HTTP ${r.status()}] ${r.request().method()} ${r.url().slice(0, 130)}`);
  });

  console.log("1. Ouverture du lien...");
  await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(5000);

  // Capture de l'etat initial
  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 300));
  console.log(`\n--- PAGE (5s apres chargement) ---\n${bodyText}\n`);

  // Si le formulaire pseudo est la, le remplir et soumettre
  const nameField = page.getByTestId("joincall_displayName");
  if (await nameField.count()) {
    console.log("2. Formulaire pseudo trouve -> remplissage et soumission");
    await nameField.fill("DebugBot");
    await page.getByTestId("joincall_joincall").click();
    await page.waitForTimeout(20000);
    const afterText = await page.evaluate(() => document.body.innerText.slice(0, 400));
    console.log(`\n--- PAGE (12s apres soumission) ---\n${afterText}\n`);
  } else {
    console.log("2. Pas de formulaire pseudo visible");
  }

  console.log("--- CONSOLE / RESEAU ---");
  for (const l of logs.slice(-40)) console.log(l);

  await page.screenshot({ path: "e2e-debug.png" });
  await browser.close();
})().catch((e) => { console.error("ERREUR SCRIPT:", e); process.exit(1); });
