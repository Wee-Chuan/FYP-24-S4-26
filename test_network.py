# test_network.py

import os
import pandas as pd
import random
from datetime import datetime, timedelta
from entity.network import readDataAndInitialise, users
from entity.ai_summary import generate_structured_summary

def generate_comment_data():
    """
    Generates a fresh `commentData.csv` with random usernames, comments, and engagements.
    """
    # Define sample usernames, comments, and posts
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

    # Generate random timestamps for the last 30 days
    start_date = datetime.now() - timedelta(days=30)
    timestamps = [(start_date + timedelta(days=random.randint(0, 30))).isoformat() for _ in range(20)]

    # Create a dataset with random values
    data = {
        "id": [random.randint(10000000000000000, 99999999999999999) for _ in range(20)],
        "likesCount": [random.randint(0, 100) for _ in range(20)],
        "ownerUsername": [random.choice(usernames) for _ in range(20)],
        "postUrl": [random.choice(post_urls) for _ in range(20)],
        "repliesCount": [random.randint(0, 10) for _ in range(20)],
        "text": [random.choice(sample_comments) for _ in range(20)],
        "timestamp": timestamps
    }

    # Save CSV
    df_simulated = pd.DataFrame(data)
    os.makedirs("./data", exist_ok=True)
    df_simulated.to_csv("./data/commentData.csv", index=False)

    print(f"✅ New `commentData.csv` generated at: ./data/commentData.csv")

def main():
    # 🔄 Generate a new dataset before running the test
    generate_comment_data()

    # Path to the dynamically generated commentData.csv file
    test_csv_path = "./data/commentData.csv"

    # Verify if the CSV file now exists
    if not os.path.exists(test_csv_path):
        print(f"❌ Error: The CSV file does not exist at {test_csv_path}")
        return

    # ✅ Load data using `network.py`
    print("🔄 Initializing data from CSV...")
    readDataAndInitialise(test_csv_path)

    # ✅ Generate the AI summary with structured insights
    print("🔄 Generating AI summary...")
    structured_summary = generate_structured_summary(users)

    # ✅ Print the structured AI summary (5-10 sentences)
    print("\n📌 Structured AI Summary:")
    print(structured_summary)

if __name__ == "__main__":
    main()
