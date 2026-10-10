# Sanjeevani Clinic: Covid screening + AI assistant

A FastAPI web app for a clinic. Patients can run a covid screening, or chat with an AI assistant that finds doctors with free slots, reads a photo of an injury, books an appointment and remembers the patient next time.

## Features
| Feature | Where it lives |
|---|---|
| Covid screening form (trained sklearn model) | `/predict`, `src/` |
| AI assistant (Groq, tool calling) | `/chatbot`, `chatbot/` |
| Signup / login (bcrypt, session cookie) | `chatbot/routes.py`, `chatbot/security.py` |
| Doctor availability + atomic booking (MySQL) | `chatbot/database/crud.py` |
| Returning patient follow-up (short summary saved per user) | `summaries` table, `chatbot/agent.py` |
| Photo of an injury or rash (vision model) | `chatbot/vision.py` |
| Patient profile: appointments (cancel / reschedule), today's token, prescriptions, bills, medical records, my doctor, screening history | `/profile`, `chatbot/routes.py` |
| Staff page to add prescriptions, bills and records | `/admin`, `chatbot/admin.py` |
| Chat popup on every page + full chat page (same conversation) | `static/dock.js`, `static/chat.js` |
| English / Hindi switch for the whole UI and the assistant | `static/i18n.js` |
| Pretrained NLP demo (POS, NER, GloVe, VADER) | `/pretrained-nlp`, `nlp_pretrained/` |

## Safety rules built into the assistant
- It never diagnoses and never suggests medicines or creams.
- It never calls a doctor "best". Doctors are shown in random order.
- It runs the covid screening only after the patient has really typed age, gender, fever, cough and city. The server checks this, so the model cannot invent values.
- Severe symptoms (chest pain, trouble breathing, heavy bleeding, fainting) get an "go to the emergency room" reply.
- Screening results are always called a rough estimate.

## Folder structure
```
main.py                   FastAPI app: pages + includes the chatbot router
src/                      ML pipeline (ingestion, transformation, training, prediction)
chatbot/
  config.py               model names, specialties, Groq client
  agent.py                the AI loop: prompt, tool calls, summary
  tools.py                tools the AI may call (find doctors, screening, my appointments)
  vision.py               photo -> description + specialty
  security.py             password hashing
  routes.py               /chatbot/* endpoints (login, message, book)
  database/
    connection.py         MySQL connection, init_db(), slot generation
    crud.py               all SQL queries (create / read / update)
    schema.sql            tables + 10 doctors
templates/                base.html + one template per page
static/                   style.css (one stylesheet), app.js, chatbot.js
nlp_pretrained/           NLTK / GloVe / VADER helpers
artifacts/                trained model.pkl and preprocessor.pkl
```

## How a chat message flows
```
Browser (chatbot.js) -> POST /chatbot/message -> routes.py
   -> (photo?) vision.py describes it
   -> agent.py asks Groq, Groq may call a tool in tools.py
        find_available_doctors -> crud.py -> MySQL
        covid_screening        -> src/pipeline/predict_pipeline.py
   -> reply + doctor cards back to the browser
Browser -> POST /chatbot/book -> crud.book_slot (one UPDATE keeps it atomic)
```

## Database
`users`, `doctors`, `slots`, `appointments`, `patient_history`, `summaries`.
`init_db()` creates the database and tables if missing and adds slots for today plus the next 3 days (10 doctors x 5 slots per day).
Booking uses `UPDATE slots SET is_booked=1 WHERE id=? AND is_booked=0`, so two patients can never get the same slot.

## Setup
1. `uv sync` (or `pip install -r requirements.txt`)
2. Copy `.env.example` to `.env` and fill it in. Generate `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`.
3. Create the training artifacts once: `python -m src.pipeline.train_pipeline`
4. Make sure MySQL is running. The app creates the `clinic` database on start.
5. `python main.py`, then open http://127.0.0.1:8000

Never commit `.env` and never put it in a zip you share.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/`, `/predict`, `/pretrained-nlp`, `/chatbot` | pages |
| POST | `/predict`, `/pretrained-nlp` | form submit |
| GET | `/chatbot/me`, `/chatbot/greet` | who is logged in, first greeting |
| POST | `/chatbot/signup`, `/login`, `/logout` | account |
| POST | `/chatbot/message` | chat (optional photo) |
| POST | `/chatbot/book` | book a slot |
| GET | `/health` | health check |

## Manual test checklist
1. Sign up, then say you have fever and cough. The assistant asks for age, gender, fever, cough, city.
2. Give all five in one message. You get an estimate with a "not a diagnosis" note and doctor cards.
3. Click a slot. A confirmation appears and the sidebar shows the visit.
4. Log out, log in, say `hi`. The assistant asks a follow-up about your earlier problem.
5. Upload a photo with a note. You get a specialist and cards.

## Staff page
Put your email in `ADMIN_EMAILS` in `.env`, restart, sign in and open `/admin`. Add a prescription, bill or record using the patient's email. The patient sees it on `/profile`.

## Known limits
- The screening model is a small demo model. It is not medical advice.
- Photo reading needs a vision-capable model on your Groq account (`GROQ_VISION_MODEL`). Without one the assistant asks the patient to describe the problem in words.
- No password reset or email verification yet.
