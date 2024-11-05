import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import community as louvain

def visualize_followers_network(user, user_csv='fake_social_network_data.csv', edge_csv='fake_social_network_edges.csv'):
    # Load user data and edge data with error handling
    try:
        df_users = pd.read_csv(user_csv)
        df_edges = pd.read_csv(edge_csv)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return

    # Convert follower and following lists from string to actual lists
    df_users['Follower List'] = df_users['Follower List'].apply(eval)
    df_users['Following List'] = df_users['Following List'].apply(eval)

    # Check if the user exists in the data
    if user not in df_users['Username'].values:
        print(f"User {user} not found in data.")
        return

    # Get the user's followers
    user_followers = df_users[df_users['Username'] == user]['Follower List'].values[0]
    
    # Create a set of user followers for easier lookup
    follower_set = set(user_followers)

    # Filter edge data for relevant user edges
    user_edges = df_edges[
        (df_edges['User'] == user) | 
        (df_edges['Follower'].isin(follower_set)) | 
        (df_edges['User'].isin(follower_set))
    ]
    
    # Create a graph and add nodes and weighted edges
    user_subgraph = nx.Graph()
    user_subgraph.add_node(user)

    for _, row in user_edges.iterrows():
        follower = row['Follower']
        target_user = row['User']
        user_subgraph.add_node(follower)
        user_subgraph.add_node(target_user)
        
        # Calculate edge weight, handling missing values
        weight = calculate_edge_weight(row.get('Likes', 0), row.get('Comments', 0), row.get('Shares', 0))
        user_subgraph.add_edge(follower, target_user, weight=weight)

    # Community detection using the Louvain method
    partition = louvain.best_partition(user_subgraph, weight='weight')

    # Get positions for nodes
    pos = nx.spring_layout(user_subgraph, seed=42)

    # Create a Plotly figure
    edge_x = []
    edge_y = []
    edge_weight = []
    edge_info = []
    
    for edge in user_subgraph.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])  # Add x coordinates with None to separate lines
        edge_y.extend([y0, y1, None])  # Add y coordinates with None to separate lines
        edge_weight.append(edge[2]['weight'])
        edge_info.append(f'Weight: {edge[2]["weight"]}')  # Store weight for hover info

    # Create edges as scatter plot
    edge_trace = go.Scatter(
        x=edge_x, 
        y=edge_y, 
        line=dict(width=0.5, color='#888'),  # Fixed width for all edges
        hoverinfo='text',
        text=edge_info,
        mode='lines'
    )

    # Create nodes
    node_x = []
    node_y = []
    node_color = []
    node_size = []
    node_text = []

    for node in user_subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_color.append(partition[node])  # Color by community
        node_size.append(30 if node == user else 10 + 2 * user_subgraph.degree(node))  
        node_text.append(f'{node}<br>Degree: {user_subgraph.degree(node)}')  # Tooltip text

    # Create nodes as scatter plot
    node_trace = go.Scatter(
        x=node_x, 
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='bottom center',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=node_size,
            color=node_color,
            line_width=2)
    )

    # Combine edges and nodes into a figure
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title=f'Follower Network Graph for User: {user}',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0,l=0,r=0,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

    # Show the plot
    fig.show()

def calculate_edge_weight(likes, comments, shares, w1=1, w2=2, w3=3):
    """Calculate edge weight based on likes, comments, and shares."""
    return (w1 * likes) + (w2 * comments) + (w3 * shares)

if __name__ == "__main__":
    visualize_followers_network("qgillespie")
