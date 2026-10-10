// Shared header logic: current page highlight, mobile menu, language switch, who is logged in.
(function () {
  const path = location.pathname.replace(/\/$/, "") || "/";
  document.querySelectorAll(".nav a").forEach(a => { if (a.dataset.path === path) a.classList.add("on"); });

  const btn = document.getElementById("menuBtn"), nav = document.getElementById("nav");
  btn.onclick = () => { const o = nav.classList.toggle("open"); btn.setAttribute("aria-expanded", o); };

  // language switch (EN / हिं)
  const langBtns = document.querySelectorAll(".lang button");
  function markLang() { langBtns.forEach(b => b.classList.toggle("on", b.dataset.lang === window.LANG)); }
  langBtns.forEach(b => b.onclick = () => window.setLang(b.dataset.lang));
  markLang(); document.addEventListener("langchange", markLang);

  // account area
  const box = document.getElementById("acct");
  fetch("/chatbot/me").then(r => r.json()).then(d => {
    if (!d.user) {
      box.innerHTML = '<a class="btn btn-primary" style="padding:8px 18px" href="/chatbot" data-i18n="auth.signin">Sign in</a>';
      window.applyI18n(box); return;
    }
    box.innerHTML = '<a class="chip" href="/profile" title="My profile"><span class="avatar"></span><span class="nm"></span></a><button type="button" data-i18n="auth.logout">Log out</button>';
    box.querySelector(".avatar").textContent = d.user.name.trim().charAt(0).toUpperCase();
    box.querySelector(".nm").textContent = d.user.name;
    const logout = async () => {
      try { sessionStorage.removeItem("sj_chat_v2"); sessionStorage.removeItem("sj_dock"); } catch (e) {}
      await fetch("/chatbot/logout", { method: "POST" }); location.href = "/";
    };
    box.querySelector("button").onclick = logout;
    // same links inside the mobile menu
    nav.insertAdjacentHTML("beforeend", '<a href="/profile" class="nav-extra" data-i18n="nav.profile">My profile</a><a href="#" class="nav-extra" id="navLogout" data-i18n="auth.logout">Log out</a>');
    document.getElementById("navLogout").onclick = e => { e.preventDefault(); logout(); };
    window.applyI18n(document);
  }).catch(() => {});
})();
