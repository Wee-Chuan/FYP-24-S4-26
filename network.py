from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from umap import UMAP
from classes import Comment, User
import csv
import re
import plotly.graph_objects as go
import networkx as nx
from community import community_louvain  # Import for Louvain community 
import json

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

# Initialize BERTopic with default parameters
vectorizer_model = CountVectorizer(stop_words="english")
topic_model = BERTopic(vectorizer_model=vectorizer_model)

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

            # Preprocess the comment text
            processed_text = preprocess_text(text)

            # Create Comment object
            comment = Comment(text=text, likes=likes, replies=replies)
            sentiment = get_sentiment(text)  # Assign sentiment
            comment.sentiment = sentiment

            # Add comment to user
            if username not in users:
                users[username] = User(username=username)
            user_comments = users[username].comments
            user_comments.append(comment)

            # Add to global comments list for topic modeling
            comments_list.append(processed_text)
            comment_mapping.append((username, len(user_comments) - 1))  # Track user and comment index

    # Fit the BERTopic model on the comments
    topics, _ = topic_model.fit_transform(comments_list)

    # Assign topics to comments using the mapping
    for idx, topic_id in enumerate(topics):
        username, comment_idx = comment_mapping[idx]
        users[username].comments[comment_idx].topic = topic_id

# Create a graph to represent the users
user_graph = nx.Graph()

def build_user_graph():
    global user_graph

    # Loop through all users and their comments
    for username, user in users.items():
        # Add user as a node
        if username not in user_graph:
            user_graph.add_node(username)

        # Compare this user's comments with others to add edges
        for other_username, other_user in users.items():
            if username != other_username:  # Avoid self-loops
                # Check if they have at least one comment with the same sentiment
                if any(comment.sentiment == other_comment.sentiment for comment in user.comments for other_comment in other_user.comments):
                    user_graph.add_edge(username, other_username)  # Add an edge

def visualize_graph_3d_with_sentiment_legend(username_para):
    # Use NetworkX's spring layout with 3D positions
    pos = nx.spring_layout(user_graph, dim=3)  # Spring layout with 3 dimensions

    # Define fixed colors for sentiments
    sentiment_colors = {"Negative": "red", "Neutral": "blue", "Positive": "green"}

    # Count the number of nodes for each sentiment
    sentiment_counts = {"Negative": 0, "Neutral": 0, "Positive": 0}
    for username in user_graph.nodes():
        if users[username].comments:
            sentiment = users[username].comments[0].sentiment
            sentiment_counts[sentiment] += 1

    # Extract node positions and colors based on their sentiment
    node_x = [pos[node][0] for node in user_graph.nodes()]
    node_y = [pos[node][1] for node in user_graph.nodes()]
    node_z = [pos[node][2] for node in user_graph.nodes()]
    node_colors = [
        sentiment_colors[users[node].comments[0].sentiment] if users[node].comments else "gray"
        for node in user_graph.nodes()
    ]

    # Extract edge positions
    edge_x = []
    edge_y = []
    edge_z = []
    for edge in user_graph.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]

    # Create the trace for nodes
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        marker=dict(size=8, color=node_colors, opacity=0.8),
        text=list(user_graph.nodes()),  # Add node labels as hover text
        hoverinfo='text',
        name="Nodes"  # Ensures the legend doesn't confuse this with extra traces
    )

    # Create the trace for edges
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(width=1, color="gray"),
        hoverinfo='none',
        showlegend=False  # Hide edges from the legend
    )

    # Add legend for nodes (sentiments)
    legend_traces = []
    for sentiment, color in sentiment_colors.items():
        count = sentiment_counts[sentiment]  # Get count for each sentiment
        legend_traces.append(
            go.Scatter3d(
                x=[None], y=[None], z=[None],  # Dummy points for legend
                mode="markers",
                marker=dict(size=10, color=color),
                name=f"{sentiment} ({count})"  # Append the count to the legend label
            )
        )

    graph_title = "3D User Graph with Sentiment-Based Node Colors: " + username_para
    # Layout configuration
    layout = go.Layout(
        title= graph_title,
        showlegend=True,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )

    # Combine traces and create the figure
    fig = go.Figure(data=[edge_trace, node_trace] + legend_traces, layout=layout)

    # Save the figure as an HTML file
    pio.write_html(fig, file="static/sentimentgraph.html", auto_open=False)

# Load users from a file
def load_users_from_file(filename="users_data.json"):
    global users
    with open(filename, "r") as file:
        loaded_data = json.load(file)
        for username, user_data in loaded_data.items():
            user_obj = User(username=username)
            for comment_data in user_data["comments"]:
                comment_obj = Comment(
                    text=comment_data["text"],
                    likes=comment_data["likes"],
                    replies=comment_data["replies"],
                )
                comment_obj.sentiment = comment_data["sentiment"]
                comment_obj.topic = comment_data["topic"]
                user_obj.comments.append(comment_obj)
            users[username] = user_obj

