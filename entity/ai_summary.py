import os
import time
import requests
import torch
import logging
from collections import Counter
from transformers import pipeline

# Set up logging for debugging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the fallback summarization pipeline (Facebook BART model).
device = "cuda" if torch.cuda.is_available() else "cpu"
fallback_summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=0 if torch.cuda.is_available() else -1
)

# Constants for prompt construction.
MAX_PROMPT_LENGTH = 1500  # Maximum characters for AI prompt.
DEFAULT_PROMPT_TEMPLATE = (
    "Based on the following sentiment analysis and engagement insights, "
    "provide a structured, concise summary with key comparisons and recommendations (max 20 sentences): {}"
)


def build_recommendation(pos_pct, neg_pct, total_comments):
    """Dynamically generates recommendations based on sentiment analysis."""
    if total_comments == 0:
        return "Insufficient data to generate recommendations."

    if neg_pct > pos_pct:
        return (
            "There is a relatively high level of negative sentiment compared to positive feedback. "
            "It is recommended to analyze critical concerns, adjust engagement strategies, "
            "and proactively address key issues in future interactions."
        )
    else:
        return (
            "Positive sentiment is dominant, indicating strong engagement. "
            "Consider experimenting with personalized content strategies to sustain audience growth."
        )


def build_insights_prompt(users):
    """Aggregates structured insights from user comments, sentiment analysis, and engagement data."""
    post_engagement = {}  # {post_url: {"likes": total_likes, "comments": [Comment objects]}}
    user_engagement = Counter()  # {username: total comments}
    sentiment_counts = Counter()  # {"Positive": X, "Negative": Y, "Neutral": Z}

    for user in users.values():
        user_engagement[user.username] += len(user.comments)
        for comment in user.comments:
            sentiment_counts[comment.sentiment] += 1
            post_url = getattr(comment, "postUrl", None)
            if post_url:
                if post_url not in post_engagement:
                    post_engagement[post_url] = {"likes": 0, "comments": []}
                post_engagement[post_url]["likes"] += comment.likes
                post_engagement[post_url]["comments"].append(comment)

    total_comments = sum(sentiment_counts.values())
    insights = []

    insights.append(f"Total comments analyzed: {total_comments}.")

    # Top active users
    if user_engagement:
        top_users = user_engagement.most_common(3)
        insights.append("Top users: " + ", ".join([f"{user} ({count} comments)" for user, count in top_users]) + ".")
    else:
        insights.append("No significant user activity detected.")

    # Most engaged posts
    if post_engagement:
        top_posts = sorted(post_engagement.items(), key=lambda x: x[1]['likes'], reverse=True)[:3]
        insights.append("Top engaging posts: " + ", ".join([f"{post} ({data['likes']} likes)" for post, data in top_posts]) + ".")
    else:
        insights.append("No major engagement on posts.")

    # Sentiment breakdown
    if total_comments > 0:
        pos, neu, neg = sentiment_counts["Positive"], sentiment_counts["Neutral"], sentiment_counts["Negative"]
        pos_pct, neu_pct, neg_pct = (pos / total_comments) * 100, (neu / total_comments) * 100, (neg / total_comments) * 100
        insights.append(
            f"Sentiment Analysis: {pos} positive ({pos_pct:.1f}%), {neu} neutral ({neu_pct:.1f}%), {neg} negative ({neg_pct:.1f}%) comments."
        )
    else:
        insights.append("No sentiment data available.")

    # Tailored Recommendations
    if total_comments > 0:
        insights.append("Recommendations: " + build_recommendation(pos_pct, neg_pct, total_comments))
    else:
        insights.append("No recommendations due to insufficient data.")

    return " ".join(insights)


class AISummaryGenerator:
    @staticmethod
    def generate_ai_summary(text):
        """
        Generates an AI-powered summary using Gemini API or a fallback model.
        """
        try:
            processed_text = " ".join(text.split())[:MAX_PROMPT_LENGTH]
            prompt = DEFAULT_PROMPT_TEMPLATE.format(processed_text)

            gemini_api_url = os.getenv("GEMINI_API_URL")
            gemini_api_key = os.getenv("GEMINI_API_KEY")

            summary, used_method = "", ""

            if gemini_api_url and gemini_api_key:
                url = f"{gemini_api_url}?key={gemini_api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                logger.info("Requesting Gemini API summary...")

                time.sleep(5)  # Small delay to prevent API rate limits
                response = requests.post(url, headers=headers, json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and isinstance(parts, list) and "text" in parts[0]:
                                summary = parts[0]["text"].strip()
                            else:
                                summary = "No summary generated."
                        else:
                            summary = "No summary available."
                    used_method = "Gemini API"
                else:
                    logger.warning(f"Gemini API failed with status code {response.status_code}. Falling back to local summarization.")
                    used_method = "Gemini API Error"

            if not summary.strip():
                logger.info("Using local summarization model...")
                summary = fallback_summarizer(prompt, max_length=300, min_length=100, do_sample=False)[0]["summary_text"]
                used_method = "Hugging Face Summarization"

            if not summary.endswith("."):
                summary += "."

            return summary + f" (Summary generated using: {used_method})"

        except Exception as e:
            logger.error("AI summary generation failed: %s", e)
            return "⚠️ AI Summary unavailable."


def generate_structured_summary(users):
    """
    Generates an AI-powered structured summary based on engagement insights and visualizations.
    """
    insights_text = build_insights_prompt(users)
    logger.info("DEBUG: Aggregated structured text: %s", insights_text)
    return AISummaryGenerator.generate_ai_summary(insights_text)
