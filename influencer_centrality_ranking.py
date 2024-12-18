import json
import networkx as nx
from collections import Counter

# Define the weights (make sure they are set somewhere in your code)
w1, w2, w3 = 0.3, 0.6, 1
w4, w5 = 0.5, 0.9

# Load the data from 0network.json
def load_data():
    with open('Data-Processing-Scripts/0network.json') as f:
        return json.load(f)

# Function to get user data based on the username
def get_user_data(username, data):
    for user in data:
        if user['username'] == username:
            return user
    return None

# Function to calculate the edge weight between two users
def calculate_edge_weight(user_data, follower, username, data):
    interaction_score = (
        w1 * user_data["interactions"].get(follower, {}).get("likes", 0) +
        w2 * user_data["interactions"].get(follower, {}).get("comments", 0) +
        w3 * user_data["interactions"].get(follower, {}).get("reposts", 0)
    )
    reciprocal_interaction_score = (
        w1 * user_data["interactions"].get(username, {}).get("likes", 0) +
        w2 * user_data["interactions"].get(username, {}).get("comments", 0) +
        w3 * user_data["interactions"].get(username, {}).get("reposts", 0)
    )
    reciprocity_factor = (
        min(interaction_score, reciprocal_interaction_score) /
        max(interaction_score, reciprocal_interaction_score)
        if max(interaction_score, reciprocal_interaction_score) > 0 else 0
    )
    follow_back_factor = 1 if username in get_user_data(follower, data)["followers_list"] else 0
    edge_weight = interaction_score * (1 + w4 * reciprocity_factor + w5 * follow_back_factor)
    return max(edge_weight, 0.1)  # Avoid zero edge weight

# Function to normalize edge weights (optional, if needed for better visualization)
def normalize_edge_weights(G):
    edge_weights = [data['weight'] for u, v, data in G.edges(data=True)]
    min_weight, max_weight = min(edge_weights), max(edge_weights)
    for u, v, data in G.edges(data=True):
        data['normalized_weight'] = (data['weight'] - min_weight) / (max_weight - min_weight) if max_weight > min_weight else 0

# Build the graph and calculate centrality scores
def build_graph_and_calculate_centrality():
    data = load_data()
    
    # Create an empty graph
    G = nx.Graph()
    
    # Add nodes and edges with weights
    for user in data:
        username = user['username']
        G.add_node(username)
        
        followers_list = user.get('followers_list', [])
        for follower in followers_list:
            G.add_node(follower)
            edge_weight = calculate_edge_weight(user, follower, username, data)
            G.add_edge(username, follower, weight=edge_weight)
    
    # Normalize edge weights (optional, depending on your use case)
    normalize_edge_weights(G)

    # Calculate degree centrality
    centrality_scores = nx.degree_centrality(G)

    # Sort the centrality scores in descending order
    sorted_centrality = {username: score for username, score in sorted(centrality_scores.items(), key=lambda item: item[1], reverse=True)}

    return sorted_centrality

# Get the sorted centrality scores
centrality_scores = build_graph_and_calculate_centrality()

# Print the top 5 nodes with their centrality scores
print("Top 5 users based on centrality:")
for username, score in list(centrality_scores.items())[:5]:
    print(f"{username}: {score}")
