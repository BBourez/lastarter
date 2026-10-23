/* Validation Meet (visio suitenumerique) : SSO -> creation -> invitation -> jonction 2 participants
 *
 * Parcours :
 *  1. Contexte A (SSO demo) : meet.<domaine> -> SSO Keycloak (auto-login passerelle)
 *     -> interface authentifiee -> creation par l'UI -> A entre dans la salle (badge = 1).
 *  2. Contexte B (sessions vierges) : ouvre le lien de partage -> silent-login (prompt=none).
 *     Sans session Keycloak, Keycloak repond login_required et rebondit sur la salle NON
 *     authentifiee : le script le detecte (users/me = 401) et relance un login COMPLET via
 *     l'URL du bouton Login de l'app (/api/v1.0/authenticate/?silent=false&returnTo=...)
 *     -> formulaire Keycloak -> re-login demo -> retour authentifie -> Join -> B entre.
 *     Effet produit ATTENDU (comportement amont concu) : B reprend l'identite LiveKit de
 *     l'utilisateur demo (identity = user.sub) -> A est ejecte (ecran "You have joined the
 *     meeting from another device").
 *  3. Contexte C (vierge, invite ANONYME — chemin produit "invité sans compte", salle
 *     publique, identity LiveKit = uuid4 unique, silentLogin=false pour eviter le rebond) :
 *     ouvre le lien -> Lobby -> nom -> Join -> C entre.
 *  4. Validation finale : badge participants == 2 sur B ET C (compteur topbar, remote+1)
 *     + websockets LiveKit ouvertes (media headless en bonus via --use-fake-ui-for-media-stream
 *     --use-fake-device-for-media-stream).
 */
const { chromium } = require("playwright-core");

const DEMO_PWD = process.env.DEMO_PWD;
const BASE = process.env.E2E_MEET_URL || "https://meet.localhost:8443";
const MEET_HOST = BASE.replace(/^https:\/\//, "");
const ROOM_RE = new RegExp(`^${MEET_HOST.replace(/\./g, "\\.")}/[a-z]{3}-[a-z]{4}-[a-z]{3}$`);
const logs = [];
const livekitWs = { A: 0, B: 0, C: 0 };

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

// Statut de session tel que le voit l'app (meme endpoint que le frontend).
// A n'appeler que lorsque la page est sur l'origine meet.
async function sessionStatus(page) {
  try {
    return await page.evaluate(async () => {
      const r = await fetch("/api/v1.0/users/me/", { credentials: "include" });
      return r.status;
    });
  } catch { return null; }
}

// Formulaire Keycloak : remplissage demo + soumission + retour attendu sur meet.
async function keycloakLogin(page, tag) {
  console.log(`   Formulaire Keycloak detecte (${tag}) -> login demo`);
  await page.waitForSelector("#username", { state: "visible", timeout: 15000 });
  await page.fill("#username", "demo");
  await page.fill("#password", DEMO_PWD);
  await page.locator("button[type=submit]").click();
  await page.waitForFunction(
    (host) => location.host === host,
    MEET_HOST,
    { timeout: 45000 },
  );
  console.log(`   Login demo soumis (${tag}) -> retour sur ${MEET_HOST}`);
}

/* Boucle SSO tolérante pour les contextes authentifies (A, B) : gere les
 * allers-retours du silent-login.
 * - sur id.<domaine> avec formulaire -> login demo
 * - sur meet non authentifie (users/me 401, cas du rebond silent-login) ->
 *   un seul login complet force via l'URL du bouton Login de l'app
 * - sur meet authentifie (users/me 200) -> termine
 */
async function ssoToMeet(page, tag, targetUrl, maxMs = 90000) {
  const deadline = Date.now() + maxMs;
  let forcedAttempts = 0;
  let kcAttempts = 0;
  while (Date.now() < deadline) {
    const url = page.url();
    if (!url.startsWith(BASE)) {
      const form = await page.locator("#username").waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false);
      if (form) {
        kcAttempts += 1;
        if (kcAttempts > 3) throw new Error(`Formulaire Keycloak representer 3 fois (${tag}) : verifier DEMO_PWD`);
        await keycloakLogin(page, tag);
      }
      continue;
    }
    if (await isDjango400(page)) {
      console.error("   !! Le backend Django repond 400 sur /api (page 'Bad Request (400)').");
      console.error("   !! Attendu : DisallowedHost (DJANGO_ALLOWED_HOSTS non pris en compte) — cf. README.");
      await page.screenshot({ path: "e2e-meet-echec-400-backend.png" });
      throw new Error(`Backend 400 (${tag})`);
    }
    const st = await sessionStatus(page);
    if (st === 200) {
      console.log(`   Session authentifiee confirmee (${tag}, users/me=200)`);
      return true;
    }
    if (st === 401 && forcedAttempts < 3) {
      // Le goto peut être interrompu par la navigation SPA en cours (rebond
      // silent-login, fenêtre anti-retry ~30 s côté frontend) : on réessaie
      // avec un temps de pose pour laisser le frontend retomber.
      forcedAttempts += 1;
      console.log(`   Non authentifie sur ${MEET_HOST} (${tag}, users/me=401) -> login complet via /api/v1.0/authenticate/ (essai ${forcedAttempts})`);
      await page.waitForTimeout(2000);
      await page.goto(
        `${BASE}/api/v1.0/authenticate/?silent=false&returnTo=${encodeURIComponent(targetUrl)}`,
        { waitUntil: "domcontentloaded", timeout: 45000 },
      ).catch(() => {});
      continue;
    }
    await page.waitForTimeout(1500);
  }
  throw new Error(`SSO non abouti vers ${targetUrl} apres ${maxMs / 1000}s (${tag})`);
}

