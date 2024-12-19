import json
import networkx as nx
import plotly.graph_objects as go
import community as community_louvain
from collections import Counter
from networkx.drawing.layout import spring_layout
import plotly.io as pio
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

import globals

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

# Fetch all documents from the 'user_interactions' collection and save to a JSON file
def save_user_interactions_to_file_as_list():
    try:
        # Reference to the 'user_interactions' collection
        user_interactions_ref = db.collection('user_interactions')
        
        # Get all documents in the collection
        docs = user_interactions_ref.stream()
        
        # Prepare the data as a list
        interactions = []
        for doc in docs:
            document_data = doc.to_dict()
            document_data['id'] = doc.id  # Optionally include the document ID in the data
            interactions.append(document_data)

        # Define the file path
        output_file = 'Data-Processing-Scripts/0network.json'

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Save the data to the JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(interactions, f, indent=4, ensure_ascii=False)
        
        print(f"Data saved successfully to {output_file}")
    
    except Exception as e:
        print(f"Error fetching and saving documents: {e}")

# Load the data from 0network.json
def load_data():
    if globals.data_loaded == False:
        save_user_interactions_to_file_as_list()
        globals.data_loaded = True
        print("DATA READ")
    else:
        print("DATA NOT READ")
    with open('Data-Processing-Scripts/0network.json') as f:
        return json.load(f)

# Function to check if a username exists in the data
def get_user_data(username, data):
    for user in data:
        if user['username'] == username:
            return user
    return None

# Define weights for interaction types and other factors
w1, w2, w3 = 0.3, 0.6, 1
w4, w5 = 0.5, 0.9

# Function to calculate interaction score, reciprocity factor, and final edge weight
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

# Function to normalize edge weights
def normalize_edge_weights(G):
    edge_weights = [data['weight'] for u, v, data in G.edges(data=True)]
    min_weight, max_weight = min(edge_weights), max(edge_weights)
    for u, v, data in G.edges(data=True):
        data['normalized_weight'] = (data['weight'] - min_weight) / (max_weight - min_weight) if max_weight > min_weight else 0

# Function to calculate top hashtags for each community
def get_top_hashtags_by_community(data, partition):
    community_hashtags = {}
    for node, community in partition.items():
        user_data = get_user_data(node, data)
        if user_data:
            hashtags = user_data.get("hashtags", [])
            if community not in community_hashtags:
                community_hashtags[community] = []
            community_hashtags[community].extend(hashtags)
    top_hashtags_by_community = {}
    for community, hashtags in community_hashtags.items():
        hashtag_counts = Counter(hashtags)
        top_hashtags_by_community[community] = hashtag_counts.most_common(3)
    return top_hashtags_by_community

# Perform community detection, excluding the username node
def perform_community_detection(G, username):
    subgraph_nodes = [node for node in G.nodes if node != username]
    subgraph = G.subgraph(subgraph_nodes)
    partition = community_louvain.best_partition(subgraph)
    partition[username] = -1  # Excluded from communities
    return partition

# Helper function to generate node and edge data for plotting
def generate_plot_data(G, pos, partition, is_3d=False, centrality_nodes=None, centrality_scores=None):
    edge_x, edge_y, edge_z = [], [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]] if not is_3d else pos[edge[0]][:2]
        x1, y1 = pos[edge[1]] if not is_3d else pos[edge[1]][:2]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        if is_3d:
            edge_z += [pos[edge[0]][2], pos[edge[1]][2], None]
    
    node_x, node_y, node_z, node_size, node_color, node_text = [], [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node][:2]
        node_x.append(x)
        node_y.append(y)
        node_z.append(pos[node][2] if is_3d else 0)
        node_size.append(10)

        # Color based on community for non-centrality graphs
        if centrality_nodes is None:
            community = partition.get(node, -1)  # Get community of the node
            node_color.append(community)  # Color based on the community ID (integer)
        else:
            # Highlight central nodes in red, others in gray
            if centrality_nodes and node in centrality_nodes:
                node_color.append('red')
            else:
                node_color.append('gray')
        
        # Prepare hover text with centrality score
        if centrality_scores:
            node_text.append(f"Node: {node}<br>Centrality: {centrality_scores[node]:.4f}")
        else:
            node_text.append(f"Node: {node}")
    
    return edge_x, edge_y, edge_z, node_x, node_y, node_z, node_size, node_color, node_text

