import json
import networkx as nx
import plotly.graph_objects as go

def create_interactive_network_graph(conversations_file, output_html_file):
    # Load the JSON data
    with open(conversations_file, 'r') as file:
        data = json.load(file)

    # Initialize the graph
    G = nx.Graph()
    G.add_node('post')

    comment_user_map = {}
    user_conversations = {}

    for conversation_id, conversation_data in data.items():
        comments = conversation_data['comments']

        for comment in comments:
            username = comment['username']
            comment_id = comment['comment_id']
            parent_id = comment['parent_id']

            # Add the user to the graph and the 'post' node connection
            G.add_node(username)
            G.add_edge('post', username)

            # Map comment to user
            comment_user_map[comment_id] = username

            # Track which conversations each user is in
            if username not in user_conversations:
                user_conversations[username] = []
            if conversation_id not in user_conversations[username]:
                user_conversations[username].append(conversation_id)

            # Add edges between users if there's a reply relationship
            if parent_id and parent_id in comment_user_map:
                parent_user = comment_user_map[parent_id]
                if username != parent_user:
                    G.add_edge(username, parent_user)

    # Centrality analysis (degree centrality for simplicity)
    centrality = nx.degree_centrality(G)

    # Sort nodes by centrality in descending order
    sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

    # Exclude the 'post' node from being highlighted
    sorted_nodes = [node for node in sorted_nodes if node[0] != 'post']

    # Get the top 5 most central nodes
    top_5_central_nodes = [node[0] for node in sorted_nodes[:5]]

    # Get node positions for visualization
    pos = nx.spring_layout(G)

    # Extract the node positions, names, and colors
    x_nodes = [pos[node][0] for node in G.nodes()]
    y_nodes = [pos[node][1] for node in G.nodes()]
    node_text = [f"{node}" for node in G.nodes()]  # Show only username in node title

    edges_x = []
    edges_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edges_x.append(x0)
        edges_x.append(x1)
        edges_x.append(None)
        edges_y.append(y0)
        edges_y.append(y1)
        edges_y.append(None)

    # Create edge traces
    edge_trace = go.Scatter(
        x=edges_x, y=edges_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node trace
    node_trace = go.Scatter(
        x=x_nodes, y=y_nodes,
        mode='markers+text',
        text=node_text,  # Username only in node title
        hoverinfo='text',  # Show conversation details in hovertext
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=15,
            colorbar=None  # Remove the color bar
        )
    )

    # Highlight the top 5 most central nodes
    node_marker = node_trace.marker
    node_marker['color'] = ['red' if node in top_5_central_nodes else 'blue' for node in G.nodes()]
    node_marker['size'] = [20 if node in top_5_central_nodes else 10 for node in G.nodes()]

    # Set up hover text to show conversations for each user
    hovertext = [f"{node}: {', '.join(user_conversations.get(node, []))}" for node in G.nodes()]
    node_trace.hovertext = hovertext

    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(showlegend=False, title="Interactive Network Graph with Conversations")

    # Save the plot as an HTML file
    fig.write_html(output_html_file)

    print(f"Graph saved to {output_html_file}")


