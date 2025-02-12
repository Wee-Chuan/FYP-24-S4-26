import os
import pandas as pd
import random
from datetime import datetime, timedelta
from entity.network import readDataAndInitialise, users, generateGraphs
from entity.ai_summary import generate_structured_summary
import matplotlib
matplotlib.use('Agg')

def generate_comment_data():
    """
    Generates a fresh 'commentData.csv' with random usernames, comments, and engagements.
    In your production environment, this CSV is created by your commentdata.py process.
    This function is provided here only for testing purposes.
    """
    usernames = ["userA", "userB", "userC", "userD", "userE"]
    sample_comments = [
        "This is an amazing post! Love the visuals.",
        "Not really my favorite content, could be better.",
        "Absolutely fantastic work, keep it up!",
        "Boring, expected more engagement.",
        "This is great, very inspiring!",
        "I don't agree with this at all.",
        "Super informative and helpful.",
        "Could have been more detailed.",
        "Excellent post, very well explained.",
        "Meh, nothing special about this."
    ]
    post_urls = [
        "https://www.instagram.com/p/C4imhM1uwTP/",
        "https://www.instagram.com/p/C3fghI8jyZT/",
        "https://www.instagram.com/p/C2abcD1efGH/"
    ]
    start_date = datetime.now() - timedelta(days=30)
    timestamps = [(start_date + timedelta(days=random.randint(0, 30))).isoformat() for _ in range(20)]
    data = {
        "id": [random.randint(10000000000000000, 99999999999999999) for _ in range(20)],
        "likesCount": [random.randint(0, 100) for _ in range(20)],
        "ownerUsername": [random.choice(usernames) for _ in range(20)],
        "postUrl": [random.choice(post_urls) for _ in range(20)],
        "repliesCount": [random.randint(0, 10) for _ in range(20)],
        "text": [random.choice(sample_comments) for _ in range(20)],
        "timestamp": timestamps
    }
    df_simulated = pd.DataFrame(data)
    os.makedirs("./data", exist_ok=True)
    df_simulated.to_csv("./data/commentData.csv", index=False)
    print("✅ New 'commentData.csv' generated at: ./data/commentData.csv")

def main():
    # For testing, generate simulated data (in production, this comes from your commentdata.py)
    generate_comment_data()

    test_csv_path = "./data/commentData.csv"
    summary_path = "./data/cached_ai_summary.txt"
    username = "test_user"  # In production, this is provided by the user after fetching data via Apify API

    # Check if the CSV file exists
    if not os.path.exists(test_csv_path):
        print(f"❌ Error: The CSV file does not exist at {test_csv_path}")
        return

    # Initialize the user data from commentData.csv (populating the 'users' dictionary)
    print("🔄 Initializing data from CSV...")
    readDataAndInitialise(test_csv_path)

    # Process the data and generate visualizations via entity/network.py
    print("🔄 Running generateGraphs() to process comment data...")
    generateGraphs(username)

    # Ensure valid user data exists before generating AI summary
    if not users:
        print("❌ No user data found. AI summary will not be generated.")
        return

    # Use cached AI summary if available; otherwise, generate a new one.
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

    # Print the overall AI summary (this would be shown at the bottom of your website)
    print("\n📌 AI-Generated Summary:")
    print(ai_summary)

if __name__ == "__main__":
    main()
