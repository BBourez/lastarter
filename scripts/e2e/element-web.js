/* Validation Element Web (chat) : SSO -> connexion -> salon -> message visible */
const { chromium } = require("playwright-core");

const DEMO_PWD = process.env.DEMO_PWD;
const logs = [];
function watch(page, tag) {
  page.on("pageerror", (e) => logs.push(`[${tag}][PAGEERROR] ${String(e).slice(0, 200)}`));
  page.on("response", (r) => { if (r.status() >= 400) logs.push(`[${tag}][HTTP ${r.status()}] ${r.request().method()} ${r.url().slice(0, 110)}`); });
}

async function clickIfVisible(page, selector, timeout = 3000) {
  try {
    await page.locator(selector).first().waitFor({ state: "visible", timeout });
    await page.locator(selector).first().click();
    return true;
  } catch { return false; }
}

(async () => {
  // Canal surchargeable (msedge absent sur certains postes) : E2E_CHANNEL=chrome node element-web.js
  const browser = await chromium.launch({
    channel: process.env.E2E_CHANNEL || "msedge",
    headless: true,
    args: ["--ignore-certificate-errors"],
  });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true, permissions: ["microphone", "camera"] });
  const page = await ctx.newPage();
  watch(page, "web");

  console.log("1. Ouverture chat.localhost (SSO immediat attendu)...");
  await page.goto("https://chat.localhost:8443/", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(5000);

  // SSO : formulaire LaStarter ?
  if (await page.locator("#username").count()) {
    console.log("   Page SSO LaStarter -> login demo");
    await page.fill("#username", "demo");
    await page.fill("#password", DEMO_PWD);
    await page.locator("button[type=submit]").click();
    await page.waitForTimeout(10000);
    // Page de confirmation Synapse éventuelle (uniquement si on est sur son URL)
    for (let i = 0; i < 2; i++) {
      if (!page.url().includes("/_synapse/")) break;
      const cont = page.locator("button:has-text('Continue'), a:has-text('Continue')");
      if (await cont.count()) { console.log("   Clic Continue (Synapse)"); await cont.first().click(); await page.waitForTimeout(6000); }
      else break;
    }
  }
  await page.waitForTimeout(8000);
  const url = page.url();
  console.log(`   URL apres SSO : ${url.slice(0, 80)}`);
  const text1 = await page.evaluate(() => document.body.innerText.slice(0, 250));
  console.log(`   Page : ${text1.replace(/\n/g, " | ").slice(0, 150)}`);

  // 2) Etat connecte : chercher le menu utilisateur / le bouton de creation de salon
  console.log("2. Verification de l'etat connecte...");
  const loggedIn = await page.evaluate(() => !!document.querySelector(".mx_UserMenu, .mx_LeftPanel, [aria-label*='User menu'], [data-testid='user-menu']"));
  console.log(`   Panneau gauche / menu utilisateur presents : ${loggedIn}`);

  // Fermer l'onboarding / verification d'identite (1re connexion)
  await page.waitForTimeout(4000);
  for (let round = 0; round < 8; round++) {
    await page.waitForTimeout(2500);
    let acted = false;
    if (await clickIfVisible(page, ".mx_CompleteSecurity_skip", 1200)) { console.log("   Skip verification"); acted = true; }
    if (!acted && await clickIfVisible(page, "text=I'll verify later", 1200)) { console.log("   I'll verify later"); acted = true; }
    if (!acted && await clickIfVisible(page, "button:has-text('Later')", 1200)) { console.log("   Later"); acted = true; }
    if (!acted && await clickIfVisible(page, "text=Dismiss", 1200)) { console.log("   Dismiss"); acted = true; }
    if (!acted && await clickIfVisible(page, "text=Got it", 1200)) { console.log("   Got it"); acted = true; }
    const panel = acted ? false : await page.evaluate(() =>
      !!document.querySelector(".mx_LeftPanel, .mx_RoomSublist, .mx_RoomList, [data-testid='room-list']"),
    );
    if (!acted && panel) break;
    if (!acted) break;
  }
  await page.waitForTimeout(3000);
  const midText = await page.evaluate(() => document.body.innerText.slice(0, 200));
  console.log(`   Page apres dialogues : ${midText.replace(/\n/g, " | ").slice(0, 130)}`);

  // 3) Ouvrir un salon existant ou en CREER un (install fraiche)
  console.log("3. Ouverture/creation d'un salon...");
  let roomOpen = false;
  const existing = page.locator("div[class*=roomName]").filter({ hasText: "reunion-client" }).first();
  if (await existing.count()) {
    await existing.click();
    await page.waitForTimeout(4000);
    roomOpen = true;
    console.log("   Salon 'reunion-client' ouvert");
  } else {
    console.log("   Aucun salon -> creation via 'New room'");
    let newRoomBtn = page.locator("[aria-label='New room']").first();
    try { await newRoomBtn.waitFor({ state: "visible", timeout: 8000 }); } catch { newRoomBtn = null; }
    if (!newRoomBtn) newRoomBtn = page.locator("text=Create a Group Chat").first();
    if (await newRoomBtn.count()) {
      await newRoomBtn.click();
      await page.waitForTimeout(2500);
      // Champ nom du dialogue de creation (input TEXTE visible, pas l'avatar)
      const nameInput = page.locator("input[type=text]:visible, input[placeholder*='Name']:visible").first();
      if (await nameInput.count()) await nameInput.fill("salon-e2e");
      // Valider (bouton Create room / Create)
      const createBtn = page.locator("button:has-text('Create room'), button:has-text('Create')").last();
      if (await createBtn.count()) await createBtn.click();
      else await page.keyboard.press("Enter");
      await page.waitForTimeout(8000);
      const txt = await page.evaluate(() => document.body.innerText);
      roomOpen = txt.includes("salon-e2e");
      console.log(`   Salon 'salon-e2e' cree et ouvert : ${roomOpen ? "OUI" : "a verifier"}`);
    } else {
      console.log("   Bouton New room introuvable");
    }
  }

  console.log("4. Envoi d'un message...");
  const composer = page.locator("[contenteditable='true'], div[class*=composer], .mx_BasicMessageComposer").first();
  let sent = false;
  if (await composer.count()) {
    const msg = `test-e2e-${Date.now()}`;
    await composer.click();
    await page.keyboard.type(msg);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(4000);
    const body = await page.evaluate(() => document.body.innerText);
    sent = body.includes(msg);
    console.log(`   Message '${msg}' envoye et visible : ${sent ? "OUI" : "NON"}`);
  } else {
    console.log("   Composer introuvable");
  }

  // 4) Screenshot de preuve
  await page.screenshot({ path: "e2e-element-web.png", fullPage: false });

  console.log("\n--- ERREURS CAPTUREES (filtrees) ---");
  const real = logs.filter((l) => !/room_keys\/version|\.well-known|typing|receipts|presence/.test(l));
  for (const l of real.slice(-10)) { console.log(l); }

  await browser.close();
})().catch((e) => { console.error("ERREUR SCRIPT:", e); process.exit(1); });
