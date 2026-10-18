/* Validation client complete : SSO -> creation reunion -> lien -> navigation vierge -> appel */
const { chromium } = require("playwright-core");

const DEMO_PWD = process.env.DEMO_PWD;
const logs = [];
function watch(page, tag) {
  page.on("pageerror", (e) => logs.push(`[${tag}][PAGEERROR] ${String(e).slice(0, 200)}`));
  page.on("response", (r) => { if (r.status() >= 400) logs.push(`[${tag}][HTTP ${r.status()}] ${r.request().method()} ${r.url().slice(0, 110)}`); });
}

(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true, args: ["--ignore-certificate-errors"] });

  // ---------- 1) CREATEUR : SSO + creation de reunion ----------
  const ctx1 = await browser.newContext({ ignoreHTTPSErrors: true });
  const p1 = await ctx1.newPage();
  watch(p1, "createur");
  console.log("1. Ouverture meet.localhost (doit rediriger vers le SSO)...");
  await p1.goto("https://meet.localhost:8443/", { waitUntil: "domcontentloaded", timeout: 30000 });
  await p1.waitForTimeout(4000);

  // Page de login Keycloak ?
  const hasUser = await p1.locator("#username").count();
  if (hasUser) {
    console.log("   Page SSO LaStarter atteinte -> login demo");
    await p1.fill("#username", "demo");
    await p1.fill("#password", DEMO_PWD);
    await p1.locator("button[type=submit]").click();
    await p1.waitForTimeout(6000);
    // Page de confirmation Synapse (secours si pas de whitelist) : cliquer Continue
    for (let i = 0; i < 2; i++) {
      const cont = p1.locator("button:has-text('Continue'), a:has-text('Continue')");
      if (await cont.count()) {
        console.log("   Page Continue Synapse -> clic");
        await cont.first().click();
        await p1.waitForTimeout(6000);
      } else break;
    }
    await p1.waitForTimeout(8000);
  }
  const homeText = await p1.evaluate(() => document.body.innerText.slice(0, 200));
  console.log(`   SPA apres SSO : ${homeText.replace(/\n/g, " | ").slice(0, 120)}`);

  // 2) Creation d'une reunion
  const nameField = p1.getByTestId("roomname");
  if (await nameField.count()) {
    console.log("2. Creation d'une reunion 'reunion-client'...");
    await nameField.fill("reunion-client");
    await p1.keyboard.press("Enter");
    await p1.waitForTimeout(15000);
  } else {
    const input = p1.getByPlaceholder(/name of call|nom/i).first();
    if (await input.count()) {
      console.log("2. Creation d'une reunion (placeholder) 'reunion-client'...");
      await input.fill("reunion-client");
      const go = p1.locator("button:has-text('Go')").first();
      if (await go.count()) await go.click();
      else await p1.keyboard.press("Enter");
      await p1.waitForTimeout(15000);
    }
  }
  const roomUrl = p1.url();
  console.log(`   URL de la room : ${roomUrl.slice(0, 110)}`);
  const inCall = await p1.evaluate(() => document.body.innerText.slice(0, 150));
  console.log(`   Etat : ${inCall.replace(/\n/g, " | ").slice(0, 110)}`);

  // ---------- 3) INVITE : navigation vierge, pseudo, appel ----------
  if (roomUrl.includes("roomId=")) {
    console.log("3. Ouverture du lien dans un contexte VIERGE (comme navigation privee)...");
    const ctx2 = await browser.newContext({ ignoreHTTPSErrors: true });
    const p2 = await ctx2.newPage();
    watch(p2, "invite");
    await p2.goto(roomUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await p2.waitForTimeout(4000);
    const guestField = p2.getByTestId("joincall_displayName");
    if (await guestField.count()) {
      await guestField.fill("ClientInvite");
      await p2.getByTestId("joincall_joincall").click();
      await p2.waitForTimeout(20000);
      const callText = await p2.evaluate(() => document.body.innerText.slice(0, 300));
      console.log(`   Invitation apres pseudo : ${callText.replace(/\n/g, " | ").slice(0, 160)}`);
      await p2.screenshot({ path: "e2e-invite.png" });
    } else {
      console.log("   Pas de formulaire pseudo !");
    }
    await ctx2.close();
  } else {
    console.log("3. PAS de roomId dans l'URL - creation de reunion en echec");
  }

  console.log("\n--- ERREURS CAPTUREES ---");
  const real = logs.filter((l) => !/room_keys\/version|\.well-known\/matrix|getRTCTransports|delegate_delayed/.test(l));
  for (const l of real.slice(-12)) console.log(l);

  await browser.close();
})().catch((e) => { console.error("ERREUR SCRIPT:", e); process.exit(1); });
