"""Tools the AI may call (sir's MCP-style idea, but plain functions). user_id comes from the server session, never from the AI."""
import re
from chatbot.config import SPECIALTIES
from chatbot.database import crud

SCHEMAS = [
 {"type": "function", "function": {"name": "find_available_doctors",
   "description": "Get doctors of one specialty with free appointment slots. Call when the patient wants a doctor/appointment or symptoms need a specialist.",
   "parameters": {"type": "object", "properties": {"specialty": {"type": "string", "enum": SPECIALTIES}}, "required": ["specialty"]}}},
 {"type": "function", "function": {"name": "covid_screening",
   "description": "Run the clinic's COVID screening model. Call ONLY after you know all five values from the patient.",
   "parameters": {"type": "object", "properties": {
      "age": {"type": "integer"}, "gender": {"type": "string", "enum": ["Male", "Female"]},
      "fever": {"type": "number", "description": "body temperature in Fahrenheit, e.g. 101 (convert if given in Celsius)"},
      "cough": {"type": "string", "enum": ["Mild", "Strong"]}, "city": {"type": "string"}},
    "required": ["age", "gender", "fever", "cough", "city"]}}},
 {"type": "function", "function": {"name": "get_my_appointments",
   "description": "Get this patient's recent appointments.", "parameters": {"type": "object", "properties": {}}}},
]

def check_screening_values(args):
    """Return a problem text if any of the 5 values is missing, a placeholder, or unrealistic."""
    try:
        age, fever = int(args.get("age")), float(args.get("fever"))
    except (TypeError, ValueError):
        return "age or fever is missing or not a number."
    if not 1 <= age <= 110:
        return "age is not realistic."
    if not (34 <= fever <= 43 or 94 <= fever <= 108):
        return "fever is not a realistic body temperature."
    city = str(args.get("city", "")).strip()
    if len(city) < 2 or any(c in city for c in "<>{}"):
        return "city is missing."
    if args.get("gender") not in ("Male", "Female") or args.get("cough") not in ("Mild", "Strong"):
        return "gender or cough is missing."
    return None

def values_come_from_patient(args, user_text):
    """The AI may only use values the patient really wrote (stops invented ages/cities)."""
    text = user_text.lower().translate(str.maketrans("०१२३४५६७८९", "0123456789"))   # Hindi digits too
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    def written(v):
        try:
            return any(float(n) == float(v) for n in numbers)
        except (TypeError, ValueError):
            return False
    if not written(args.get("age")):
        return "age was not told by the patient."
    if not written(args.get("fever")):
        return "fever was not told by the patient."
    if str(args.get("city", "")).strip().lower() not in text:
        return "city was not told by the patient."
    return None

def run_tool(name, args, user_id, user_text=""):
    if name == "find_available_doctors":
        spec = args.get("specialty")
        if spec not in SPECIALTIES:
            return {"error": "unknown specialty"}
        prior = crud.get_prior_doctor(user_id, spec)          # already under treatment -> same doctor
        docs = crud.get_available_doctors(spec, prior["id"] if prior else None)
        return {"doctors": docs, "existing_doctor": bool(prior), "count": len(docs)}
    if name == "covid_screening":
        problem = check_screening_values(args) or values_come_from_patient(args, user_text)
        if problem:   # AI guessed or used placeholders -> make it ask the patient instead
            return {"error": problem + " Ask the patient for the missing value(s). Do not guess."}
        try:   # same model the /predict page uses (needs artifacts/model.pkl from the training pipeline)
            from src.pipeline.predict_pipeline import CustomData, PredictPipeline
            fever = float(args["fever"])
            if 34 <= fever <= 43:                      # patient gave Celsius -> convert to Fahrenheit
                fever = round(fever * 9 / 5 + 32, 1)
            df = CustomData(int(args["age"]), args["gender"], fever, args["cough"],
                            str(args["city"]).strip().title()).get_data_as_dataframe()
            result, prob = PredictPipeline().predict(df)
            try:   # keep a record for the patient's profile page
                crud.save_screening(user_id, int(args["age"]), args["gender"], fever, args["cough"],
                                    str(args["city"]).strip().title(), result, float(prob), "chat")
            except Exception:
                pass
            return {"screening_result": "higher COVID risk" if result == "Positive" else "lower COVID risk",
                    "estimate_percent": float(prob), "note": "rough estimate from a small demo model, not a diagnosis"}
        except Exception as e:
            return {"error": f"screening unavailable: {e}"}
    if name == "get_my_appointments":
        return {"appointments": crud.get_user_appointments(user_id)}
    return {"error": "unknown tool"}