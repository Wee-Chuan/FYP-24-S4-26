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

# Function to identify influential nodes using centrality measures
def identify_influential_nodes(G, top_n=5):
    # Calculate centrality measures
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)

    # Combine centrality measures into a dictionary
    centrality_measures = {
        "Degree": degree_centrality,
        "Closeness": closeness_centrality,
        "Betweenness": betweenness_centrality,
    }

    # Identify top N influential nodes for each centrality measure
    top_nodes = {
        measure: sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]
        for measure, centrality in centrality_measures.items()
    }

    return centrality_measures, top_nodes

# Function to extract top hashtags for each community
def get_top_hashtags(data, partition):
    community_hashtags = {}

    # Loop over users and get hashtags per community
    for user in data:
        username = user["username"]
        user_community = partition.get(username, None)

        if user_community is not None:
            if user_community not in community_hashtags:
                community_hashtags[user_community] = []

            community_hashtags[user_community].extend(user["hashtags"])

    # Get top 3 hashtags for each community
    top_hashtags = {}
    for community, hashtags in community_hashtags.items():
        hashtag_counts = Counter(hashtags)
        top_3 = [hashtag for hashtag, _ in hashtag_counts.most_common(3)]
        top_hashtags[community] = top_3

    return top_hashtags

def plot_2d_network(G, pos_2d, partition, community_labels, title, filename="static/graph1.png"):
    plt.figure(figsize=(12, 8))
    
    # Assign colors to communities
    unique_communities = set(partition.values())
    community_colors = {community: f"C{i}" for i, community in enumerate(unique_communities)}

    # Draw edges
    nx.draw_networkx_edges(G, pos_2d, alpha=0.5)

    # Draw nodes with community-based colors
    for community in unique_communities:
        nodes_in_community = [node for node, com in partition.items() if com == community]
        nx.draw_networkx_nodes(
            G, pos_2d,
            nodelist=nodes_in_community,
            node_color=community_colors[community],
            label=community_labels[community],
            node_size=300
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

def plot_influential_nodes(G, pos_2d, centrality_measures, title, filename="static/graph2.png", top_n=5):
    plt.figure(figsize=(12, 8))
    
    # Draw edges
    nx.draw_networkx_edges(G, pos_2d, alpha=0.5)

    # Draw all nodes in a default color (e.g., light gray)
    nx.draw_networkx_nodes(G, pos_2d, node_color="lightgray", node_size=300)

    # Highlight top influential nodes in red
    highlighted_nodes = set()
    for centrality_name, nodes in centrality_measures.items():
        top_nodes = sorted(nodes.items(), key=lambda x: x[1], reverse=True)[:top_n]
        for node, _ in top_nodes:
            highlighted_nodes.add(node)

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

def main():
    # Now, instead of loading from a local file, load data from Firestore
    data = get_user_data_from_firestore()

    # Create an empty graph (undirected graph)
    G = nx.Graph()

    # Define weights for the interaction types and other factors
    w1, w2, w3 = 1, 1, 1  # weights for likes, comments, reposts (can be adjusted)
    w4, w5 = 0.5, 0.5  # weights for reciprocity and follow-back

    # Define small constants to avoid zero weights
    EPSILON = 0.1
    MIN_RECIPROCITY = 0.5
    MIN_FOLLOW_BACK = 0.5

    # Add edges for followers/following
    for user in data:
        username = user["username"]
        for follower in user["followers_list"]:
            if follower != username:  # Skip self-interaction
                # Compute weights for interactions
                interaction_score = (
                    w1 * user["interactions"].get(follower, {}).get("likes", 0) +
                    w2 * user["interactions"].get(follower, {}).get("comments", 0) +
                    w3 * user["interactions"].get(follower, {}).get("reposts", 0) +
                    EPSILON  # Base weight
                )

                reciprocal_interaction_score = (
                    w1 * user["interactions"].get(username, {}).get("likes", 0) +
                    w2 * user["interactions"].get(username, {}).get("comments", 0) +
                    w3 * user["interactions"].get(username, {}).get("reposts", 0) +
                    EPSILON  # Base weight
                )

                if interaction_score > 0 and reciprocal_interaction_score > 0:
                    reciprocity_factor = min(interaction_score, reciprocal_interaction_score) / max(interaction_score, reciprocal_interaction_score)
                else:
                    reciprocity_factor = MIN_RECIPROCITY

                follow_back_factor = 1 if username in user["followers_list"] else MIN_FOLLOW_BACK

                edge_weight = interaction_score * (1 + w4 * reciprocity_factor + w5 * follow_back_factor)

                # Add or update edge in graph
                if G.has_edge(follower, username):
                    G[follower][username]['weight'] += edge_weight
                else:
                    G.add_edge(follower, username, weight=edge_weight)

    # Run the Louvain algorithm to detect communities
    partition = community_louvain.best_partition(G)

    # Generate 2D positions for nodes
    pos_2d = nx.spring_layout(G, seed=42)

    # Get top hashtags for each community
    top_hashtags = get_top_hashtags(data, partition)

    # Rename communities with top 3 hashtags
    community_labels = {
        community: ", ".join(hashtags) if hashtags else f"Community {community}"
        for community, hashtags in top_hashtags.items()
    }

    # Plot 1: Network with Communities
    plot_2d_network(G, pos_2d, partition, community_labels, "Network with Communities (2D)")

    # Calculate centrality measures and identify influential nodes
    centrality_measures, top_nodes = identify_influential_nodes(G)

    # Display top nodes for each centrality measure
    for measure, nodes in top_nodes.items():
        print(f"\nTop {len(nodes)} nodes by {measure} centrality:")
        for node, score in nodes:
            print(f"  Node: {node}, Score: {score:.4f}")

    # Plot 2: Network with Influential Nodes
    plot_influential_nodes(
        G, pos_2d, centrality_measures,
        "Network with Influential Nodes Highlighted", top_n=5
    )

    # Display top hashtags for each community
    for community, hashtags in top_hashtags.items():
        print(f"Community '{community_labels[community]}': {', '.join(hashtags)}")

# Run the main function
main()
