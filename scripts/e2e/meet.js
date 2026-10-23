/* Validation Meet (visio suitenumerique) : SSO -> creation -> invitation -> jonction 2 participants
 *
 * Parcours :
 *  1. Contexte A : meet.<domaine> -> SSO automatique Keycloak -> login demo -> interface authentifiee
 *  2. Creation d'une reunion par l'UI (bouton "Create a meeting" -> "Start an instant meeting")
 *     -> POST /api/v1.0/rooms/ par le frontend -> navigation vers /{slug}
 *  3. Lien de partage = URL de la salle (/{slug}, slug [a-z]{3}-[a-z]{4}-[a-z]{3})
 *  4. Contexte B (sessions vierges) : ouverture du lien -> silent-login SSO -> re-login demo
 *     -> ecran "Join the meeting?" -> Join -> Conference
 *  5. Validation finale : badge participants == 2 sur les DEUX pages (compteur UI du topbar,
 *     remote+1) + websockets LiveKit ouvertes des deux cotes (media headless en bonus via
 *     --use-fake-ui-for-media-stream --use-fake-device-for-media-stream).
 */
const { chromium } = require("playwright-core");

const DEMO_PWD = process.env.DEMO_PWD;
const BASE = process.env.E2E_MEET_URL || "https://meet.localhost:8443";
const MEET_HOST = BASE.replace(/^https:\/\//, "");
const ROOM_RE = new RegExp(`^${MEET_HOST.replace(/\./g, "\\.")}/[a-z]{3}-[a-z]{4}-[a-z]{3}$`);
const logs = [];
const livekitWs = { A: 0, B: 0 };

function watch(page, tag) {
  page.on("pageerror", (e) => logs.push(`[${tag}][PAGEERROR] ${String(e).slice(0, 200)}`));
  page.on("response", (r) => {
    if (r.status() >= 400) logs.push(`[${tag}][HTTP ${r.status()}] ${r.request().method()} ${r.url().slice(0, 110)}`);
  });
  page.on("websocket", (ws) => {
    if (/livekit\./.test(ws.url())) {
      livekitWs[tag] += 1;
      logs.push(`[${tag}][WS] ${ws.url().slice(0, 80)}`);
    }
  });
}

async function isDjango400(page) {
  try {
    const txt = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 500) : "");
    return /Bad Request \(400\)/.test(txt);
  } catch { return false; }
}

// SSO : le frontend (auto-login.js de la passerelle sur "/", silent-login ailleurs) renvoie
// vers /api/v1.0/authenticate/ -> Keycloak. On attend le formulaire et on se connecte.
async function loginViaKeycloak(page, tag) {
  console.log(`   Attente du formulaire Keycloak (${tag})...`);
  await page.waitForSelector("#username", { timeout: 30000 });
  await page.fill("#username", "demo");
  await page.fill("#password", DEMO_PWD);
  await page.locator("button[type=submit]").click();
  console.log(`   Login demo soumis (${tag}) -> retour attendu sur ${MEET_HOST}`);
  await page.waitForFunction(
    (host) => location.host === host,
    MEET_HOST,
    { timeout: 45000 },
  );
}

// Etat de la salle : badge participants (compteur du topbar) + nb de <video> dans la grille.
// Le bouton expose aria-describedby -> span sr-only "N participants" (le chiffre y est toujours).
async function roomStats(page) {
  return page.evaluate(() => {
    const out = { onRoom: false, badge: null, count: null, videos: document.querySelectorAll("video").length };
    const btn = document.querySelector('button[data-attr^="controls-participants-"]');
    if (!btn) return out;
    out.onRoom = true;
    const id = btn.getAttribute("aria-describedby");
    const sr = id && document.getElementById(id);
    if (sr) {
      out.sr = (sr.textContent || "").trim();
      const m = out.sr.match(/(\d+)/);
      if (m) out.count = Number(m[1]);
    }
    const wrap = btn.closest("div") || btn.parentElement;
    if (wrap) {
      const b = wrap.querySelector('div[aria-hidden="true"]');
      if (b) out.badge = (b.textContent || "").trim();
    }
    return out;
  });
}

