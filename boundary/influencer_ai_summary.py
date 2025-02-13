import os
import time
import requests
import torch
from collections import Counter
from transformers import pipeline
import logging

# boundary/influencer_ai_summary.py
from gemini_api import GeminiAPI


# Set up logging for debugging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the fallback summarization pipeline (Facebook BART model)
device = "cuda" if torch.cuda.is_available() else "cpu"
fallback_summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=0 if torch.cuda.is_available() else -1
)

# Constants for prompt construction.
MAX_PROMPT_LENGTH = 1000  # Maximum number of characters to include in the prompt.
DEFAULT_PROMPT_TEMPLATE = (
    "Based on the following detailed data insights derived from your visualizations, "
    "provide a comprehensive overall summary with key comparisons and actionable recommendations in fewer than 20 sentences: {}"
)

def build_recommendation(pos_pct, neg_pct, total_comments):
    """
    Create a recommendation based on the sentiment distribution and overall engagement.
    """
    if total_comments == 0:
        return "Insufficient data to generate recommendations."
    if neg_pct > pos_pct:
        return ("The data suggests that negative sentiment is relatively high compared to positive feedback. "
                "It is recommended to review the content strategy, address user concerns, and implement targeted improvements "
                "to enhance user satisfaction.")
    else:
        return ("The overall positive sentiment is promising; however, there is room for improvement. "
                "Consider expanding interactive content and addressing neutral feedback with more engaging, personalized content.")

def build_insights_prompt(users):
    """
    Aggregates detailed insights from the comment data.
    Returns a structured text string that includes:
      - Total comment count,
      - Top active users with comment counts,
      - Most engaged posts with like counts,
      - Detailed sentiment distribution (raw counts and percentages),
      - Key discussion trends (top comment texts, truncated for brevity),
      - A tailored recommendation.
    """
    post_engagement = {}   # {post_url: {"likes": total_likes, "comments": [Comment objects]}}
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

    insights.append(f"Total comments in the dataset: {total_comments}.")

    if user_engagement:
        top_users_data = user_engagement.most_common(3)
        top_users_str = ", ".join([f"{user} ({count} comments)" for user, count in top_users_data])
        insights.append("Top active users: " + top_users_str + ".")
    else:
        insights.append("No significant user activity detected.")

    if post_engagement:
        top_posts_data = sorted(post_engagement.items(), key=lambda x: x[1]['likes'], reverse=True)[:3]
        top_posts_str = ", ".join([f"{post} ({data['likes']} likes)" for post, data in top_posts_data])
        insights.append("Most engaged posts: " + top_posts_str + ".")
    else:
        insights.append("No posts with significant engagement.")

    if total_comments > 0:
        pos = sentiment_counts.get("Positive", 0)
        neu = sentiment_counts.get("Neutral", 0)
        neg = sentiment_counts.get("Negative", 0)
        pos_pct = round((pos / total_comments) * 100, 1)
        neu_pct = round((neu / total_comments) * 100, 1)
        neg_pct = round((neg / total_comments) * 100, 1)
        insights.append(
            f"Sentiment breakdown: {pos} positive ({pos_pct}%), {neu} neutral ({neu_pct}%), and {neg} negative ({neg_pct}%)."
        )
    else:
        insights.append("No sentiment data available.")

    all_comments = [comment for post, data in post_engagement.items() for comment in data["comments"]]
    if all_comments:
        # Use top 3 comment texts based on a 'likes' attribute if available.
        discussion_trends = sorted(
            all_comments,
            key=lambda x: getattr(x, 'likes', 0),
            reverse=True
        )[:3]
        trends = "; ".join([ (c.text if len(c.text) <= 100 else c.text[:97] + "...") for c in discussion_trends ])
        insights.append("Discussion trends: " + trends + ".")
    else:
        insights.append("No key discussion trends identified.")

    # Build recommendation based on sentiment percentages.
    recommendation = build_recommendation(pos_pct if total_comments > 0 else 0,
                                          neg_pct if total_comments > 0 else 0,
                                          total_comments)
    insights.append("Recommendation: " + recommendation)

    structured_text = " ".join(insights)
    return structured_text

class AISummaryGenerator:
    @staticmethod
    def generate_ai_summary(text):
        """
        Generates a structured summary (fewer than 20 sentences) using the Gemini API.
        Falls back to Hugging Face summarization if necessary.
        """
        try:
            processed_text = " ".join(text.split())[:MAX_PROMPT_LENGTH]
            prompt = DEFAULT_PROMPT_TEMPLATE.format(processed_text)

            gemini_api_url = os.getenv("GEMINI_API_URL")
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            summary = ""
            used_method = ""

            if gemini_api_url and gemini_api_key:
                url = f"{gemini_api_url}?key={gemini_api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ]
                }
                logger.info("Sending request to Gemini API with prompt: %s", prompt)
                time.sleep(5)  # Delay to mitigate rate limit issues
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                except requests.RequestException as e:
                    logger.error("Request to Gemini API failed: %s", e)
                    response = None

                if response and response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and isinstance(parts, list) and "text" in parts[0]:
                                summary = parts[0]["text"].strip()
                            else:
                                summary = ""
                        else:
                            summary = data.get("summary", "").strip()
                    used_method = "Gemini API"
                elif response and response.status_code == 429:
                    logger.warning("Gemini API rate limit exceeded.")
                    summary = "Rate limit exceeded. Please try again later."
                    used_method = "Gemini API Error"
                else:
                    logger.warning("Gemini API error: %s", response.status_code if response else "No response")
                    try:
                        result = fallback_summarizer(prompt, max_length=300, min_length=100, do_sample=False)
                        summary = result[0]["summary_text"].strip()
                        used_method = "Hugging Face Summarization"
                    except Exception as e:
                        logger.error("Hugging Face summarization error: %s", e)
                        summary = "No AI summary available due to insufficient data."
                        used_method = "Hugging Face Error"
            else:
                logger.info("Gemini API credentials not provided; using Hugging Face summarizer.")
                try:
                    result = fallback_summarizer(prompt, max_length=300, min_length=100, do_sample=False)
                    summary = result[0]["summary_text"].strip()
                    used_method = "Hugging Face Summarization"
                except Exception as e:
                    logger.error("Hugging Face summarization error: %s", e)
                    summary = "No AI summary available due to insufficient data."
                    used_method = "Hugging Face Error"

            if not summary.strip():
                summary = "No AI summary available due to insufficient data."

            # Limit the final summary to fewer than 20 sentences.
            sentences = summary.split(". ")
            if len(sentences) > 20:
                summary = ". ".join(sentences[:20]) + "."
            elif not summary.endswith("."):
                summary += "."

            return summary + f" (Summary generated using: {used_method})"
        except Exception as e:
            logger.error("Error generating AI summary: %s", e)
            return "⚠️ AI Summary not available."

def generate_structured_summary(users):
    """
    Aggregates detailed insights from the comment data (which powers network.html visualizations)
    and returns a comprehensive AI summary that compares the visualized metrics and provides actionable recommendations.
    The final summary is limited to fewer than 20 sentences.
    """
    insights_text = build_insights_prompt(users)
    logger.info("DEBUG: Aggregated structured text: %s", insights_text)
    return AISummaryGenerator.generate_ai_summary(insights_text)

def process_ai_summary(text: str) -> str:
    """
    Generate and return an AI summary for the provided text using the Gemini API.
    """
    # Customize the prompt as needed. Here we're simply passing the text.
    return GeminiAPI.summarize_text(text)

