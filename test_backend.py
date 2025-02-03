import os
import unittest
import json
import pandas as pd
import random
from flask import Flask
from flask.testing import FlaskClient
from boundary.influencer_boundary import influencer_boundary
from entity.user import User

# Constants
ENGAGEMENT_CSV_PATH = "engagement_metrics.csv"  # Use existing data
API_GET_METRICS = "/api/get_visualization_data?post_url="
NUM_TEST_POSTS = 3  # Number of posts to randomly test

class TestBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize Flask test client and ensure engagement_metrics.csv is available."""
        cls.app = Flask(__name__)
        cls.app.register_blueprint(influencer_boundary)
        cls.client = cls.app.test_client()

        if not os.path.exists(ENGAGEMENT_CSV_PATH):
            raise FileNotFoundError(f"❌ Error: {ENGAGEMENT_CSV_PATH} not found!")

        print(f"✅ Using existing {ENGAGEMENT_CSV_PATH} for testing.")

    def test_1_csv_integrity(self):
        """Test if engagement_metrics.csv is correctly structured and not empty."""
        df = pd.read_csv(ENGAGEMENT_CSV_PATH)

        # Debugging: Print available columns
        print(f"📢 Available Columns in CSV: {list(df.columns)}")

        self.assertGreater(len(df), 0, "❌ CSV file is empty!")

        # Adjusted column names (match actual CSV)
        required_columns = {"id", "likes", "comments", "text", "postUrl", "verified"}
        self.assertTrue(required_columns.issubset(df.columns), f"❌ Missing required columns: {required_columns - set(df.columns)}")

        print(f"✅ CSV Integrity Test Passed! {len(df)} rows found.")

    def test_2_random_post_analysis(self):
        """Test AI-generated summary and engagement insights for 3 random posts."""
        df = pd.read_csv(ENGAGEMENT_CSV_PATH)

        unique_posts = df["postUrl"].dropna().unique()
        if len(unique_posts) < NUM_TEST_POSTS:
            raise ValueError("Not enough posts available for random testing!")

        selected_posts = random.sample(list(unique_posts), NUM_TEST_POSTS)

        for idx, post_url in enumerate(selected_posts, start=1):
            print(f"\n🔹 **Post {idx}:** {post_url}")

            post_data = User.get_post_engagement(ENGAGEMENT_CSV_PATH, post_url)
            self.assertGreater(len(post_data), 0, f"❌ No engagement data found for post {idx}!")

            # Generate AI summary
            ai_summary = User.generate_ai_summary(post_data)

            print(f"📊 **AI Summary for Post {idx}:**\n{ai_summary}")

            # Extract most liked and least liked comments
            sorted_data = sorted(post_data, key=lambda x: x.get("likes", 0), reverse=True)  # Changed `likesCount` to `likes`
            top_3_comments = sorted_data[:3]
            bottom_3_comments = sorted_data[-3:]

            print("\n🔥 **Top 3 Most Liked Comments:**")
            for comment in top_3_comments:
                print(f"👍 {comment.get('likes', 0)} likes | 💬 {comment.get('text', 'No text')}")  # Safe `.get()` usage

            print("\n❄️ **Bottom 3 Least Liked Comments:**")
            for comment in bottom_3_comments:
                print(f"👎 {comment.get('likes', 0)} likes | 💬 {comment.get('text', 'No text')}")

        print(f"\n✅ AI Summary and Engagement Insights for {NUM_TEST_POSTS} posts tested!")

    def test_3_api_get_metrics(self):
        """Test API endpoint for retrieving engagement data for a single post."""
        df = pd.read_csv(ENGAGEMENT_CSV_PATH)
        post_url = df["postUrl"].dropna().iloc[0]  # Get the first post URL

        print(f"\n📢 **Testing API with postUrl:** {post_url}")

        response = self.client.get(API_GET_METRICS + post_url)

        print("\n📢 **API Debug - Status Code:**", response.status_code)
        print("📢 **API Debug - Response Data:**", response.data.decode("utf-8"))

        self.assertEqual(response.status_code, 200, "❌ API did not return 200 response!")

        data = json.loads(response.data)
        self.assertIsInstance(data, dict, "❌ API response should be a dictionary!")
        self.assertIn("post_data", data, "❌ Missing 'post_data' in API response!")
        self.assertIn("ai_summary", data, "❌ Missing 'ai_summary' in API response!")

        print("\n✅ API Data Retrieval Successful!")

    @classmethod
    def tearDownClass(cls):
        """Keep engagement_metrics.csv for further testing."""
        print(f"\n✅ Keeping {ENGAGEMENT_CSV_PATH} after testing as requested.")

if __name__ == "__main__":
    unittest.main()
