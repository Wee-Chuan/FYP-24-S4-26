# influencer_ai_summary.py

import os
import csv
import entity.network as nw
from ai_summary import generate_structured_summary

def process_ai_summary(username):
    """
    Processes AI-generated insights for influencer network visualization.
    - Reads processed comment data.
    - Generates AI summary.
    - Saves summary to a file.
    - Returns summary text.
    """
    try:
        # Ensure data exists before summarization
        data_path = "data/commentData.csv"
        if not os.path.exists(data_path):
            print("❌ Error: commentData.csv not found.")
            return "No data available for summarization."

        # Read data and initialize users
        nw.readDataAndInitialise(data_path)

        # ✅ Generate AI Summary
        ai_summary = generate_structured_summary(nw.users)

        # ✅ Save AI Summary to a file
        summary_path = f"data/ai_summary_{username}.txt"
        with open(summary_path, "w") as file:
            file.write(ai_summary)
        print(f"✅ AI Summary saved at: {summary_path}")

        return ai_summary

    except Exception as e:
        print(f"Error processing AI summary: {e}")
        return "Error generating AI insights."
