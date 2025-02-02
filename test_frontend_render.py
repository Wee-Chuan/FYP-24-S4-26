import unittest
from flask import Flask
from flask.testing import FlaskClient
from boundary.influencer_boundary import influencer_boundary  # Ensure this matches your project structure

class TestFrontendRendering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize Flask test client"""
        cls.app = Flask(__name__)
        cls.app.register_blueprint(influencer_boundary)
        cls.client = cls.app.test_client()

    def test_engagement_page_loads(self):
        """Ensure engagement.html loads successfully via Flask route."""
        response = self.client.get("/dashboard/influencer/engagement")  # ✅ Corrected route
        self.assertEqual(response.status_code, 200, f"❌ Engagement page did not load! Response: {response.status_code}")

    def test_engagement_page_contains_chart(self):
        """Check if engagement.html contains the Chart.js canvas."""
        response = self.client.get("/dashboard/influencer/engagement")  # ✅ Corrected route
        html_content = response.data.decode('utf-8')

        self.assertIn('<canvas id="engagementChart">', html_content, "❌ Engagement chart not found in HTML!")

if __name__ == "__main__":
    unittest.main()
