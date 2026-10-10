// Language switch (English / हिन्दी). Elements use data-i18n="key", data-i18n-html, data-i18n-ph (placeholder), data-i18n-title.
(function () {
  const D = {
    en: {
      "brand": "Sanjeevani Clinic",
      "nav.home": "Home", "nav.screening": "Covid screening", "nav.assistant": "AI assistant", "nav.nlp": "NLP lab", "nav.profile": "My profile",
      "footer.note": "This site assists triage and booking. It does not replace a doctor's examination or diagnosis. In an emergency, go to the nearest hospital.",
      "auth.signin": "Sign in", "auth.logout": "Log out", "auth.title": "Sign in to continue",
      "auth.sub": "We save a short summary of your visits so we can pick up where you left off.",
      "auth.login": "Log in", "auth.signup": "Create account", "auth.name": "Full name", "auth.email": "Email", "auth.pass": "Password", "auth.hint": "At least 6 characters",
      "dock.title": "Chat with us", "dock.sub": "Book a doctor, ask a question", "dock.expand": "Open full page", "dock.min": "Minimise",
      "chat.name": "Sanjeevani assistant", "chat.online": "● Online", "chat.q1": "I have fever and cough", "chat.q2": "Is a neurologist available today?", "chat.q3": "I want to book a doctor",
      "chat.remove": "Remove", "chat.ph": "Describe your symptoms, attach a photo, or ask for a doctor", "chat.done": "Appointment confirmed", "chat.pick": "Pick a time",
      "cp.welcome": "Welcome", "cp.hi": "Hi", "cp.saved": "Your visits are saved so the assistant can follow up.", "cp.visits": "Upcoming and recent visits",
      "cp.none": "No visits yet. Ask the assistant to book one.",
      "cp.emerg": "<strong>Emergency?</strong> Chest pain, trouble breathing, heavy bleeding or fainting: go to the nearest hospital now. Do not wait for a chat reply.",
      "home.eyebrow": "Screening desk · open now", "home.h1": "Check your risk, then <em>book the right doctor</em> in minutes.",
      "home.lede": "Take a one-minute covid screening, or just tell our AI assistant how you feel. It can look at a photo of an injury, find a doctor with free slots and remember you the next time you visit.",
      "home.cta1": "Start screening", "home.cta2": "Talk to the assistant", "home.t1": "Takes under a minute", "home.t2": "Real doctors, real slots", "home.t3": "Not a diagnosis",
      "home.s1e": "What you can do", "home.s1h": "Everything a front desk does, without the queue.",
      "home.f1h": "Covid screening", "home.f1p": "Enter age, fever, cough and city. A trained model gives an instant risk estimate.",
      "home.f2h": "AI assistant", "home.f2p": "Describe symptoms in English or Hinglish. It asks only what is missing.",
      "home.f3h": "Photo understanding", "home.f3p": "Share a photo of a rash or injury and it points you to the right specialist.",
      "home.f4h": "Easy booking", "home.f4p": "Pick a free slot on a doctor card. A returning patient keeps the same doctor.",
      "home.s2e": "How it works", "home.s2h": "Three steps from symptom to appointment.",
      "home.p1h": "Tell us how you feel", "home.p1p": "Use the screening form or chat with the assistant.",
      "home.p2h": "Get a first read", "home.p2p": "See your screening estimate and the specialist you should consult.",
      "home.p3h": "Book a slot", "home.p3p": "Tap a free time on a doctor card. Your visit summary is saved for next time.",
      "home.band": "<strong>Please note:</strong> the screening is a rough estimate from a small demo model. Only a doctor can diagnose. If you have chest pain, trouble breathing or heavy bleeding, go to the emergency room now.",
      "pr.eyebrow": "Screening desk", "pr.h1": "Covid screening", "pr.sub": "Fill in the details below to get an instant screening estimate.",
      "pr.age": "Age (years)", "pr.fever": "Body temperature (°F)", "pr.hint": "Normal is about 98.6°F", "pr.gender": "Gender", "pr.male": "Male", "pr.female": "Female",
      "pr.cough": "Cough", "pr.mild": "Mild", "pr.strong": "Strong", "pr.city": "City", "pr.submit": "Check my result",
      "pr.high": "Higher covid risk", "pr.low": "Lower covid risk", "pr.conf": "Model confidence",
      "pr.disc": "This is a screening estimate from a small demo model, not a diagnosis. Please consult a doctor to confirm.", "pr.book": "Book a doctor with the assistant",
      "pr.before": "Before you start", "pr.l1": "Measure your temperature with a thermometer if you can.", "pr.l2": "Choose \"Strong\" cough if it is frequent or painful.",
      "pr.l3": "The result is only a first read to help the doctor prioritise.", "pr.l4": "Prefer to chat? The AI assistant can run this screening for you.",
      "nlp.eyebrow": "Pretrained NLP", "nlp.sub": "Paste a patient message to see part-of-speech tags, named entities, similar words and a sentiment score.",
      "nlp.text": "Your text", "nlp.go": "Analyze text", "nlp.pos": "Part-of-speech tags", "nlp.ner": "Named entities", "nlp.nersub": "People, places and organisations",
      "nlp.sim": "Similar words", "nlp.simsub": "GloVe embeddings for the first word", "nlp.sent": "Sentiment",
      "pf.gate.h": "Please sign in", "pf.gate.p": "Sign in to see your appointments, screenings and visit summary.", "pf.patient": "Patient", "pf.welcome": "Welcome,",
      "pf.book": "Book with assistant", "pf.runscreen": "Run screening",
      "pf.overview": "Overview", "pf.appts": "My appointments", "pf.today": "Today's appointments", "pf.screen": "Screening history", "pf.notes": "Visit notes", "pf.details": "Profile details",
      "pf.s1": "Upcoming", "pf.s2": "Total visits", "pf.s3": "Screenings", "pf.s4": "Member since",
      "pf.next": "Next appointment", "pf.nonext": "No upcoming appointment. Book one with the assistant.", "pf.last": "Latest screening", "pf.noscreen": "No screening yet. Run one from the screening page or the assistant.",
      "pf.token": "Token #", "pf.doctor": "Doctor", "pf.spec": "Specialization", "pf.date": "Date", "pf.time": "Time", "pf.status": "Status",
      "pf.noappt": "No appointments yet.", "pf.notoday": "No appointments today.", "pf.cancel": "Cancel", "pf.confirm": "Cancel this appointment?", "pf.cancelled": "Appointment cancelled. The slot is free again.",
      "pf.when": "When", "pf.age": "Age", "pf.gender": "Gender", "pf.fever": "Fever", "pf.cough": "Cough", "pf.city": "City", "pf.result": "Result", "pf.conf": "Confidence", "pf.via": "Via",
      "pf.sum": "Assistant's summary of your visits", "pf.sumnote": "A short note the assistant keeps so it can follow up with you. It is not a medical record.",
      "pf.nosum": "Nothing yet. Chat with the assistant and a summary will appear here.", "pf.hist": "Doctors you have booked", "pf.nohist": "No bookings yet.",
      "pf.dname": "Name", "pf.demail": "Email", "pf.dsince": "Member since", "pf.drole": "Account type",
      "pf.rx": "Prescriptions", "pf.bills": "Bills", "pf.records": "Medical records", "pf.mydoc": "My doctor", "pf.s5": "Pending bills",
      "pf.medicine": "Medicine", "pf.dosage": "Dosage", "pf.note": "Note", "pf.desc": "Description", "pf.amount": "Amount", "pf.due": "Total due", "pf.visits": "visits",
      "pf.norx": "No prescriptions yet. Prescriptions added by your doctor will appear here.", "pf.nobills": "No bills yet.", "pf.allpaid": "All bills are paid.",
      "pf.norec": "No medical records yet. Reports added by the clinic will appear here.", "pf.nodoc": "No assigned doctor yet. Book an appointment and your doctor will appear here.",
      "pf.bookagain": "Book again", "pf.resched": "Reschedule", "pf.rstitle": "Pick a new time", "pf.rsnone": "No other free times for this doctor right now.", "pf.rsok": "Appointment moved to", "pf.close": "Close",
      "bill.pending": "Pending", "bill.paid": "Paid",
      "mine.h": "Your health at a glance", "mine.sub": "Everything about your visits in one place.", "mine.open": "Open my profile",
      "spec.General Physician": "General Physician", "spec.Neurologist": "Neurologist", "spec.Orthopedic": "Orthopedic", "spec.Gastroenterologist": "Gastroenterologist", "spec.Dermatologist": "Dermatologist", "spec.ENT": "ENT",
      "st.upcoming": "Upcoming", "st.past": "Past", "st.cancelled": "Cancelled",
      "val.Male": "Male", "val.Female": "Female", "val.Mild": "Mild", "val.Strong": "Strong", "via.chat": "Assistant", "via.form": "Form"
    },
    hi: {
      "brand": "संजीवनी क्लिनिक",
      "nav.home": "होम", "nav.screening": "कोविड स्क्रीनिंग", "nav.assistant": "एआई सहायक", "nav.nlp": "एनएलपी लैब", "nav.profile": "मेरी प्रोफ़ाइल",
      "footer.note": "यह साइट जाँच-पूर्व छँटाई और बुकिंग में मदद करती है। यह डॉक्टर की जाँच या निदान की जगह नहीं लेती। आपात स्थिति में नज़दीकी अस्पताल जाएँ।",
      "auth.signin": "साइन इन", "auth.logout": "लॉग आउट", "auth.title": "आगे बढ़ने के लिए साइन इन करें",
      "auth.sub": "हम आपकी विज़िट का छोटा सारांश सहेजते हैं ताकि अगली बार वहीं से शुरू कर सकें।",
      "auth.login": "लॉग इन", "auth.signup": "खाता बनाएँ", "auth.name": "पूरा नाम", "auth.email": "ईमेल", "auth.pass": "पासवर्ड", "auth.hint": "कम से कम 6 अक्षर",
      "dock.title": "हमसे बात करें", "dock.sub": "डॉक्टर बुक करें, सवाल पूछें", "dock.expand": "पूरा पेज खोलें", "dock.min": "छोटा करें",
      "chat.name": "संजीवनी सहायक", "chat.online": "● ऑनलाइन", "chat.q1": "मुझे बुखार और खाँसी है", "chat.q2": "क्या आज न्यूरोलॉजिस्ट उपलब्ध हैं?", "chat.q3": "मुझे डॉक्टर बुक करना है",
      "chat.remove": "हटाएँ", "chat.ph": "अपने लक्षण लिखें, फोटो जोड़ें या डॉक्टर के बारे में पूछें", "chat.done": "अपॉइंटमेंट पक्का हो गया", "chat.pick": "समय चुनें",
      "cp.welcome": "स्वागत है", "cp.hi": "नमस्ते", "cp.saved": "आपकी विज़िट सहेजी जाती हैं ताकि सहायक फ़ॉलो-अप कर सके।", "cp.visits": "आने वाली और पिछली विज़िट",
      "cp.none": "अभी कोई विज़िट नहीं। सहायक से बुकिंग के लिए कहें।",
      "cp.emerg": "<strong>आपात स्थिति?</strong> सीने में दर्द, साँस लेने में तकलीफ़, ज़्यादा खून बहना या बेहोशी: अभी नज़दीकी अस्पताल जाएँ। चैट के जवाब का इंतज़ार न करें।",
      "home.eyebrow": "स्क्रीनिंग डेस्क · अभी खुला है", "home.h1": "अपना जोखिम जाँचें, फिर मिनटों में <em>सही डॉक्टर बुक करें</em>।",
      "home.lede": "एक मिनट की कोविड स्क्रीनिंग करें, या बस एआई सहायक को बताएँ कि आप कैसा महसूस कर रहे हैं। यह चोट की फोटो देख सकता है, खाली स्लॉट वाला डॉक्टर ढूँढ सकता है और अगली बार आपको याद रखता है।",
      "home.cta1": "स्क्रीनिंग शुरू करें", "home.cta2": "सहायक से बात करें", "home.t1": "एक मिनट से कम", "home.t2": "असली डॉक्टर, असली स्लॉट", "home.t3": "यह निदान नहीं है",
      "home.s1e": "आप क्या कर सकते हैं", "home.s1h": "फ्रंट डेस्क का हर काम, बिना कतार के।",
      "home.f1h": "कोविड स्क्रीनिंग", "home.f1p": "उम्र, बुखार, खाँसी और शहर भरें। प्रशिक्षित मॉडल तुरंत जोखिम का अनुमान देता है।",
      "home.f2h": "एआई सहायक", "home.f2p": "लक्षण हिंदी, अंग्रेज़ी या हिंग्लिश में बताएँ। यह सिर्फ़ वही पूछता है जो कम है।",
      "home.f3h": "फोटो समझना", "home.f3p": "दाने या चोट की फोटो भेजें, यह सही विशेषज्ञ बताएगा।",
      "home.f4h": "आसान बुकिंग", "home.f4p": "डॉक्टर कार्ड पर खाली समय चुनें। पुराने मरीज़ को वही डॉक्टर मिलते हैं।",
      "home.s2e": "यह कैसे काम करता है", "home.s2h": "लक्षण से अपॉइंटमेंट तक तीन कदम।",
      "home.p1h": "अपनी हालत बताएँ", "home.p1p": "स्क्रीनिंग फ़ॉर्म भरें या सहायक से चैट करें।",
      "home.p2h": "पहला अनुमान पाएँ", "home.p2p": "अपना स्क्रीनिंग अनुमान और किस विशेषज्ञ से मिलना है, देखें।",
      "home.p3h": "स्लॉट बुक करें", "home.p3p": "डॉक्टर कार्ड पर खाली समय दबाएँ। आपकी विज़िट का सारांश अगली बार के लिए सहेजा जाता है।",
      "home.band": "<strong>ध्यान दें:</strong> स्क्रीनिंग एक छोटे डेमो मॉडल का मोटा अनुमान है। निदान सिर्फ़ डॉक्टर कर सकते हैं। सीने में दर्द, साँस में तकलीफ़ या ज़्यादा खून बहने पर तुरंत इमरजेंसी में जाएँ।",
      "pr.eyebrow": "स्क्रीनिंग डेस्क", "pr.h1": "कोविड स्क्रीनिंग", "pr.sub": "तुरंत स्क्रीनिंग अनुमान पाने के लिए नीचे जानकारी भरें।",
      "pr.age": "उम्र (वर्ष)", "pr.fever": "शरीर का तापमान (°F)", "pr.hint": "सामान्य तापमान लगभग 98.6°F होता है", "pr.gender": "लिंग", "pr.male": "पुरुष", "pr.female": "महिला",
      "pr.cough": "खाँसी", "pr.mild": "हल्की", "pr.strong": "तेज़", "pr.city": "शहर", "pr.submit": "मेरा नतीजा देखें",
      "pr.high": "कोविड का ज़्यादा जोखिम", "pr.low": "कोविड का कम जोखिम", "pr.conf": "मॉडल का भरोसा",
      "pr.disc": "यह एक छोटे डेमो मॉडल का स्क्रीनिंग अनुमान है, निदान नहीं। पुष्टि के लिए कृपया डॉक्टर से मिलें।", "pr.book": "सहायक से डॉक्टर बुक करें",
      "pr.before": "शुरू करने से पहले", "pr.l1": "हो सके तो थर्मामीटर से तापमान नापें।", "pr.l2": "खाँसी बार-बार आए या दर्द करे तो \"तेज़\" चुनें।",
      "pr.l3": "यह नतीजा सिर्फ़ पहला अनुमान है, जिससे डॉक्टर प्राथमिकता तय कर सकें।", "pr.l4": "चैट पसंद है? एआई सहायक यह स्क्रीनिंग आपके लिए कर सकता है।",
      "nlp.eyebrow": "प्रीट्रेंड एनएलपी", "nlp.sub": "मरीज़ का संदेश डालें और देखें: शब्द-भेद, नामित इकाइयाँ, मिलते-जुलते शब्द और भावना स्कोर।",
      "nlp.text": "आपका टेक्स्ट", "nlp.go": "टेक्स्ट जाँचें", "nlp.pos": "शब्द-भेद (POS) टैग", "nlp.ner": "नामित इकाइयाँ", "nlp.nersub": "लोग, जगहें और संस्थाएँ",
      "nlp.sim": "मिलते-जुलते शब्द", "nlp.simsub": "पहले शब्द के लिए GloVe एम्बेडिंग", "nlp.sent": "भावना (सेंटीमेंट)",
      "pf.gate.h": "कृपया साइन इन करें", "pf.gate.p": "अपनी अपॉइंटमेंट, स्क्रीनिंग और विज़िट सारांश देखने के लिए साइन इन करें।", "pf.patient": "मरीज़", "pf.welcome": "स्वागत है,",
      "pf.book": "सहायक से बुक करें", "pf.runscreen": "स्क्रीनिंग करें",
      "pf.overview": "सारांश", "pf.appts": "मेरी अपॉइंटमेंट", "pf.today": "आज की अपॉइंटमेंट", "pf.screen": "स्क्रीनिंग इतिहास", "pf.notes": "विज़िट नोट्स", "pf.details": "प्रोफ़ाइल विवरण",
      "pf.s1": "आने वाली", "pf.s2": "कुल विज़िट", "pf.s3": "स्क्रीनिंग", "pf.s4": "सदस्यता तिथि",
      "pf.next": "अगली अपॉइंटमेंट", "pf.nonext": "कोई आने वाली अपॉइंटमेंट नहीं। सहायक से बुक करें।", "pf.last": "आख़िरी स्क्रीनिंग", "pf.noscreen": "अभी कोई स्क्रीनिंग नहीं। स्क्रीनिंग पेज या सहायक से करें।",
      "pf.token": "टोकन #", "pf.doctor": "डॉक्टर", "pf.spec": "विशेषज्ञता", "pf.date": "तारीख़", "pf.time": "समय", "pf.status": "स्थिति",
      "pf.noappt": "अभी कोई अपॉइंटमेंट नहीं।", "pf.notoday": "आज कोई अपॉइंटमेंट नहीं।", "pf.cancel": "रद्द करें", "pf.confirm": "यह अपॉइंटमेंट रद्द करें?", "pf.cancelled": "अपॉइंटमेंट रद्द हो गई। स्लॉट फिर से खाली है।",
      "pf.when": "कब", "pf.age": "उम्र", "pf.gender": "लिंग", "pf.fever": "बुखार", "pf.cough": "खाँसी", "pf.city": "शहर", "pf.result": "नतीजा", "pf.conf": "भरोसा", "pf.via": "माध्यम",
      "pf.sum": "आपकी विज़िट का सहायक का सारांश", "pf.sumnote": "सहायक आपसे फ़ॉलो-अप करने के लिए एक छोटा नोट रखता है। यह मेडिकल रिकॉर्ड नहीं है।",
      "pf.nosum": "अभी कुछ नहीं। सहायक से चैट करें, सारांश यहाँ दिखेगा।", "pf.hist": "आपके बुक किए गए डॉक्टर", "pf.nohist": "अभी कोई बुकिंग नहीं।",
      "pf.dname": "नाम", "pf.demail": "ईमेल", "pf.dsince": "सदस्यता तिथि", "pf.drole": "खाते का प्रकार",
      "pf.rx": "प्रिस्क्रिप्शन", "pf.bills": "बिल", "pf.records": "मेडिकल रिकॉर्ड", "pf.mydoc": "मेरे डॉक्टर", "pf.s5": "बकाया बिल",
      "pf.medicine": "दवा", "pf.dosage": "खुराक", "pf.note": "नोट", "pf.desc": "विवरण", "pf.amount": "राशि", "pf.due": "कुल बकाया", "pf.visits": "विज़िट",
      "pf.norx": "अभी कोई प्रिस्क्रिप्शन नहीं। डॉक्टर द्वारा जोड़े गए प्रिस्क्रिप्शन यहाँ दिखेंगे।", "pf.nobills": "अभी कोई बिल नहीं।", "pf.allpaid": "सभी बिल चुकाए जा चुके हैं।",
      "pf.norec": "अभी कोई मेडिकल रिकॉर्ड नहीं। क्लिनिक द्वारा जोड़ी गई रिपोर्ट यहाँ दिखेंगी।", "pf.nodoc": "अभी कोई डॉक्टर असाइन नहीं। अपॉइंटमेंट बुक करें, आपके डॉक्टर यहाँ दिखेंगे।",
      "pf.bookagain": "फिर से बुक करें", "pf.resched": "समय बदलें", "pf.rstitle": "नया समय चुनें", "pf.rsnone": "इन डॉक्टर के लिए अभी कोई और खाली समय नहीं।", "pf.rsok": "अपॉइंटमेंट बदलकर", "pf.close": "बंद करें",
      "bill.pending": "बकाया", "bill.paid": "चुकाया",
      "mine.h": "आपकी सेहत एक नज़र में", "mine.sub": "आपकी विज़िट की सारी जानकारी एक जगह।", "mine.open": "मेरी प्रोफ़ाइल खोलें",
      "spec.General Physician": "सामान्य चिकित्सक", "spec.Neurologist": "न्यूरोलॉजिस्ट", "spec.Orthopedic": "हड्डी रोग विशेषज्ञ", "spec.Gastroenterologist": "गैस्ट्रोएंटेरोलॉजिस्ट", "spec.Dermatologist": "त्वचा रोग विशेषज्ञ", "spec.ENT": "ईएनटी",
      "st.upcoming": "आने वाली", "st.past": "बीती हुई", "st.cancelled": "रद्द",
      "val.Male": "पुरुष", "val.Female": "महिला", "val.Mild": "हल्की", "val.Strong": "तेज़", "via.chat": "सहायक", "via.form": "फ़ॉर्म"
    }
  };
  let lang = "en";
  try { lang = localStorage.getItem("sj_lang") || "en"; } catch (e) {}
  if (!D[lang]) lang = "en";
  window.LANG = lang;

  window.t = function (key, fallback) {
    if (key === "" || key == null) return "";
    return (D[window.LANG] && D[window.LANG][key]) || D.en[key] || fallback || key;
  };
  window.applyI18n = function (root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach(e => { e.textContent = window.t(e.dataset.i18n, e.textContent); });
    root.querySelectorAll("[data-i18n-html]").forEach(e => { e.innerHTML = window.t(e.dataset.i18nHtml, e.innerHTML); });
    root.querySelectorAll("[data-i18n-ph]").forEach(e => { e.placeholder = window.t(e.dataset.i18nPh, e.placeholder); });
    root.querySelectorAll("[data-i18n-title]").forEach(e => { e.title = window.t(e.dataset.i18nTitle, e.title); });
    document.documentElement.lang = window.LANG === "hi" ? "hi" : "en";
  };
  window.setLang = function (l) {
    if (!D[l]) return;
    window.LANG = l; try { localStorage.setItem("sj_lang", l); } catch (e) {}
    window.applyI18n(document);
    document.dispatchEvent(new Event("langchange"));
  };
  window.applyI18n(document);
})();
