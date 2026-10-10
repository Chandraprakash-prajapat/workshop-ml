// Floating assistant (like a messaging dock). Shown on every page except the full /chatbot page.
(function () {
  if (location.pathname.indexOf("/chatbot") === 0) return;
  const KEY = "sj_dock";
  const get = () => { try { return sessionStorage.getItem(KEY); } catch (e) { return null; } };
  const set = v => { try { sessionStorage.setItem(KEY, v); } catch (e) {} };

  const box = document.createElement("div");
  box.className = "dock";
  box.innerHTML = `
    <button class="dock-launch" type="button" aria-label="Open assistant">
      <span class="dock-av"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 01-11.6 7.1L4 20l1-4.6A8 8 0 1121 12z"/></svg></span>
      <span class="dock-text"><b data-i18n="dock.title">Chat with us</b><small data-i18n="dock.sub">Book a doctor, ask a question</small></span>
    </button>
    <section class="dock-panel hide" role="dialog" aria-label="Sanjeevani assistant">
      <header>
        <span class="dock-av sm"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 01-11.6 7.1L4 20l1-4.6A8 8 0 1121 12z"/></svg></span>
        <span class="dock-head"><b data-i18n="chat.name">Sanjeevani assistant</b><small data-i18n="chat.online">● Online</small></span>
        <a class="dock-ic" href="/chatbot" title="Open full page" data-i18n-title="dock.expand" aria-label="Open full page"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg></a>
        <button class="dock-ic" type="button" data-close title="Minimise" data-i18n-title="dock.min" aria-label="Minimise"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14"/></svg></button>
      </header>
      <div class="dock-body"></div>
    </section>`;
  document.body.append(box);

  const launch = box.querySelector(".dock-launch"), panel = box.querySelector(".dock-panel"), body = box.querySelector(".dock-body");
  let mounted = false;
  function open() {
    launch.classList.add("hide"); panel.classList.remove("hide"); set("open");
    if (!mounted) { mounted = true; window.SJChat.mount(body, {}); }
  }
  function close() { panel.classList.add("hide"); launch.classList.remove("hide"); set("closed"); launch.focus(); }
  launch.onclick = open;
  box.querySelector("[data-close]").onclick = close;
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !panel.classList.contains("hide")) close(); });
  document.addEventListener("sj-open-dock", open);
  if (window.applyI18n) window.applyI18n(box);
  if (get() === "open") open();
})();
