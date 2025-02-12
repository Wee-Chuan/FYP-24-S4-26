import os
import time
import json
import requests
import builtins

# === Patch built-in open for testing only ===
original_open = builtins.open
def patched_open(filename, mode='r', *args, **kwargs):
    # If the file being opened is commentData.csv (for reading), use utf-8 encoding with errors ignored.
    if filename.endswith("commentData.csv") and mode.startswith('r'):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "ignore")
    return original_open(filename, mode, *args, **kwargs)
builtins.open = patched_open
# === End Patch ===

# Configuration
BASE_URL = "http://localhost:5000"  # Your Flask server address
USERNAME = "test_user"              # Username for testing
CSV_PATH = "./data/commentData.csv" # Actual CSV file produced by your process
SUMMARY_CACHE = "./data/cached_ai_summary.txt"

# ---------------- Part 1: API Test ---------------- #
def test_api_endpoint():
    """
    Calls the /display_network endpoint of your API.
    This endpoint is expected to:
      - Generate/update commentData.csv,
      - Process the comment data,
      - Generate visualizations and an overall AI summary,
      - Return a JSON response containing the username and AI summary.
    """
    url = f"{BASE_URL}/display_network"
    data = {"username": USERNAME}
    print("=== Testing API Endpoint /display_network ===")
    try:
        response = requests.post(url, data=data, timeout=60)
    except Exception as e:
        print("Error making API request:", e)
        return None

    print("Status Code:", response.status_code)
    try:
        api_response = response.json()
        print("API Response:")
        print(json.dumps(api_response, indent=4))
        return api_response
    except Exception as e:
        print("Error parsing API response:", e)
        print("Response Text:", response.text)
        return None

# ---------------- Part 2: Local Processing Test ---------------- #
def test_local_processing():
    """
    Uses local functions from network.py and ai_summary.py to process the
    actual CSV file, generate visualizations, and produce an AI summary.
    """
    from entity.network import readDataAndInitialise, users, generateGraphs
    from entity.ai_summary import generate_structured_summary

    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: The CSV file does not exist at {CSV_PATH}.")
        return None

    print("🔄 Initializing data from CSV (local processing)...")
    readDataAndInitialise(CSV_PATH)

    print("🔄 Running generateGraphs() to process comment data locally...")
    generateGraphs(USERNAME)

    if not users:
        print("❌ No user data found locally. AI summary will not be generated.")
        return None

    if os.path.exists(SUMMARY_CACHE):
        print("\n📌 Using Cached AI Summary (local processing)...")
        with open(SUMMARY_CACHE, "r") as f:
            local_summary = f.read()
    else:
        print("🔄 Generating AI summary locally...")
        local_summary = generate_structured_summary(users)
        if not local_summary or not local_summary.strip():
            local_summary = "No AI summary available due to insufficient data."
        with open(SUMMARY_CACHE, "w") as f:
            f.write(local_summary)

    print("\n📌 Locally Generated AI Summary:")
    print(local_summary)
    return local_summary

# ---------------- Main ---------------- #
def main():
    print("========== PART 1: Testing API Endpoint ==========")
    api_result = test_api_endpoint()
    if api_result is None:
        print("API test failed. Ensure your Flask server is running at", BASE_URL)
    else:
        print("API test completed.\n")
    
    print("Waiting for CSV file to settle on disk...")
    time.sleep(5)
    
    print("\n========== PART 2: Testing Local Processing ==========")
    local_summary = test_local_processing()

if __name__ == "__main__":
    main()