# Function to create the network figure
def create_network_figure(G, pos, partition, is_3d=False, centrality_nodes=None, centrality_scores=None):
    edge_trace, node_trace = plot_network(G, pos, partition, is_3d, centrality_nodes, centrality_scores)
    
    top_hashtags = get_top_hashtags_by_community(load_data(), partition)
    legend_text = "<b>Top Hashtags by Community:</b><br>"
    for community, hashtags in top_hashtags.items():
        legend_text += f"Community {community}: " + ", ".join([f"{tag} ({count})" for tag, count in hashtags]) + "<br>"

    layout = go.Layout(
        title="Network Graph", titlefont_size=16, showlegend=False, hovermode='closest',
        margin=dict(b=0, l=0, r=200, t=40), annotations=[dict(x=1.02, y=1, xref='paper', yref='paper', text=legend_text,
                                                           showarrow=False, align="left", font=dict(size=10),
                                                           bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1)],
        scene=dict(xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False),
                   zaxis=dict(showgrid=False, zeroline=False)) if is_3d else None
    )

    return go.Figure(data=[edge_trace, node_trace], layout=layout)


# Function to create plotly network graph
def plot_network(G, pos, partition, is_3d=False, centrality_nodes=None, centrality_scores=None):
    edge_x, edge_y, edge_z, node_x, node_y, node_z, node_size, node_color, node_text = generate_plot_data(
        G, pos, partition, is_3d, centrality_nodes)

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none', mode='lines') if is_3d else go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none', mode='lines')

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers', hoverinfo='text',
        marker=dict(size=node_size, color=node_color, colorscale='Viridis', opacity=0.8, line_width=1)) if is_3d else go.Scatter(
        x=node_x, y=node_y,
        mode='markers', hoverinfo='text',
        marker=dict(size=node_size, color=node_color, opacity=0.8, line_width=2))

    node_trace.text = node_text

    return edge_trace, node_trace

def plot_user_network_with_3d(username, save_as_html=False, output_dir="templates/dashboard/influencer_menu"):
    data = load_data()
    user_data = get_user_data(username, data)
    if not user_data:
        print(f"Username '{username}' not found in the data.")
        return None
    
    G = nx.Graph()
    G.add_node(username)
    followers_list = user_data.get('followers_list', [])
    
    # Add nodes and edges for followers
    for follower in followers_list:
        G.add_node(follower)
        edge_weight = calculate_edge_weight(user_data, follower, username, data)
        G.add_edge(username, follower, weight=edge_weight)
    
    for follower in followers_list:
        follower_data = get_user_data(follower, data)
        if not follower_data:
            continue
        follower_following_list = follower_data.get('following_list', [])
        for other_follower in followers_list:
            if other_follower in follower_following_list:
                edge_weight = calculate_edge_weight(follower_data, other_follower, follower, data)
                G.add_edge(follower, other_follower, weight=edge_weight)

    normalize_edge_weights(G)
    partition = perform_community_detection(G, username)
    
    pos_2d = nx.spring_layout(G, seed=42)
    pos_3d = spring_layout(G, dim=3, seed=42)

    # Perform centrality analysis, excluding the username node
    centrality_scores = nx.degree_centrality(G)
    sorted_centrality = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
    top_4_central_nodes = [node for node, _ in sorted_centrality[:4]]
    top_4_dict = {node: centrality_scores[node] for node in top_4_central_nodes}  # Return as dictionary
    
    # Generate original 2D and 3D network figures (no centrality highlighting)
    fig_2d = create_network_figure(G, pos_2d, partition, is_3d=False)
    fig_3d = create_network_figure(G, pos_3d, partition, is_3d=True)
    
    # Generate centrality-based 2D and 3D network figures
    fig_2d_centrality = create_network_figure(G, pos_2d, partition, is_3d=False, centrality_nodes=top_4_central_nodes, centrality_scores=centrality_scores)
    fig_3d_centrality = create_network_figure(G, pos_3d, partition, is_3d=True, centrality_nodes=top_4_central_nodes, centrality_scores=centrality_scores)
    
    if save_as_html:
        os.makedirs(output_dir, exist_ok=True)
        fig_2d.write_html(os.path.join(output_dir, f"2d_network.html"))
        fig_3d.write_html(os.path.join(output_dir, f"3d_network.html"))
        fig_2d_centrality.write_html(os.path.join(output_dir, f"2d_network_centrality.html"))
        fig_3d_centrality.write_html(os.path.join(output_dir, f"3d_network_centrality.html"))
    
    print("Top 3 Nodes with Centrality Scores:", top_4_dict)
    return top_4_dict
