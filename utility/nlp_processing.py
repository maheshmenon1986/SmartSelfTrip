import json
import os
import numpy as np
import streamlit as st

# Define BASE_DIR once at the top
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path for your page icon
image_path = os.path.join(BASE_DIR, "images", "technology.png")

# Set Streamlit page configuration (must be called once, at the very top)
st.set_page_config(
    layout="wide",
    page_title="Smart2SelfTrip",
    page_icon=image_path # Set the page icon to the path of your image
)

# Define other paths relative to BASE_DIR
MODEL_PATH = os.path.join(BASE_DIR, "local_models", "paraphrase-MiniLM-L3-v2")
INTENT_PATH = os.path.join(BASE_DIR, "intent_list.json")

@st.cache_resource(show_spinner="Getting ready to explore...Your UI is getting loaded")
def load_nlp_resources():

    # Move heavy imports here, so spinner shows immediately
    from sentence_transformers import SentenceTransformer, util

    print(f"DEBUG: Starting load_nlp_resources - Model path: {MODEL_PATH}")
    try:
        model = SentenceTransformer(MODEL_PATH)
        print("DEBUG: SentenceTransformer model loaded.")

        with open(INTENT_PATH, "r", encoding="utf-8") as f:
            intent_data = json.load(f)["intents"]
        print("DEBUG: Intent data loaded.")

        intent_examples = []
        intent_mapping = []
        for intent_name, intent_info in intent_data.items():
            samples = intent_info.get("samples", [])
            for sample in samples:
                intent_examples.append(sample)
                intent_mapping.append(intent_name)
        print(f"DEBUG: Prepared {len(intent_examples)} intent examples.")

        intent_embeddings = model.encode(intent_examples, convert_to_tensor=True)
        print("DEBUG: Intent embeddings precomputed.")

        # Return util as well so interpret_intent can access it
        return model, intent_embeddings, intent_mapping, util

    except Exception as e:
        print(f"ERROR: Failed to load NLP resources: {e}")
        st.error(f"Failed to load AI components. Demo fallback activated. Error: {e}")

        class FallbackModel:
            def encode(self, text, convert_to_tensor=True):
                return np.zeros(384)

        class FallbackClassifier:
            def interpret(self, text):
                text_lower = text.lower().strip()
                if "plan" in text_lower or "trip" in text_lower or "itinerary" in text_lower:
                    return "plan_trip", 0.95
                elif "place" in text_lower or "attraction" in text_lower or "explore" in text_lower:
                    return "find_places", 0.90
                elif text_lower == "yes":
                    return "confirm_action", 0.99
                elif text_lower == "no":
                    return "cancel_action", 0.99
                return "fallback", 0.5

        return FallbackClassifier(), None, None, None

# Call cached function once globally
model, intent_embeddings, intent_mapping, util = load_nlp_resources()

CONFIDENCE_THRESHOLD = 0.6

def interpret_intent(user_input):
    if intent_mapping is None or model is None or util is None:
        # fallback classifier
        return model.interpret(user_input)

    input_embedding = model.encode(user_input, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(input_embedding, intent_embeddings)[0]

    top_result = np.argmax(cosine_scores.cpu().numpy())
    confidence = float(cosine_scores[top_result])

    if confidence < CONFIDENCE_THRESHOLD:
        return "fallback", confidence

    matched_intent = intent_mapping[top_result]
    return matched_intent, confidence