# Save topic counts and keywords to files
def save_topic_data(topic_model, comments_list, topic_filename="topic_counts.json", keywords_filename="topic_keywords.json"):
    # Get topic counts
    topic_counts = topic_model.get_topic_info()
    topic_counts_dict = {
        int(row["Topic"]): {
            "count": int(row["Count"]),
            "name": row["Name"]
        }
        for _, row in topic_counts.iterrows()
    }

    # Save topic counts to a file
    with open(topic_filename, "w") as file:
        json.dump(topic_counts_dict, file, indent=4)

    # Get topic keywords
    topic_keywords_dict = {}
    for topic_id in topic_model.get_topics():
        # Extract keywords for each topic
        topic_keywords_dict[topic_id] = {
            "keywords": [
                word for word, _ in topic_model.get_topic(topic_id)
            ]
        }

    # Save topic keywords to a file
    with open(keywords_filename, "w") as file:
        json.dump(topic_keywords_dict, file, indent=4)

# Save users and related topic data
def save_users_to_file(user_filename="users_data.json", topic_filename="topic_counts.json", keywords_filename="topic_keywords.json"):
    data_to_save = {}
    for username, user in users.items():
        data_to_save[username] = {
            "comments": [
                {
                    "text": comment.text,
                    "likes": comment.likes,
                    "replies": comment.replies,
                    "sentiment": comment.sentiment,
                    "topic": comment.topic,
                }
                for comment in user.comments
            ]
        }

    # Save users to a JSON file
    with open(user_filename, "w") as file:
        json.dump(data_to_save, file, indent=4)

    # Save topic-related data
    save_topic_data(topic_model, comments_list, topic_filename, keywords_filename)

import networkx as nx
import plotly.graph_objects as go

def build_topic_graph():
    topic_graph = nx.Graph()

    # Assign users to topics
    user_topics = {}
    for username, user in users.items():
        # Determine the user's primary topic (most frequent topic in their comments)
        topics = [comment.topic for comment in user.comments if comment.topic is not None]
        if topics:
            primary_topic = max(set(topics), key=topics.count)
            user_topics[username] = primary_topic

    # Add nodes and edges based on topics
    for user, topic in user_topics.items():
        topic_graph.add_node(user, topic=topic)  # Add user nodes with topic attribute

        # Connect users with the same topic
        for other_user, other_topic in user_topics.items():
            if user != other_user and topic == other_topic:
                topic_graph.add_edge(user, other_user)

    return topic_graph, user_topics

import plotly.io as pio
    
def visualize_topic_graph_2d(topic_graph, user_topics):
    
    with open('topic_counts.json', 'r') as file:
        topic_counts = json.load(file)
        
    # Generate 2D positions for the nodes
    pos = nx.spring_layout(topic_graph)  # 2D spring layout

    # Assign colors to topics
    unique_topics = set(user_topics.values())
    topic_colors = {topic: f"hsl({i * 360 / len(unique_topics)}, 80%, 60%)" for i, topic in enumerate(unique_topics)}

    # Extract node positions and colors based on topics
    node_x = [pos[node][0] for node in topic_graph.nodes()]
    node_y = [pos[node][1] for node in topic_graph.nodes()]
    node_colors = [topic_colors[user_topics[node]] for node in topic_graph.nodes()]

    # Extract edge positions
    edge_x = []
    edge_y = []
    for edge in topic_graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    # Create the trace for edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="rgba(0, 0, 0, 0)"),  # Transparent edges
        hoverinfo="none",
        mode="lines"
    )

    # Create the trace for nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        marker=dict(
            size=10,
            color=node_colors,
            opacity=0.8,
            line=dict(width=0, color="black")
        )
    )

    # Add topic labels (calculate the average position of nodes in each cluster)
    topic_labels = []
    for topic in unique_topics:
        # Get the topic name from the topic_counts dictionary using the topic number as the key
        topic_name = topic_counts.get(str(topic), {}).get("name", f"Topic {topic}")
        
        cluster_nodes = [node for node, t in user_topics.items() if t == topic]
        cluster_x = [pos[node][0] for node in cluster_nodes]
        cluster_y = [pos[node][1] for node in cluster_nodes]
        if cluster_x and cluster_y:
            avg_x = sum(cluster_x) / len(cluster_x)
            avg_y = sum(cluster_y) / len(cluster_y)
            topic_labels.append(
                go.Scatter(
                    x=[avg_x], y=[avg_y],
                    mode="text",
                    text=topic_name,  # Use the topic name instead of the topic number
                    hoverinfo="none",
                    textfont=dict(size=16, color="black")
                )
            )

    # Layout configuration
    layout = go.Layout(
        title="2D User Graph Clustered by Topics",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )

    # Combine traces and create the figure
    fig = go.Figure(data=[edge_trace, node_trace] + topic_labels, layout=layout)

    # Save the figure as an HTML file
    pio.write_html(fig, file="static/topicnetwork.html", auto_open=False)

# Main function to visualize topic-based clustering
def visualize_topics():
    topic_graph, user_topics = build_topic_graph()
    visualize_topic_graph_2d(topic_graph, user_topics)

# Modify the main function
def generateGraphs(username):
    filename = "commentData.csv"
    processed_user_file = "users_data.json"
    topic_count_file = "topic_counts.json"
    topic_keywords_file = "topic_keywords.json"

    readDataAndInitialise(filename)  # Process the raw data
    print(f"Saving processed data to {processed_user_file}...")
    save_users_to_file(processed_user_file, topic_count_file, topic_keywords_file)  # Save users and topic data

    build_user_graph()  # Build the graph with nodes and edges
    visualize_graph_3d_with_sentiment_legend(username)  # Visualize the graph
    visualize_topics()



