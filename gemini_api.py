# gemini_api.py
import os
import requests

def fallback_summarizer(prompt, max_length=100, min_length=50, do_sample=False):
    """
    Dummy fallback summarizer function.
    Replace this with your actual fallback summarization logic if needed.
    """
    # For demonstration purposes, we simply return a placeholder summary.
    return [{"summary_text": f"[Fallback summary for prompt: {prompt}]"}]

class GeminiAPI:
    @staticmethod
    def summarize_text(prompt: str, max_length: int = 100, min_length: int = 50, do_sample: bool = False) -> str:
        """
        Summarize the given prompt text using the Gemini API if available;
        otherwise, fall back to the alternative summarizer.
        The output is trimmed to at most 2 sentences.
        """
        gemini_api_url = os.getenv("GEMINI_API_URL", "")
        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        used_method = ""
        summary = ""

        if gemini_api_url and gemini_api_key:
            url = f"{gemini_api_url}?key={gemini_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            try:
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
                else:
                    print(f"Gemini API error {response.status_code}: {response.text}")
                    summary = fallback_summarizer(prompt, max_length, min_length, do_sample)[0]["summary_text"]
                    used_method = "Fallback (Gemini error)"
            except Exception as e:
                print(f"Exception calling Gemini API: {e}")
                summary = fallback_summarizer(prompt, max_length, min_length, do_sample)[0]["summary_text"]
                used_method = "Fallback (Gemini exception)"
        else:
            summary = fallback_summarizer(prompt, max_length, min_length, do_sample)[0]["summary_text"]
            used_method = "Fallback (No Gemini config)"

        # Trim the summary to at most 2 sentences
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        if len(sentences) > 2:
            summary_out = '. '.join(sentences[:2]) + '.'
        else:
            summary_out = '. '.join(sentences) + '.'

        return summary_out + f" (Summary generated using: {used_method})"
