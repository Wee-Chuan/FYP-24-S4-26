import os
from entity.network import readDataAndInitialise, users, generateGraphs
from entity.ai_summary import generate_structured_summary
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import builtins

# Save the original open function
original_open = builtins.open

def patched_open(filename, mode='r', *args, **kwargs):
    # If the file is the CSV we use for testing and is being opened for reading,
    # inject encoding="utf-8" and errors="ignore"
    if filename.endswith("commentData.csv") and mode.startswith('r'):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "ignore")
    return original_open(filename, mode, *args, **kwargs)

# Patch the built-in open function
builtins.open = patched_open

def main():
    # Path to the actual comment data file.
    test_csv_path = "./data/commentData.csv"
    summary_path = "./data/cached_ai_summary.txt"
    username = "test_user"  # This would be provided by the user in production

    # Check if the CSV file exists
    if not os.path.exists(test_csv_path):
        print(f"❌ Error: The CSV file does not exist at {test_csv_path}.")
        print("Please generate commentData.csv first (e.g., via your production process).")
        return

    # Initialize data from CSV
    print("🔄 Initializing data from CSV...")
    readDataAndInitialise(test_csv_path)

    # Process the data and generate visualizations
    print("🔄 Running generateGraphs() to process comment data...")
    generateGraphs(username)

    # Ensure valid user data exists
    if not users:
        print("❌ No user data found. AI summary will not be generated.")
        return

    # Use cached AI summary if it exists; otherwise, generate a new one.
    if os.path.exists(summary_path):
        print("\n📌 Using Cached AI Summary...")
        with open(summary_path, "r") as file:
            ai_summary = file.read()
    else:
        print("🔄 Generating AI summary...")
        ai_summary = generate_structured_summary(users)
        if ai_summary is None or not ai_summary.strip():
            ai_summary = "No AI summary available due to insufficient data."
        with open(summary_path, "w") as file:
            file.write(ai_summary)

    # Print the AI-generated summary (to be displayed on your website)
    print("\n📌 AI-Generated Summary:")
    print(ai_summary)

if __name__ == "__main__":
    main()
