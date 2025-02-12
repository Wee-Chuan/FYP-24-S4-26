import csv
import re
import json
import plotly.graph_objects as go
import plotly.io as pio
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from entity.classes import Comment, User
import entity.admin as st

#----------------------------------------Gemini_API--------------------------------------#
from entity.ai_summary import generate_structured_summary
#----------------------------------------------------------------------------------------#


# Global variables
users = {}

# Load the model and tokenizer for sentiment analysis
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Function to get sentiment from the model
def get_sentiment(text):
    # Set max_length to 512 to match the model's max token length
    encoded_input = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True)
    output = model(**encoded_input)
    scores = softmax(output.logits.detach().numpy()[0])  # Convert logits to probabilities

    sentiments = ["Negative", "Neutral", "Positive"]
    sentiment = sentiments[scores.argmax()]  # Get the sentiment with the highest score
    return sentiment

# Preprocessing function to clean the text
def preprocess_text(text):
    # Remove mentions (e.g., @username)
    text = re.sub(r'@[\w]+', '', text)
    
    # Remove non-ASCII characters (emojis or special characters)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    return text

# Function to read data and initialize users
def readDataAndInitialise(filename):
    users.clear()
    global comments_list, comment_mapping

    with open(filename, 'r') as file:
        reader = csv.DictReader(file)

        # Remove BOM and strip any extra spaces from header names
        reader.fieldnames = [header.strip().lstrip('\ufeff') for header in reader.fieldnames]

        for row in reader:
            # Skip rows with missing critical information
            if not row["likesCount"] or not row["repliesCount"] or not row["text"] or not row["ownerUsername"]:
                continue

            # Extract data
            username = row["ownerUsername"]
            text = row["text"]
            likes = int(row["likesCount"])
            replies = int(row["repliesCount"])
            timestamp = row["timestamp"]

            # Create Comment object
            comment = Comment(text=text, likes=likes, replies=replies, timestamp = timestamp, username=username)
            sentiment = get_sentiment(text)  # Assign sentiment
            comment.sentiment = sentiment

            # Add comment to user
            if username not in users:
                users[username] = User(username=username)
            users[username].comments.append(comment)

# Function to generate the pie chart as an image
def visualize_sentiment_pie_chart():
    # Count the number of sentiments
    sentiment_counts = {"Negative": 0, "Neutral": 0, "Positive": 0}
    for username, user in users.items():
        for comment in user.comments:
            sentiment_counts[comment.sentiment] += 1

    # Prepare data for pie chart
    labels = list(sentiment_counts.keys())
    values = list(sentiment_counts.values())

    # Create the pie chart using Matplotlib
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'})

    # Equal aspect ratio ensures that pie chart is drawn as a circle
    ax.axis('equal')

    # Save the figure as an image
    plt.title("Sentiment Distribution")
    plt.savefig('data/sentiment_pie_chart.png')  # Save as PNG image
    plt.close()

from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Function to generate a word cloud for each sentiment
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def generate_word_clouds():
    sentiment_texts = {"Negative": "", "Neutral": "", "Positive": ""}

    # Collect text for each sentiment
    for username, user in users.items():
        for comment in user.comments:
            sentiment_texts[comment.sentiment] += comment.text + " "

    # Generate and save word clouds for each sentiment
    for sentiment, text in sentiment_texts.items():
        if not text.strip():  # Check if text is empty or whitespace
            print(f"No text available for {sentiment} sentiment. Generating 'NO WORDS' image.")
            
            # Generate "NO WORDS" image for empty sentiment
            wordcloud = WordCloud(width=800, height=400, background_color="white").generate("NIL")
            
            # Display the word cloud with "NO WORDS"
            plt.figure(figsize=(8, 4))
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            plt.title(f"Word Cloud for {sentiment} Sentiment - NO WORDS")
            
            # Save the "NO WORDS" word cloud image
            wordcloud_file = f"data/wordcloud_{sentiment.lower()}.png"
            plt.savefig(wordcloud_file)
            plt.close()
            
            print(f"Saved 'NO WORDS' image for {sentiment} sentiment at {wordcloud_file}")
            continue

        # Generate the word cloud for non-empty sentiment text
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
        
        # Display the word cloud
        plt.figure(figsize=(8, 4))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title(f"Word Cloud for {sentiment} Sentiment")
        
        # Save the word cloud as an image
        wordcloud_file = f"data/wordcloud_{sentiment.lower()}.png"
        plt.savefig(wordcloud_file)
        plt.close()

        print(f"Saved word cloud for {sentiment} sentiment at {wordcloud_file}")

