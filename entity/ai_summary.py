import os
import time
import requests
import torch
from collections import Counter
from transformers import pipeline

# Initialize Hugging Face summarization pipeline (Facebook BART model)
device = "cuda" if torch.cuda.is_available() else "cpu"
fallback_summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=0 if torch.cuda.is_available() else -1
)

class AISummaryGenerator:
    @staticmethod
    def generate_ai_summary(text):
        """
        Generates a structured 5-10 sentence summary using Gemini API.
        Falls back to Hugging Face summarization if Gemini API is unavailable.
        """
        try:
            # Ensure text is within 1000 characters
            prompt = " ".join(text.split())[:1000]

            # Check if Gemini API is available
            gemini_api_url = os.getenv("GEMINI_API_URL")
            gemini_api_key = os.getenv("GEMINI_API_KEY")

            if gemini_api_url and gemini_api_key:
                url = f"{gemini_api_url}?key={gemini_api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": (
                                        "Summarize the following social media insights in 5-10 sentences. Identify: "
                                        "- Top active users, - Most engaged posts, "
                                        "- Sentiment distribution (positive, neutral, negative), "
                                        "- Key discussion trends, and - Recommendations for increasing engagement. "
                                        f"{prompt}"
                                    )
                                }
                            ]
                        }
                    ]
                }
                # Delay to reduce rate-limit issues
                time.sleep(5)
                response = requests.post(url, headers=headers, json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and isinstance(parts, list) and "text" in parts[0]:
                                summary = parts[0]["text"]
                            else:
                                summary = "No summary available."
                        else:
                            summary = data.get("summary", "No summary available.")
                    else:
                        summary = data.get("summary", "No summary available.")
                    used_method = "Gemini API"
                elif response.status_code == 429:
                    summary = "Rate limit exceeded. Try again later."
                    used_method = "Gemini API Error"
                else:
                    summary = f"Error generating summary via Gemini API: {response.status_code}"
                    used_method = "Gemini API Error"
            else:
                # Fall back to Hugging Face summarization
                try:
                    result = fallback_summarizer(prompt, max_length=250, min_length=50, do_sample=False)
                    summary = result[0]["summary_text"]
                    used_method = "Hugging Face Summarization"
                except Exception as e:
                    print(f"Hugging Face summarization error: {e}")
                    summary = "Error using Hugging Face summarizer."
                    used_method = "Hugging Face Error"

            # Fallback if the summary is empty
            if not summary.strip():
                summary = "No AI summary available due to insufficient data."

            return summary + f" (Summary generated using: {used_method})"
        
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return "⚠️ AI Summary not available."

def generate_structured_summary(users):
    """
    Generates structured insights from the actual data loaded from commentData.csv,
    and then uses the AI summarizer to produce a 5-10 sentence summary.
    """
    post_engagement = {}   # {post_url: {"likes": total_likes, "comments": [list of Comment objects]}}
    user_engagement = Counter()  # {username: total comments}
    sentiment_counts = Counter()  # {"Positive": X, "Negative": Y, "Neutral": Z}

    # Process the actual user data
    for user in users.values():
        user_engagement[user.username] += len(user.comments)
        for comment in user.comments:
            sentiment_counts[comment.sentiment] += 1
            post_url = getattr(comment, "postUrl", None)  # Assuming postUrl exists
            if post_url:
                if post_url not in post_engagement:
                    post_engagement[post_url] = {"likes": 0, "comments": []}
                post_engagement[post_url]["likes"] += comment.likes
                post_engagement[post_url]["comments"].append(comment)

    # Construct insights dynamically
    summary_parts = []

    # Top active users
    top_users = [user for user, _ in user_engagement.most_common(3)]
    if top_users:
        summary_parts.append(f"Top Active Users: {', '.join(top_users)}.")
    else:
        summary_parts.append("No significant user activity detected.")

    # Most engaged posts
    top_posts = [post for post, data in sorted(post_engagement.items(), key=lambda x: x[1]['likes'], reverse=True)[:3]]
    if top_posts:
        summary_parts.append(f"Most Engaged Posts: {', '.join(top_posts)}.")
    elif not post_engagement:
        summary_parts.append("No posts had significant engagement.")

    # Sentiment distribution
    if any(sentiment_counts.values()):
        sentiment_summary = f"Sentiment Analysis: {sentiment_counts['Positive']} Positive, {sentiment_counts['Neutral']} Neutral, {sentiment_counts['Negative']} Negative."
        summary_parts.append(sentiment_summary)
    else:
        summary_parts.append("No sentiment data available.")

    # Discussion trends based on comments (using the comment text)
    # (Assumes Comment objects have a 'text' attribute; if 'likes' is available in the comment object, use that; otherwise, default to 0)
    discussion_trends = sorted(
        [comment.text for post, data in post_engagement.items() for comment in data["comments"]],
        key=lambda x: getattr(x, 'likes', 0),
        reverse=True
    )[:3]
    if discussion_trends:
        summary_parts.append(f"Discussion Trends: {', '.join(discussion_trends)}.")
    else:
        summary_parts.append("No key discussion trends detected.")

    structured_text = " ".join(summary_parts) if summary_parts else "No significant data available."

    # Debug print to verify aggregated text
    print("DEBUG: Aggregated structured text:", structured_text)

    return AISummaryGenerator.generate_ai_summary(structured_text)
