import os
import json
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore
import networkx as nx
import community as community_louvain
import matplotlib.pyplot as plt
from collections import Counter

# Load environment variables
load_dotenv()

# Firebase Initialization
if not firebase_admin._apps:
    firebase_credentials = {
        "type": os.getenv("GOOGLE_CLOUD_TYPE"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("GOOGLE_CLOUD_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLOUD_CLIENT_ID"),
        "auth_uri": os.getenv("GOOGLE_CLOUD_AUTH_URI"),
        "token_uri": os.getenv("GOOGLE_CLOUD_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("GOOGLE_CLOUD_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("GOOGLE_CLOUD_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("GOOGLE_CLOUD_UNIVERSE_DOMAIN")
    }

    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Fetch user interaction data from Firestore
def get_user_data_from_firestore():
    # Fetch documents from 'user_interactions' collection
    users_ref = db.collection('user_interactions')
    docs = users_ref.stream()

    data = []
    for doc in docs:
        user_data = doc.to_dict()  # Get the data from each document
        data.append(user_data)

    return data

# Function to check if the logged-in user exists in the database
def get_logged_in_user_data(username):
    # Fetch documents for the specific user
    users_ref = db.collection('user_interactions')
    user_ref = users_ref.where("username", "==", username).limit(1).stream()

    # If user exists, return the data; otherwise, return None
    user_data = next(user_ref, None)
    if user_data:
        return user_data.to_dict()
    return None

def plot_no_data_found(filename="static/graph1.png"):
    # Generate an image with the text "SORRY NO DATA FOUND"
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.text(0.5, 0.5, 'SORRY NO DATA FOUND', horizontalalignment='center', verticalalignment='center', fontsize=16, color='red')
    ax.axis('off')
    plt.savefig(filename, format="PNG")
    plt.close()

def plot_2d_network(G, pos_2d, partition, community_labels, title, filename="static/graph1.png"):
    plt.figure(figsize=(12, 8))

    # Fixed parameters for edges (uniform opacity and thickness)
    edge_opacity = 0.5  # Set opacity
    edge_thickness = 1  # Set thickness

    # Draw all edges with uniform color, opacity, and thickness
    for u, v in G.edges():
        nx.draw_networkx_edges(G, pos_2d, edgelist=[(u, v)], edge_color="lightgray", width=edge_thickness, alpha=edge_opacity)

    # Draw nodes with community-based colors
    unique_communities = set(partition.values())
    community_colors = {community: f"C{i}" for i, community in enumerate(unique_communities)}

    for community in unique_communities:
        nodes_in_community = [node for node, com in partition.items() if com == community]
        nx.draw_networkx_nodes(
            G, pos_2d,
            nodelist=nodes_in_community,
            node_color=community_colors[community],
            label=community_labels.get(community, f"Community {community}"),
            node_size=300
        )

    # Draw node labels
    nx.draw_networkx_labels(G, pos_2d, font_size=8, font_color="black")

    # Add title and axis
    plt.title(title, fontsize=16)
    plt.axis("off")

    # Save the figure as a PNG file
    plt.savefig(filename, format="PNG")
    plt.close()


def plot_influential_nodes(G, pos_2d, centrality_measures, title, filename="static/graph2.png", top_n=5):
    plt.figure(figsize=(12, 8))
    
    # Fixed parameters for edges (uniform opacity and thickness)
    edge_opacity = 0.5  # Set opacity
    edge_thickness = 1  # Set thickness

    # Draw all edges with uniform color, opacity, and thickness
    for u, v in G.edges():
        nx.draw_networkx_edges(G, pos_2d, edgelist=[(u, v)], edge_color="lightgray", width=edge_thickness, alpha=edge_opacity)

    # Draw all nodes in a default color (e.g., light gray)
    nx.draw_networkx_nodes(G, pos_2d, node_color="lightgray", node_size=300)

    # Highlight top influential nodes in red
    highlighted_nodes = set()
    for centrality_name, nodes in centrality_measures.items():
        top_nodes = sorted(nodes.items(), key=lambda x: x[1], reverse=True)[:top_n]
        for node, _ in top_nodes:
            highlighted_nodes.add(node)

    # Draw the top influential nodes in red
    nx.draw_networkx_nodes(
        G, pos_2d,
        nodelist=list(highlighted_nodes),
        node_color="red",
        node_size=500,
        label=f"Top {top_n} Influential Nodes"
    )
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos_2d, font_size=8, font_color="black")
    
    # Add title and legend
    plt.legend(loc="best")
    plt.title(title, fontsize=16)
    plt.axis("off")
    
    # Save the figure as a PNG file
    plt.savefig(filename, format="PNG")
    plt.close()

def main(username):
    # Fetch the logged-in user data
    user_data = get_logged_in_user_data(username)

    if not user_data:
        # If user not found, generate "SORRY NO DATA FOUND" graph
        plot_no_data_found(filename="static/graph1.png")
        plot_no_data_found(filename="static/graph2.png")
        return

    # Create an empty graph (undirected graph)
    G = nx.Graph()

    # Define weights for the interaction types and other factors
    w1, w2, w3 = 1, 1, 1  # weights for likes, comments, reposts (can be adjusted)
    w4, w5 = 0.5, 0.5  # weights for reciprocity and follow-back

    # Define small constants to avoid zero weights
    EPSILON = 0.1
    MIN_RECIPROCITY = 0.5
    MIN_FOLLOW_BACK = 0.5

    # Add the username node
    G.add_node(username)

    # Add nodes from the followers list only
    followers = user_data.get("followers_list", [])
    for follower in followers:
        G.add_node(follower)

    # Add edges between followers and the username node
    for follower in followers:
        # Add edge from the username node to each follower (if interaction exists)
        interaction_score = (
            w4 * user_data["interactions"].get(follower, {}).get("likes", 0) +
            w5 * user_data["interactions"].get(follower, {}).get("comments", 0) +
            EPSILON  # Base weight for connection
        )
        if interaction_score > 0:
            G.add_edge(username, follower, weight=interaction_score)

    # Add edges between followers based on their interactions
    for follower in followers:
        follower_data = get_logged_in_user_data(follower)
        if follower_data:
            for other_follower in follower_data["followers_list"]:
                if other_follower in followers and other_follower != follower:
                    # Calculate interaction score between followers
                    interaction_score = (
                        w1 * follower_data["interactions"].get(other_follower, {}).get("likes", 0) +
                        w2 * follower_data["interactions"].get(other_follower, {}).get("comments", 0) +
                        w3 * follower_data["interactions"].get(other_follower, {}).get("reposts", 0) +
                        EPSILON  # Base weight
                    )
                    if interaction_score > 0:
                        G.add_edge(follower, other_follower, weight=interaction_score)

    # If the graph has no nodes, generate "SORRY NO DATA FOUND" graph
    if len(G.nodes) == 0:
        plot_no_data_found()
        return

    # Run the Louvain algorithm to detect communities
    partition = community_louvain.best_partition(G)

    # Generate 2D positions for nodes
    pos_2d = nx.spring_layout(G, seed=42)

    # Get centrality measures for influential nodes
    centrality_measures = {
        "Degree": nx.degree_centrality(G),
        "Closeness": nx.closeness_centrality(G),
        "Betweenness": nx.betweenness_centrality(G),
    }

    # Plot 1: Network with Communities
    plot_2d_network(G, pos_2d, partition, {k: k for k in partition.values()}, "Network with Communities (2D)")

    # Plot 2: Network with Influential Nodes
    plot_influential_nodes(G, pos_2d, centrality_measures, "Network with Influential Nodes Highlighted")

