import requests
from bs4 import BeautifulSoup

# Configuration: adjust BASE_URL if needed.
BASE_URL = "http://localhost:5000"
NETWORK_URL = f"{BASE_URL}/network"

def test_network_page():
    try:
        # Make a GET request to the /network route.
        response = requests.get(NETWORK_URL, timeout=30)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} when requesting {NETWORK_URL}")
            return

        # Parse the HTML using BeautifulSoup.
        soup = BeautifulSoup(response.text, "html.parser")

        # Look for the AI summary section.
        ai_summary_div = soup.find("div", id="aiSummary")
        if ai_summary_div:
            summary_heading = ai_summary_div.find("h3")
            summary_text = ai_summary_div.find("p")
            print("Overall AI Summary Section Found:")
            if summary_heading:
                print("Heading:", summary_heading.get_text())
            if summary_text:
                print("Summary:", summary_text.get_text())
            else:
                print("No summary text found in the AI summary section.")
        else:
            print("Error: AI summary section not found in the HTML response.")

    except Exception as e:
        print("Error during test:", e)

if __name__ == "__main__":
    test_network_page()