def generate_negative_comments_html():
    comments_per_page = 5

    # Extract negative comments from users
    negative_comments = []
    seen_comments = set()  # To track unique comments

    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Negative" and comment.text not in seen_comments:
                negative_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })
                seen_comments.add(comment.text)

    # HTML content structure
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #ffebee;
                    margin: 2em;
                    color: #333;
                }}
                h1 {{
                    text-align: center;
                    color: #d32f2f;
                }}
                #noCommentsMessage {{
                    text-align: center;
                    font-size: 1.5em;
                    color: #d32f2f;
                }}
                table {{
                    width: 80%;
                    border-collapse: collapse;
                    margin: 0 auto;
                    background-color: white;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #e57373;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #ffcdd2;
                }}
                tr:hover {{
                    background-color: #f8bbd0;
                }}
                .pagination {{
                    text-align: center;
                    margin-top: 20px;
                }}
                .pagination button {{
                    background-color: #d32f2f;
                    color: white;
                    padding: 10px 15px;
                    border: none;
                    cursor: pointer;
                    border-radius: 5px;
                }}
            </style>

            <script>
                const comments = {json.dumps(negative_comments)};
                let currentPage = 1;
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p id="noCommentsMessage">No negative comments available.</p>';
                        document.getElementById('paginationControls').style.display = 'none';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = Math.min(start + commentsPerPage, comments.length);
                    const paginatedComments = comments.slice(start, end);

                    let tableHtml = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Comment</th>
                                    <th>Likes</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    paginatedComments.forEach(comment => {{
                        tableHtml += `
                            <tr>
                                <td>${{comment.username}}</td>
                                <td>${{comment.text}}</td>
                                <td>${{comment.likes}}</td>
                                <td>${{comment.timestamp}}</td>
                            </tr>
                        `;
                    }});

                    tableHtml += '</tbody></table>';

                    document.getElementById('tableContainer').innerHTML = tableHtml;
                    document.getElementById('prevButton').disabled = currentPage === 1;
                    document.getElementById('nextButton').disabled = end >= comments.length;
                }}

                function nextPage() {{
                    currentPage++;
                    renderTable();
                }}

                function previousPage() {{
                    currentPage--;
                    renderTable();
                }}

                window.onload = function () {{
                    renderTable();
                }}
            </script>
        </head>
        <body>
            <h1>Negative Comments Table</h1>
            <div id="tableContainer"></div>
            <div id="paginationControls" class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("data/negative_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'data/negative_comments_table.html' generated.")

def generate_neutral_comments_html():
    comments_per_page = 5

    # Extract neutral comments from users
    neutral_comments = []
    seen_comments = set()  # To track unique comments

    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Neutral" and comment.text not in seen_comments:
                neutral_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })
                seen_comments.add(comment.text)

    # HTML content structure
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #f9f9f9;
                    margin: 2em;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                    word-wrap: break-word;
                    max-width: 300px;
                }}
                th {{
                    background-color: #808080; /* Neutral gray */
                    color: white;
                    text-transform: uppercase;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f0f0f0; /* Light gray for even rows */
                }}
                tr:hover {{
                    background-color: #e0e0e0; /* Slight hover effect */
                    cursor: pointer;
                }}
                td {{
                    color: #333333; /* Dark gray for text */
                }}
                .pagination {{
                    margin-top: 10px;
                    text-align: center;
                }}
                .pagination button {{
                    background-color: #808080;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    margin-right: 5px;
                    cursor: pointer;
                    border-radius: 5px;
                    transition: background-color 0.2s ease;
                }}
                .pagination button:hover {{
                    background-color: #A9A9A9; /* Light grayish for hover */
                }}
                .pagination button:disabled {{
                    background-color: #cccccc;
                    cursor: not-allowed;
                }}
            </style>

            <script>
                let currentPage = 1;
                const comments = {json.dumps(neutral_comments)};  // Properly embedded JSON
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p id="noCommentsMessage">No neutral comments available.</p>';
                        document.getElementById('paginationControls').style.display = 'none';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = Math.min(start + commentsPerPage, comments.length); // Ensure 'end' does not go beyond array length
                    const paginatedComments = comments.slice(start, end);

                    let tableHtml = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Comment</th>
                                    <th>Likes</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    paginatedComments.forEach(comment => {{
                        tableHtml += `
                            <tr>
                                <td>${{comment.username}}</td>
                                <td>${{comment.text}}</td>
                                <td>${{comment.likes}}</td>
                                <td>${{comment.timestamp}}</td>
                            </tr>
                        `;
                    }});

                    tableHtml += '</tbody></table>';

                    document.getElementById('tableContainer').innerHTML = tableHtml;
                    document.getElementById('prevButton').disabled = currentPage === 1;
                    document.getElementById('nextButton').disabled = end >= comments.length;
                }}

                function nextPage() {{
                    currentPage++;
                    renderTable();
                }}

                function previousPage() {{
                    currentPage--;
                    renderTable();
                }}

                window.onload = function () {{
                    renderTable();
                }}
            </script>
        </head>
        <body>
            <h1>Neutral Comments Table</h1>
            <div id="tableContainer"></div>
            <div id="paginationControls" class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("data/neutral_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'data/neutral_comments_table.html' generated.")

