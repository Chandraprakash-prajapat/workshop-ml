// Chat page logic: login popup, chat messages, doctor cards, booking, photo upload.
const $ = id => document.getElementById(id);
let mode = "login", chatHistory = [], photoB64 = null, photoUrl = null;

async function api(url, body) {
  const opt = body === undefined ? undefined : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch("/chatbot" + url, opt);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || "Request failed");
  return d;
}
function scrollDown() { $("log").scrollTop = $("log").scrollHeight; }
function add(text, cls, imgSrc) {
  const d = document.createElement("div"); d.className = "msg " + cls;
  if (imgSrc) { const i = document.createElement("img"); i.src = imgSrc; i.alt = "Your photo"; d.append(i); }
  if (text) d.append(document.createTextNode(text));
  $("log").append(d); scrollDown(); return d;
}
function typing() {
  const t = document.createElement("div"); t.className = "typing"; t.innerHTML = "<i></i><i></i><i></i>";
  $("log").append(t); scrollDown(); return t;
}
function initials(name) { return name.replace(/^Dr\.?\s*/i, "").split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase(); }

function doctorCards(docs) {
  docs.forEach(doc => {
    const c = document.createElement("div"); c.className = "doc-card";
    c.innerHTML = '<div class="doc-top"><div class="doc-av"></div><div><b></b><small></small></div></div><div class="slot-label">Pick a time</div><div class="slots"></div>';
    c.querySelector(".doc-av").textContent = initials(doc.name);
    c.querySelector("b").textContent = doc.name;
    c.querySelector("small").textContent = doc.specialty;
    doc.slots.forEach(s => {
      const b = document.createElement("button"); b.type = "button"; b.className = "slot"; b.textContent = s.label;
      b.onclick = () => book(s.id, c); c.querySelector(".slots").append(b);
    });
    $("log").append(c);
  });
  scrollDown();
}
async function book(slotId, card) {
  card.querySelectorAll(".slot").forEach(b => b.disabled = true);
  try {
    const r = await api("/book", { slot_id: slotId });
    const d = document.createElement("div"); d.className = "confirm";
    d.innerHTML = '<div class="tick"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div><b>Appointment confirmed</b><span></span></div>';
    d.querySelector("span").textContent = r.doctor + " · " + r.when;
    $("log").append(d); card.remove(); scrollDown(); loadMe();
  } catch (e) { add(e.message, "err"); card.querySelectorAll(".slot").forEach(b => b.disabled = false); }
}
async function loadMe() {
  const d = await api("/me");
  if (!d.user) { $("auth").classList.remove("hide"); return false; }
  $("auth").classList.add("hide"); $("who").textContent = "Hi, " + d.user.name;
  $("appts").innerHTML = d.appointments.length ? "" : '<p class="muted" style="font-size:.88rem">No visits yet. Ask the assistant to book one.</p>';
  d.appointments.forEach(a => {
    const e = document.createElement("div"); e.className = "appt"; e.innerHTML = "<b></b><span></span>";
    e.querySelector("b").textContent = a.name; e.querySelector("span").textContent = a.specialty + " · " + a.when;
    $("appts").append(e);
  });
  return true;
}
async function start() {
  if (!(await loadMe())) return;
  $("log").innerHTML = ""; chatHistory = [];
  const t = typing();
  try { const r = await api("/greet"); t.remove(); add(r.reply, "bot"); } catch (e) { t.remove(); add(e.message, "err"); }
  $("text").focus();
}
function clearPhoto() { photoB64 = null; if (photoUrl) URL.revokeObjectURL(photoUrl); photoUrl = null; $("photo").value = ""; $("preview").classList.add("hide"); }
$("photo").onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  if (f.size > 3e6) { add("Photo is too large (max 3 MB).", "err"); $("photo").value = ""; return; }
  const r = new FileReader();
  r.onload = () => { photoB64 = r.result.split(",")[1]; photoUrl = URL.createObjectURL(f);
    $("previewImg").src = photoUrl; $("previewName").textContent = f.name; $("preview").classList.remove("hide"); };
  r.readAsDataURL(f);
};
$("removePhoto").onclick = clearPhoto;

async function send(text) {
  const photo = photoB64, shown = photoUrl;
  photoB64 = null; photoUrl = null; $("photo").value = ""; $("preview").classList.add("hide");
  add(text, "me", shown); $("quick").classList.add("hide"); $("sendbtn").disabled = true;
  const t = typing();
  try {
    const r = await api("/message", { message: text, history: chatHistory, image: photo });
    t.remove(); add(r.reply, "bot");
    chatHistory.push({ role: "user", content: text || "(photo)" }, { role: "assistant", content: r.reply });
    if (r.doctors && r.doctors.length) doctorCards(r.doctors);
  } catch (e) { t.remove(); add(e.message, "err"); }
  $("sendbtn").disabled = false; $("text").focus();
}
$("form").onsubmit = e => { e.preventDefault(); const v = $("text").value.trim(); if (v || photoB64) { $("text").value = ""; send(v); } };
$("quick").onclick = e => { if (e.target.tagName === "BUTTON") send(e.target.textContent); };

document.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {
  mode = b.dataset.m;
  document.querySelectorAll(".tabs button").forEach(x => x.classList.toggle("on", x === b));
  $("nameWrap").classList.toggle("hide", mode === "login"); $("passHint").classList.toggle("hide", mode === "login");
  $("authbtn").textContent = mode === "login" ? "Log in" : "Create account"; $("autherr").textContent = "";
});
async function submitAuth() {
  $("authbtn").disabled = true;
  try { await api("/" + mode, { name: $("aname").value, email: $("aemail").value, password: $("apass").value }); location.reload(); }
  catch (e) { $("autherr").textContent = e.message; }
  $("authbtn").disabled = false;
}
$("authbtn").onclick = submitAuth;
["aname", "aemail", "apass"].forEach(id => $(id).addEventListener("keydown", e => { if (e.key === "Enter") submitAuth(); }));
$("logout").onclick = async () => { await api("/logout", {}); location.href = "/"; };
start();
