import os
from sentence_transformers import SentenceTransformer

# Define the absolute path to your utility directory
# os.path.dirname(__file__) will be C:\Automation\AI\reconciliationwithai\utility
utility_dir = os.path.dirname(__file__)

# Define the path where you want to save the model within the utility directory
# This will result in: C:\Automation\AI\reconciliationwithai\utility\local_models\paraphrase-MiniLM-L3-v2
local_model_path = os.path.join(utility_dir, "../local_models", "paraphrase-MiniLM-L3-v2")

# Create the directory if it doesn't exist
os.makedirs(local_model_path, exist_ok=True)

# Check if the model is already downloaded (by checking for a key file like config.json)
if not os.path.exists(os.path.join(local_model_path, "config.json")):
    print(f"Downloading model 'paraphrase-MiniLM-L3-v2' to {local_model_path}...")
    try:
        model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")
        model.save(local_model_path)
        print("Model downloaded and saved locally successfully!")
    except Exception as e:
        print(f"Error downloading or saving model: {e}")
        print("Please check your internet connection or model name.")
else:
    print(f"Model already exists at {local_model_path}, skipping download.")