// Etat de la salle : badge participants (compteur du topbar) + nb de <video> dans la grille.
// Le bouton expose aria-describedby -> span sr-only "N participants" (le chiffre y est toujours).
async function roomStats(page) {
  return page.evaluate(() => {
    const out = { onRoom: false, badge: null, count: null, videos: document.querySelectorAll("video").length, body: document.body ? document.body.innerText.slice(0, 200) : "" };
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
      console.log(`   ${tag} : ${expected} participant(s) valides (badge='${last.badge}', sr='${last.sr}', videos=${last.videos})`);
      return last;
    }
    await page.waitForTimeout(2000);
  }
  console.log(`   ${tag} : compte ${expected} jamais atteint (dernier etat : ${JSON.stringify(last && { onRoom: last.onRoom, count: last.count, badge: last.badge })})`);
  return null;
}

// Ecran de jonction (Lobby) : attend le formulaire, remplit le nom si present, clique Join.
async function joinFromLobby(page, tag, displayName) {
  await page.waitForSelector('button[type="submit"]', { timeout: 60000 });
  const nameInput = page.locator("#input-name");
  if (await nameInput.count()) {
    if (!(await nameInput.inputValue())) {
      await nameInput.fill(displayName);
      console.log(`   ${tag} : nom saisi : ${displayName}`);
    }
  }
  await page.locator('button[type="submit"]').click();
  console.log(`   ${tag} : clic Join -> Conference...`);
  await page.waitForSelector('button[data-attr^="controls-participants-"]', { timeout: 60000 });
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
    // ---------- 1. Contexte A : SSO puis creation ----------
    console.log("1. Contexte A : ouverture de " + BASE + " (SSO automatique attendu)...");
    const ctxA = await browser.newContext(ctxOpts);
    const pageA = await ctxA.newPage();
    watch(pageA, "A");

    await pageA.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 30000 });
    await ssoToMeet(pageA, "A", BASE + "/");
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
    try {
      await pageA.keyboard.press("Escape"); // ferme l'InviteDialog (partage)
      await pageA.waitForTimeout(1000);
    } catch { /* ignore */ }
    await pageA.screenshot({ path: "e2e-meet-2-salle-creee.png" });

    // A bien connecte au SFU (badge = 1) avant l'arrivee de B : sinon la course
    // d'identite LiveKit pourrait ejecter B au lieu de A.
    await waitForParticipantCount(pageA, "A", 1, 60000);

    // ---------- 3. Contexte B : lien -> SSO (re-login demo) -> salle ----------
    console.log("3. Contexte B : ouverture du lien de partage (sessions vierges)...");
    const ctxB = await browser.newContext(ctxOpts);
    const pageB = await ctxB.newPage();
    watch(pageB, "B");

    await pageB.goto(shareLink, { waitUntil: "domcontentloaded", timeout: 30000 });
    // Hors "/" l'auto-login.js ne se declenche pas : le frontend tente le silent-login
    // (prompt=none). Sans session Keycloak, Keycloak repond login_required et rebondit sur
    // la salle non authentifiee ; la boucle ssoToMeet force alors le login complet.
    await ssoToMeet(pageB, "B", shareLink);
    await joinFromLobby(pageB, "B", "Demo invite");
    await pageB.screenshot({ path: "e2e-meet-3-jonction-sso.png" });

    // Effet produit attendu : A (meme identite demo) est ejecte par LiveKit.
    await pageB.waitForTimeout(4000);
    try {
      const bodyA = await pageA.evaluate(() => document.body.innerText.slice(0, 400));
      if (/another device/i.test(bodyA)) {
        console.log("   A ejecte comme attendu (duplicate identity, ecran 'joined from another device').");
        await pageA.screenshot({ path: "e2e-meet-4-createur-ejecte-duplicate.png" });
      } else {
        console.log("   A toujours present (pas d'ecran duplicate identity).");
      }
    } catch { /* ignore */ }

    // ---------- 4. Contexte C : invite anonyme (identite unique, salle publique) ----------
    console.log("4. Contexte C : invite anonyme sur le lien (silentLogin=false)...");
    const ctxC = await browser.newContext(ctxOpts);
    const pageC = await ctxC.newPage();
    watch(pageC, "C");

    await pageC.goto(shareLink + "?silentLogin=false", { waitUntil: "domcontentloaded", timeout: 30000 });
    await joinFromLobby(pageC, "C", "Invite anonyme");
    await pageC.screenshot({ path: "e2e-meet-5-jonction-anonyme.png" });

    // ---------- 5. Validation finale : 2 participants des deux cotes ----------
    console.log("5. Validation finale : 2 participants dans la salle...");
    const statsB = await waitForParticipantCount(pageB, "B", 2, 60000);
    const statsC = await waitForParticipantCount(pageC, "C", 2, 30000);
    await pageB.screenshot({ path: "e2e-meet-6-deux-participants.png" });
    await pageC.screenshot({ path: "e2e-meet-7-deux-participants-invite.png" });

    const ok = !!statsB && !!statsC;
    console.log("\n--- SYNTHESE ---");
    console.log(`Lien de partage                  : ${shareLink}`);
    console.log(`SSO contexte A + creation        : OK`);
    console.log(`SSO contexte B (re-login) + join : OK`);
    console.log(`A ejecte (duplicate identity)    : documente (ecran produit concu)`);
    console.log(`Badge 2 participants (B, SSO)    : ${statsB ? "OUI" : "NON"}`);
    console.log(`Badge 2 participants (C, anonyme): ${statsC ? "OUI" : "NON"}`);
    console.log(`Websockets LiveKit A/B/C         : ${livekitWs.A} / ${livekitWs.B} / ${livekitWs.C}`);

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
