from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
import os

# Define the model ID and the local path where you want to save it
repo_id = "sentence-transformers/all-MiniLM-L3-v2" # This is the target model
local_dir = r"C:\Automation\AI\Smart2SelfTrip\smart2selftrip\utility\allmini_L3_final" # Using a distinct, clear name

print(f"Attempting to download '{repo_id}' directly to {local_dir}...")

try:
    # Ensure the directory exists
    os.makedirs(local_dir, exist_ok=True)

    # Download the entire repository snapshot
    downloaded_path = snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)

    print(f"SUCCESS: Model '{repo_id}' downloaded directly to: {downloaded_path}")

    # Optional: Verify that SentenceTransformer can load it from the local path
    print(f"Verifying local load from: {downloaded_path}")
    model = SentenceTransformer(downloaded_path)
    print("SUCCESS: Model loaded locally by SentenceTransformer!")

except Exception as e:
    print(f"ERROR: Failed to download or load model directly: {e}")