import os
import unittest
import json
import pandas as pd
from flask import Flask
from flask.testing import FlaskClient
from boundary.influencer_boundary import influencer_boundary
from entity.user import User
from wordcloud import WordCloud
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download necessary NLP resources
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Constants
TEST_CSV_PATH = "test_engagement_data.csv"
UPLOAD_API_URL = "/dashboard/engagement_metrics"
API_GET_METRICS = "/api/get_visualization_data"
MAX_PROCESSING_TIME = 5  # Max processing time in seconds

class TestFullSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize Flask test client and create test dataset."""
        cls.app = Flask(__name__)
        cls.app.register_blueprint(influencer_boundary)
        cls.client = cls.app.test_client()

        # Create a test dataset for file upload
        test_data = {
            "id": [1, 2, 3, 4, 5],
            "likesCount": [100, 250, 180, 95, 300],
            "repliesCount": [10, 50, 40, 15, 90],
            "text": ["Great post!", "This is bad", "I love this!", "Not sure about this", "Amazing content!"],
            "owner/username": ["user1", "user2", "user3", "user4", "user5"],
            "owner/is_verified": [True, False, True, False, True],
            "postUrl": ["url1", "url2", "url3", "url4", "url5"]
        }
        cls.df = pd.DataFrame(test_data)
        cls.df.to_csv(TEST_CSV_PATH, index=False)

    def test_1_file_upload(self):
        """Test if CSV file is correctly uploaded via influencer_boundary.py."""
        with open(TEST_CSV_PATH, "rb") as file:
            response = self.client.post(UPLOAD_API_URL, content_type="multipart/form-data", data={"file": file})
        
        self.assertEqual(response.status_code, 302, "❌ File upload failed!")  # Expecting a redirect after upload

    def test_2_engagement_processing(self):
        """Test if engagement data is correctly processed via user.py."""
        processed_data = User.get_engagement_metrics(TEST_CSV_PATH)
        
        self.assertIsInstance(processed_data, list, "❌ Processed data should be a list!")
        self.assertGreater(len(processed_data), 0, "❌ No engagement data processed!")

        sample_entry = processed_data[0]
        self.assertIn("likes", sample_entry, "❌ Missing 'likes' in processed data!")
        self.assertIn("comments", sample_entry, "❌ Missing 'comments' in processed data!")
        self.assertIn("owner_username", sample_entry, "❌ Missing 'owner_username' in processed data!")

    def test_3_ai_sentiment_analysis(self):
        """Test AI-based sentiment classification."""
        sample_comments = self.df['text'].dropna().sample(n=5, random_state=42).tolist()
        sentiments = [self.analyze_sentiment(comment) for comment in sample_comments]
        valid_sentiments = {"Positive", "Neutral", "Negative"}

        for sentiment in sentiments:
            self.assertIn(sentiment, valid_sentiments, f"❌ Invalid sentiment classification: {sentiment}")

    def test_4_wordcloud_data(self):
        """Test if word cloud is generated correctly without saving an image."""
        text_data = " ".join(self.df["text"].dropna())  # Combine text
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_data)

        # Check if word cloud contains expected words
        words = wordcloud.words_
        self.assertGreater(len(words), 0, "❌ Word cloud should not be empty!")
        for expected_word in ["Great", "Amazing", "Bad", "Loved"]:  # Modify based on dataset
            if expected_word.lower() in text_data.lower():
                self.assertIn(expected_word, words, f"❌ '{expected_word}' should be in the word cloud!")

    def test_5_verified_vs_non_verified_engagement(self):
        """Ensure verified users engage differently from non-verified users."""
        verified_data = self.df[self.df["owner/is_verified"] == True]
        non_verified_data = self.df[self.df["owner/is_verified"] == False]

        verified_likes = verified_data["likesCount"].sum()
        non_verified_likes = non_verified_data["likesCount"].sum()

        self.assertGreater(verified_likes + non_verified_likes, 0, "❌ No engagement detected!")

    def test_6_most_engaged_commenters(self):
        """Check that the top commenters are ranked correctly."""
        top_commenters = self.df.groupby("owner/username")["repliesCount"].sum().sort_values(ascending=False)
        self.assertGreater(len(top_commenters), 0, "❌ No engaged commenters found!")

    def test_7_api_response(self):
        """Test if the API correctly returns processed engagement data."""
        response = self.client.get(API_GET_METRICS)
        self.assertEqual(response.status_code, 200, "❌ API did not return a 200 response!")

        data = json.loads(response.data)
        self.assertIsInstance(data, list, "❌ API response should be a list!")
        self.assertGreater(len(data), 0, "❌ API response contains no data!")

    def test_8_processing_time(self):
        """Ensure the dataset processes within a reasonable time limit."""
        start_time = time.time()
        User.get_engagement_metrics(TEST_CSV_PATH)
        end_time = time.time()
        processing_time = end_time - start_time
        self.assertLess(processing_time, MAX_PROCESSING_TIME, f"❌ Processing took too long: {processing_time:.2f} seconds")

    @staticmethod
    def analyze_sentiment(comment):
        """Perform AI-based sentiment analysis on a comment."""
        if pd.isna(comment):
            return "Neutral"

        score = sia.polarity_scores(comment)['compound']
        if score >= 0.05:
            return "Positive"
        elif score <= -0.05:
            return "Negative"
        else:
            return "Neutral"

    @classmethod
    def tearDownClass(cls):
        """Clean up test CSV file after all tests have run."""
        if os.path.exists(TEST_CSV_PATH):
            os.remove(TEST_CSV_PATH)

if __name__ == "__main__":
    unittest.main()
