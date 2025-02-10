import csv
import re
import json
import plotly.graph_objects as go
import plotly.io as pio
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from classes import Comment, User
import entity.admin as st

# Global variables
users = {}
comments_list = []  # To store all comments for topic modeling
comment_mapping = []  # To track comment-to-user mapping for topic assignment

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
    plt.savefig('static/sentiment_pie_chart.png')  # Save as PNG image
    plt.close()
 

from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Function to generate a word cloud for each sentiment
def generate_word_clouds():
    sentiment_texts = {"Negative": "", "Neutral": "", "Positive": ""}

    # Collect text for each sentiment
    for username, user in users.items():
        for comment in user.comments:
            sentiment_texts[comment.sentiment] += comment.text + " "

    # Generate and save word clouds for each sentiment
    for sentiment, text in sentiment_texts.items():
        # Generate the word cloud
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

        # Display the word cloud
        plt.figure(figsize=(8, 4))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title(f"Word Cloud for {sentiment} Sentiment")
        
        # Save the word cloud as an image
        wordcloud_file = f"static/wordcloud_{sentiment.lower()}.png"
        plt.savefig(wordcloud_file)
        plt.close()

        print(f"Saved word cloud for {sentiment} sentiment at {wordcloud_file}")

def generate_negative_comments_html():
    comments_per_page = 5

    # Extract negative comments from users
    negative_comments = []
    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Negative":
                negative_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })

    if not negative_comments:
        print("No negative comments found.")
        return

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
                    background-color: #B22222; /* Dark Red */
                    color: white;
                    text-transform: uppercase;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #FDEDEC; /* Light red tint for even rows */
                }}
                tr:hover {{
                    background-color: #FFCCCC; /* Slight hover effect */
                    cursor: pointer;
                }}
                td {{
                    color: #7D0000; /* Deep red for text */
                }}
                .pagination {{
                    margin-top: 10px;
                    text-align: center;
                }}
                .pagination button {{
                    background-color: #B22222;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    margin-right: 5px;
                    cursor: pointer;
                    border-radius: 5px;
                    transition: background-color 0.2s ease;
                }}
                .pagination button:hover {{
                    background-color: #FF4C4C;
                }}
                .pagination button:disabled {{
                    background-color: #cccccc;
                    cursor: not-allowed;
                }}
            </style>

            <script>
                let currentPage = 1;
                const comments = {json.dumps(negative_comments)};  // Properly embedded JSON
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p>No negative comments available.</p>';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = start + commentsPerPage;
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
            <div class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("static/negative_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'negative_comments_table.html' generated.")

def generate_neutral_comments_html():
    comments_per_page = 5

    # Extract negative comments from users
    negative_comments = []
    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Neutral":
                negative_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })

    if not negative_comments:
        print("No negative comments found.")
        return

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
                const comments = {json.dumps(negative_comments)};  // Properly embedded JSON
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p>No negative comments available.</p>';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = start + commentsPerPage;
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
            <div class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("static/neutral_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'static/neutral_comments_table.html' generated.")

def generate_positive_comments_html():
    comments_per_page = 5

    # Extract negative comments from users
    negative_comments = []
    for username, user in users.items():
        for comment in user.comments:
            if comment.sentiment == "Positive":
                negative_comments.append({
                    "text": comment.text.replace("\n", " ").replace('"', '\\"'),  # Clean newlines and escape quotes
                    "likes": comment.likes,
                    "timestamp": comment.timestamp,
                    "username": comment.username
                })

    if not negative_comments:
        print("No positive comments found.")
        return

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
                    background-color: #006400; /* Dark Green for positive tone */
                    color: white;
                    text-transform: uppercase;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2; /* Light gray for even rows */
                }}
                tr:hover {{
                    background-color: #e6f7e6; /* Light green hover effect */
                    cursor: pointer;
                }}
                td {{
                    color: #004d00; /* Darker green for text */
                }}
                .pagination {{
                    margin-top: 10px;
                    text-align: center;
                }}
                .pagination button {{
                    background-color: #006400;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    margin-right: 5px;
                    cursor: pointer;
                    border-radius: 5px;
                    transition: background-color 0.2s ease;
                }}
                .pagination button:hover {{
                    background-color: #004d00; /* Darker green for hover */
                }}
                .pagination button:disabled {{
                    background-color: #cccccc;
                    cursor: not-allowed;
                }}
            </style>

            <script>
                let currentPage = 1;
                const comments = {json.dumps(negative_comments)};  // Properly embedded JSON
                const commentsPerPage = 5;

                function renderTable() {{
                    if (comments.length === 0) {{
                        document.getElementById('tableContainer').innerHTML = '<p>No positive comments available.</p>';
                        return;
                    }}

                    const start = (currentPage - 1) * commentsPerPage;
                    const end = start + commentsPerPage;
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
            <h1>Positive Comments</h1>
            <div id="tableContainer"></div>
            <div class="pagination">
                <button id="prevButton" onclick="previousPage()">Previous</button>
                <button id="nextButton" onclick="nextPage()">Next</button>
            </div>
        </body>
    </html>
    """

    # Write the HTML content to a file
    with open("static/positive_comments_table.html", "w") as file:
        file.write(html_content)

    print("HTML file 'static/positive_comments_table.html' generated.")


# Main function to generate graphs
def generateGraphs(username):
    filename = "data/commentData.csv"
    processed_user_file = "data/users_data.json"

    readDataAndInitialise(filename)  # Process the raw data
    print(f"Saving processed data to {processed_user_file}...")
    # Optionally save data to a file here if needed

    # Generate the pie chart
    visualize_sentiment_pie_chart()  # Visualize sentiment distribution in pie chart
    generate_word_clouds()
    generate_negative_comments_html()
    generate_neutral_comments_html()
    generate_positive_comments_html()
    
    st.upload_to_firebase(file_path = "static/negative_comments_table.html", destination_blob_name = username+"/negative_comments_table.html")
    st.upload_to_firebase(file_path = "static/neutral_comments_table.html", destination_blob_name = username+"/neutral_comments_table.html")
    st.upload_to_firebase(file_path = "static/positive_comments_table.html", destination_blob_name = username+"/positive_comments_table.html")
    st.upload_to_firebase(file_path = "static/sentiment_pie_chart.png", destination_blob_name = username+"/sentiment_pie_chart.png")
    st.upload_to_firebase(file_path = "static/wordcloud_negative.png", destination_blob_name = username+"/wordcloud_negative.png")
    st.upload_to_firebase(file_path = "static/wordcloud_positive.png", destination_blob_name = username+"/wordcloud_positive.png")
    st.upload_to_firebase(file_path = "static/wordcloud_neutral.png", destination_blob_name = username+"/wordcloud_neutral.png")

