// Reusable chat engine. Used by the popup on every page (dock.js) and by the full /chatbot page.
// Usage: SJChat.mount(containerElement, { onBooked: fn })
(function () {
  const KEY = "sj_chat_v2";
  const tr = (k, f) => (window.t ? window.t(k, f) : f || k);

  async function api(url, body) {
    const opt = body === undefined ? undefined : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    const r = await fetch("/chatbot" + url, opt);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || "Request failed");
    return d;
  }
  const load = () => { try { return JSON.parse(sessionStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
  const save = s => { try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  const initials = n => n.replace(/^Dr\.?\s*/i, "").split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase();

  function mount(root, opts) {
    opts = opts || {};
    root.classList.add("cx");
    root.innerHTML = `
      <div class="cx-log" aria-live="polite"></div>
      <div class="cx-quick">
        <button type="button" data-i18n="chat.q1">I have fever and cough</button>
        <button type="button" data-i18n="chat.q2">Is a neurologist available today?</button>
        <button type="button" data-i18n="chat.q3">I want to book a doctor</button>
      </div>
      <div class="cx-preview hide"><img alt=""><span></span><button type="button" data-i18n="chat.remove">Remove</button></div>
      <form class="cx-composer">
        <label class="icon-btn" title="Photo" aria-label="Photo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.5l-8.6 8.6a5 5 0 01-7.1-7.1l9-9a3.3 3.3 0 014.7 4.7l-9 9a1.7 1.7 0 01-2.4-2.4l8.3-8.3"/></svg>
          <input type="file" accept="image/*" class="hide">
        </label>
        <input class="input" data-i18n-ph="chat.ph" placeholder="Describe your symptoms, attach a photo, or ask for a doctor" autocomplete="off" aria-label="Message">
        <button class="send-btn" aria-label="Send"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg></button>
      </form>
      <div class="cx-auth hide">
        <h3 data-i18n="auth.title">Sign in to continue</h3>
        <p data-i18n="auth.sub">We save a short summary of your visits so we can pick up where you left off.</p>
        <div class="tabs"><button type="button" class="on" data-m="login" data-i18n="auth.login">Log in</button><button type="button" data-m="signup" data-i18n="auth.signup">Create account</button></div>
        <div class="field hide" data-name><label data-i18n="auth.name">Full name</label><input autocomplete="name" data-f="name"></div>
        <div class="field"><label data-i18n="auth.email">Email</label><input type="email" autocomplete="email" data-f="email"></div>
        <div class="field"><label data-i18n="auth.pass">Password</label><input type="password" autocomplete="current-password" data-f="password"><span class="hint hide" data-hint data-i18n="auth.hint">At least 6 characters</span></div>
        <div class="auth-err" role="alert"></div>
        <button type="button" class="btn btn-primary" data-submit style="width:100%" data-i18n="auth.login">Log in</button>
      </div>`;
    const $ = s => root.querySelector(s);
    const log = $(".cx-log"), form = $(".cx-composer"), text = form.querySelector(".input"), sendBtn = form.querySelector(".send-btn");
    const fileIn = form.querySelector("input[type=file]"), prev = $(".cx-preview"), quick = $(".cx-quick"), auth = $(".cx-auth");
    let mode = "login", photo = null, photoUrl = null, user = null, state = { uid: null, items: [] };

    const persist = () => { state.items = state.items.slice(-60); save(state); };
    const down = () => { log.scrollTop = log.scrollHeight; };
    const push = item => { state.items.push(item); persist(); draw(item); };

    function draw(it) {
      let n;
      if (it.k === "me" || it.k === "bot" || it.k === "err") {
        n = document.createElement("div"); n.className = "msg " + it.k;
        if (it.img) { const i = document.createElement("img"); i.src = it.img; i.alt = ""; n.append(i); }
        n.append(document.createTextNode(it.text || ""));
      } else if (it.k === "docs") {
        n = document.createDocumentFragment();
        it.docs.forEach(doc => n.append(card(doc, it)));
      } else if (it.k === "tool") {
        n = document.createElement("div");
        n.textContent = "🔧 Tool used: " + it.tools.map(t => t.tool).join(", ");
        n.style.cssText = "align-self:flex-start;margin:-2px 0 8px 4px;padding:3px 10px;font-size:12px;border-radius:12px;background:#e8f1ff;color:#1a4fa0;border:1px solid #c5d9f7;";
      } else if (it.k === "done") {
        n = document.createElement("div"); n.className = "confirm";
        n.innerHTML = '<div class="tick"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div><b data-i18n="chat.done">Appointment confirmed</b><span></span></div>';
        n.querySelector("span").textContent = it.doctor + " · " + it.when;
      }
      log.append(n); if (window.applyI18n) window.applyI18n(log); down();
    }
    function card(doc, item) {
      const c = document.createElement("div"); c.className = "doc-card";
      c.innerHTML = '<div class="doc-top"><div class="doc-av"></div><div><b></b><small></small></div></div><div class="slot-label" data-i18n="chat.pick">Pick a time</div><div class="slots"></div>';
      c.querySelector(".doc-av").textContent = initials(doc.name);
      c.querySelector("b").textContent = doc.name; c.querySelector("small").textContent = doc.specialty;
      doc.slots.forEach(s => {
        const b = document.createElement("button"); b.type = "button"; b.className = "slot"; b.textContent = s.label;
        b.onclick = () => book(s.id, c, item); c.querySelector(".slots").append(b);
      });
      return c;
    }
    function drawAll() { log.innerHTML = ""; state.items.forEach(draw); }
    function typing() { const t = document.createElement("div"); t.className = "typing"; t.innerHTML = "<i></i><i></i><i></i>"; log.append(t); down(); return t; }

    async function book(slotId, cardEl, item) {
      cardEl.querySelectorAll(".slot").forEach(b => b.disabled = true);
      try {
        const r = await api("/book", { slot_id: slotId });
        state.items = state.items.filter(x => x !== item); state.items.push({ k: "done", doctor: r.doctor, when: r.when });
        persist(); drawAll(); if (opts.onBooked) opts.onBooked();
      } catch (e) { push({ k: "err", text: e.message }); cardEl.querySelectorAll(".slot").forEach(b => b.disabled = false); }
    }
    function history() {
      return state.items.filter(x => x.k === "me" || x.k === "bot").slice(-12)
        .map(x => ({ role: x.k === "me" ? "user" : "assistant", content: x.text || "(photo)" }));
    }
    async function greet() {
      const t = typing();
      try { const r = await api("/greet?lang=" + (window.LANG || "en")); t.remove(); push({ k: "bot", text: r.reply }); }
      catch (e) { t.remove(); push({ k: "err", text: e.message }); }
    }
    function clearPhoto() { photo = null; if (photoUrl) URL.revokeObjectURL(photoUrl); photoUrl = null; fileIn.value = ""; prev.classList.add("hide"); }
    fileIn.onchange = e => {
      const f = e.target.files[0]; if (!f) return;
      if (f.size > 3e6) { push({ k: "err", text: "Photo is too large (max 3 MB)." }); fileIn.value = ""; return; }
      const r = new FileReader();
      r.onload = () => { photo = r.result.split(",")[1]; photoUrl = URL.createObjectURL(f);
        prev.querySelector("img").src = photoUrl; prev.querySelector("span").textContent = f.name; prev.classList.remove("hide"); };
      r.readAsDataURL(f);
    };
    prev.querySelector("button").onclick = clearPhoto;

    async function send(msg) {
      const img = photo, shown = photoUrl; photo = null; photoUrl = null; fileIn.value = ""; prev.classList.add("hide");
      const hist = history();
      state.items.push({ k: "me", text: msg || (img ? "(photo)" : "") }); persist();
      draw({ k: "me", text: msg, img: shown });       // thumbnail only on screen, never stored
      quick.classList.add("hide"); sendBtn.disabled = true;
      const t = typing();
      try {
        const r = await api("/message", { message: msg, history: hist, image: img, lang: window.LANG || "en" });
        t.remove(); push({ k: "bot", text: r.reply });
        if (r.tools_used && r.tools_used.length) push({ k: "tool", tools: r.tools_used });
        if (r.doctors && r.doctors.length) push({ k: "docs", docs: r.doctors });
      } catch (e) { t.remove(); push({ k: "err", text: e.message }); }
      sendBtn.disabled = false; text.focus();
    }
    form.onsubmit = e => { e.preventDefault(); const v = text.value.trim(); if (v || photo) { text.value = ""; send(v); } };
    quick.onclick = e => { if (e.target.tagName === "BUTTON") send(e.target.textContent); };

    // ----- login / signup panel -----
    auth.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {
      mode = b.dataset.m;
      auth.querySelectorAll(".tabs button").forEach(x => x.classList.toggle("on", x === b));
      auth.querySelector("[data-name]").classList.toggle("hide", mode === "login");
      auth.querySelector("[data-hint]").classList.toggle("hide", mode === "login");
      auth.querySelector("[data-submit]").setAttribute("data-i18n", mode === "login" ? "auth.login" : "auth.signup");
      if (window.applyI18n) window.applyI18n(auth); auth.querySelector(".auth-err").textContent = "";
    });
    async function submitAuth() {
      const btn = auth.querySelector("[data-submit]"); btn.disabled = true;
      const f = n => auth.querySelector(`[data-f=${n}]`).value;
      try { const d = await api("/" + mode, { name: f("name"), email: f("email"), password: f("password") }); if (d.role === "super_admin") location.href = "/admin"; else location.reload(); }
      catch (e) { auth.querySelector(".auth-err").textContent = e.message; btn.disabled = false; }
    }
    auth.querySelector("[data-submit]").onclick = submitAuth;
    auth.querySelectorAll("input").forEach(i => i.addEventListener("keydown", e => { if (e.key === "Enter") submitAuth(); }));

    // ----- start -----
    (async function init() {
      if (window.applyI18n) window.applyI18n(root);
      let me; try { me = await api("/me"); } catch (e) { me = {}; }
      if (!me.user) { auth.classList.remove("hide"); form.classList.add("hide"); quick.classList.add("hide"); return; }
      user = me.user; const old = load();
      if (old.uid === user.id && old.items && old.items.length) {
        state = old; drawAll(); if (state.items.some(x => x.k === "me")) quick.classList.add("hide");
      } else { state = { uid: user.id, items: [] }; persist(); await greet(); }
      text.focus();
    })();
    return { focus: () => text.focus() };
  }
  window.SJChat = { mount };
})();