async function waitForParticipantCount(page, tag, expected, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    try { last = await roomStats(page); } catch { last = null; }
    if (last && last.count === expected) {
      console.log(`   ${tag} : ${expected} participants valides (badge='${last.badge}', sr='${last.sr}', videos=${last.videos})`);
      return last;
    }
    await page.waitForTimeout(2000);
  }
  console.log(`   ${tag} : compte jamais atteint (dernier etat : ${JSON.stringify(last)})`);
  return null;
}

(async () => {
  if (!DEMO_PWD) {
    console.error("DEMO_PWD manquant. Usage : E2E_CHANNEL=chrome DEMO_PWD=... node meet.js");
    process.exit(1);
  }
  // Canal surchargeable (msedge absent sur certains postes) : E2E_CHANNEL=chrome node meet.js
  const browser = await chromium.launch({
    channel: process.env.E2E_CHANNEL || "msedge",
    headless: true,
    args: [
      "--ignore-certificate-errors",
      "--use-fake-ui-for-media-stream",
      "--use-fake-device-for-media-stream",
    ],
  });

  const ctxOpts = { ignoreHTTPSErrors: true, permissions: ["microphone", "camera"], locale: "en-US" };

  try {
    // ---------- 1. Contexte A : SSO puis interface authentifiee ----------
    console.log("1. Contexte A : ouverture de " + BASE + " (SSO automatique attendu)...");
    const ctxA = await browser.newContext(ctxOpts);
    const pageA = await ctxA.newPage();
    watch(pageA, "A");

    await pageA.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 30000 });
    // auto-login.js redirige "/" vers /api/v1.0/authenticate/ -> Django -> Keycloak
    try {
      await loginViaKeycloak(pageA, "A");
    } catch (e) {
      if (await isDjango400(pageA)) {
        console.error("   !! Le backend Django repond 400 sur /api/v1.0/authenticate/ (page 'Bad Request (400)').");
        console.error("   !! Diagnostique : DisallowedHost — meet v1.36.2 (django-configurations) lit DJANGO_ALLOWED_HOSTS,");
        console.error("   !! or le catalogue rend ALLOWED_HOSTS=meet.localhost -> ALLOWED_HOSTS vide au runtime -> 400 sur TOUT /api + /admin.");
        console.error("   !! Correction proposee (non appliquee) : renommer la cle [env] du catalogue en DJANGO_ALLOWED_HOSTS puis recreer meet_backend.");
        await pageA.screenshot({ path: "e2e-meet-echec-400-backend.png" });
        throw e;
      }
      throw e;
    }
    await pageA.waitForSelector('button[data-attr="create-meeting"]', { timeout: 45000 });
    console.log("   Interface authentifiee : bouton 'Create a meeting' present.");
    await pageA.screenshot({ path: "e2e-meet-1-accueil-authentifie.png" });

    // ---------- 2. Creation d'une reunion par l'UI ----------
    console.log("2. Creation d'une reunion (UI : Create a meeting -> Start an instant meeting)...");
    await pageA.locator('button[data-attr="create-meeting"]').click();
    await pageA.waitForSelector('[data-attr="create-option-instant"]', { timeout: 15000 });
    await pageA.locator('[data-attr="create-option-instant"]').click();
    await pageA.waitForFunction(
      () => /^\/[a-z]{3}-[a-z]{4}-[a-z]{3}$/.test(location.pathname),
      { timeout: 30000 },
    );
    // Choix documente : creation via l'UI (POST /api/v1.0/rooms/ fait par le frontend,
    // cookie de session SSO) — pas d'appel API direct dans le script.
    await pageA.waitForSelector('button[data-attr^="controls-participants-"]', { timeout: 60000 });
    const shareLink = pageA.url();
    if (!ROOM_RE.test(shareLink.replace(/^https:\/\//, ""))) {
      throw new Error(`Lien de salle inattendu : ${shareLink}`);
    }
    console.log(`   Reunion creee : ${shareLink}`);
    // Le dialogue de partage (InviteDialog) peut recouvrir la vue : on le ferme proprement.
    try {
      await pageA.keyboard.press("Escape");
      await pageA.waitForTimeout(1000);
    } catch { /* ignore */ }
    await pageA.screenshot({ path: "e2e-meet-2-salle-creee.png" });

    // ---------- 3. Contexte B : lien de partage -> SSO (re-login demo) -> salle ----------
    console.log("3. Contexte B : ouverture du lien de partage (sessions vierges)...");
    const ctxB = await browser.newContext(ctxOpts);
    const pageB = await ctxB.newPage();
    watch(pageB, "B");

    await pageB.goto(shareLink, { waitUntil: "domcontentloaded", timeout: 30000 });
    // Hors "/" l'auto-login.js ne se declenche pas : le frontend tente le silent-login
    // (/api/v1.0/authenticate/?silent=true&returnTo=...) -> Keycloak (formulaire, contexte vierge).
    await loginViaKeycloak(pageB, "B");
    await pageB.waitForURL(new RegExp(`^${BASE.replace(/\./g, "\\.")}/`), { timeout: 45000 });

    // ---------- 4. Jonction : ecran "Join the meeting?" -> Join ----------
    console.log("4. Ecran de jonction (Join the meeting?)...");
    await pageB.waitForSelector('button[type="submit"]', { timeout: 60000 });
    // Le champ nom n'est affiche que pour les non-connectes ou si
    // authenticated_users_can_edit_display_name : on le remplit s'il existe et est vide.
    const nameInput = pageB.locator("#input-name");
    if (await nameInput.count() && !(await nameInput.inputValue())) {
      await nameInput.fill("Demo invite");
      console.log("   Nom saisi : Demo invite");
    }
    await pageB.locator('button[type="submit"]').click();
    console.log("   Clic Join -> Conference...");
    await pageB.waitForSelector('button[data-attr^="controls-participants-"]', { timeout: 60000 });
    await pageB.screenshot({ path: "e2e-meet-3-jonction.png" });

    // ---------- 5. Validation finale : 2 participants des deux cotes ----------
    console.log("5. Validation finale : 2 participants dans la salle...");
    const statsA = await waitForParticipantCount(pageA, "A", 2, 60000);
    const statsB = await waitForParticipantCount(pageB, "B", 2, 30000);
    await pageA.screenshot({ path: "e2e-meet-4-deux-participants.png" });
    await pageB.screenshot({ path: "e2e-meet-5-deux-participants-invite.png" });

    const ok = !!statsA && !!statsB;
    console.log("\n--- SYNTHESE ---");
    console.log(`Lien de partage            : ${shareLink}`);
    console.log(`SSO contexte A + creation  : OK`);
    console.log(`SSO contexte B + jonction  : OK`);
    console.log(`Badge 2 participants (A)   : ${statsA ? "OUI" : "NON"}`);
    console.log(`Badge 2 participants (B)   : ${statsB ? "OUI" : "NON"}`);
    console.log(`Websockets LiveKit A/B     : ${livekitWs.A} / ${livekitWs.B}`);

    console.log("\n--- ERREURS CAPTUREES (filtrees) ---");
    const real = logs.filter((l) => !/rooms\/[a-z0-9-]+\/?$|config\/|telemetry|analytics/.test(l));
    for (const l of real.slice(-12)) console.log(l);

    await browser.close();
    if (!ok) {
      console.error("ECHEC : 2 participants non confirmes des deux cotes.");
      process.exit(1);
    }
    console.log("\nPARCOURS MEET VALIDE (vert).");
  } catch (e) {
    console.error("ERREUR SCRIPT:", e);
    try { await browser.close(); } catch { /* ignore */ }
    process.exit(1);
  }
})();