def generate_positive_comments_html():
    comments_per_page = 5

    # Extract positive comments from users
    positive_comments = []
    seen_comments = set()  # To track unique comments

    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Positive" and comment.text not in seen_comments:
                positive_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })
                seen_comments.add(comment.text)

    # HTML content structure with improved style
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #e8f5e9;  /* Light green background */
                    margin: 2em;
                    color: #333;
                }}
                h1 {{
                    text-align: center;
                    color: #388e3c; /* Green */
                    font-size: 2.5em;
                    margin-bottom: 20px;
                }}
                table {{
                    width: 80%;
                    border-collapse: collapse;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.1);
                    margin: 0 auto;
                    overflow: hidden;
                }}
                th, td {{
                    padding: 14px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                    word-wrap: break-word;
                }}
                th {{
                    background-color: #81c784;  /* Light green */
                    color: white;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                tr:nth-child(even) {{
                    background-color: #f1f8e9;  /* Slightly lighter green */
                }}
                tr:hover {{
                    background-color: #c8e6c9; /* Light hover effect */
                    cursor: pointer;
                }}
                td {{
                    color: #388e3c;  /* Green text */
                }}
                .pagination {{
                    text-align: center;
                    margin-top: 20px;
                }}
                .pagination button {{
                    background-color: #388e3c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    margin-right: 5px;
                    cursor: pointer;
                    border-radius: 5px;
                    transition: background-color 0.3s ease;
                    font-size: 1em;
                }}
                .pagination button:hover {{
                    background-color: #66bb6a;  /* Darker green for hover */
                }}
                .pagination button:disabled {{
                    background-color: #bdbdbd;
                    cursor: not-allowed;
                }}
                .pagination button:active {{
                    background-color: #388e3c;
                    transform: scale(0.98);
                }}
            </style>

            <script>
                let currentPage = 1;
                const comments = {json.dumps(positive_comments)};  // Properly embedded JSON
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p id="noCommentsMessage">No positive comments available.</p>';
                        document.getElementById('paginationControls').style.display = 'none';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = Math.min(start + commentsPerPage, comments.length); // Ensure 'end' does not go beyond array length
                    const paginatedComments = comments.slice(start, end);

                    let tableHtml = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Comment</th>
                                    <th>Likes</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    paginatedComments.forEach(comment => {{
                        tableHtml += `
                            <tr>
                                <td>${{comment.username}}</td>
                                <td>${{comment.text}}</td>
                                <td>${{comment.likes}}</td>
                                <td>${{comment.timestamp}}</td>
                            </tr>
                        `;
                    }});

                    tableHtml += '</tbody></table>';

                    document.getElementById('tableContainer').innerHTML = tableHtml;
                    document.getElementById('prevButton').disabled = currentPage === 1;
                    document.getElementById('nextButton').disabled = end >= comments.length;
                }}

                function nextPage() {{
                    currentPage++;
                    renderTable();
                }}

                function previousPage() {{
                    currentPage--;
                    renderTable();
                }}

                window.onload = function () {{
                    renderTable();
                }}
            </script>
        </head>
        <body>
            <h1>Positive Comments Table</h1>
            <div id="tableContainer"></div>
            <div id="paginationControls" class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("data/positive_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'data/positive_comments_table.html' generated.")


import time

def generateGraphs(username):
    global users
    users.clear()
    filename = "data/commentData.csv"

    readDataAndInitialise(filename)  # Process the raw data

    # Generate the pie chart
    visualize_sentiment_pie_chart()  # Visualize sentiment distribution in pie chart
    generate_word_clouds()
    generate_negative_comments_html()
    generate_neutral_comments_html()
    generate_positive_comments_html()

    # Get the current timestamp for unique file names (in milliseconds)
    timestamp = int(time.time() * 1000)  # Milliseconds for more precision

    # List of files to be uploaded with timestamps added to the filenames
    files_to_upload = [
        ("data/negative_comments_table.html", f"{username}/negative_comments_table_{timestamp}.html"),
        ("data/neutral_comments_table.html", f"{username}/neutral_comments_table_{timestamp}.html"),
        ("data/positive_comments_table.html", f"{username}/positive_comments_table_{timestamp}.html"),
        ("data/sentiment_pie_chart.png", f"{username}/sentiment_pie_chart_{timestamp}.png"),
        ("data/wordcloud_negative.png", f"{username}/wordcloud_negative_{timestamp}.png"),
        ("data/wordcloud_positive.png", f"{username}/wordcloud_positive_{timestamp}.png"),
        ("data/wordcloud_neutral.png", f"{username}/wordcloud_neutral_{timestamp}.png")
    ]
    
    # Upload the new files without deletion
    for local_file, remote_file in files_to_upload:
        try:
            # Upload the new file with a unique timestamped name
            success = st.upload_to_firebase(file_path=local_file, destination_blob_name=remote_file)
            
            if success:
                print(f"Successfully uploaded {remote_file}")
            else:
                print(f"Failed to upload {remote_file}")
        except Exception as e:
            print(f"Error uploading {remote_file}: {e}")
            
    print (comments_list)
    print("users is cleared")
    print(f"All files uploaded for user {username}.")
    print(users)

    
