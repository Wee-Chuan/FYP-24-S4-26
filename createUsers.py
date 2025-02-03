import csv, re, json, os, random
from collections import defaultdict
from postclasses import Comment, User
import networkx as nx
from pyvis.network import Network

def extract_parent_id_from_url(url):
    """Extract the parent ID from the URL."""
    if url:
        match = re.search(r'/c/(\d+)', url)
        if match:
            return match.group(1)
    return None

def process_comment_data(input_file):
    users = []
    user_dict = {}
    comment_dict = {}

    with open(input_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames

        for row in reader:
            try:
                # Extract fields from the CSV row
                username = row['ownerUsername'].strip()
                text = row['text'].strip()
                likes = int(row['likesCount']) if row['likesCount'] else 0
                replies_count = int(row['repliesCount']) if row['repliesCount'] else 0
                comment_id = row['id']
                timestamp = row['timestamp']
                parent_url = row['parentCommentUrl'].strip() if row['parentCommentUrl'] else None

                # Create Comment object
                comment = Comment(text, likes, replies_count, comment_id, timestamp)
                comment.username = username

                # Extract parent ID from the parent URL (if available)
                parent_id = extract_parent_id_from_url(parent_url)
                comment.parent_id = parent_id

                # Add comment to the user dictionary
                if username not in user_dict:
                    user_dict[username] = User(username)
                    users.append(user_dict[username])

                user_dict[username].add_comment(comment)
                comment_dict[comment_id] = comment

            except KeyError as e:
                print(f"Missing column: {e}")
            except ValueError as e:
                print(f"Invalid value in data: {e}")

    return users

def write_users_to_json(users, output_file):
    users_data = {}

    for user in users:
        user_data = {
            'username': user.username,
            'comments': []
        }

        for comment in user.comments:
            comment_data = comment.to_dict()
            user_data['comments'].append(comment_data)

        users_data[user.username] = user_data

    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(users_data, json_file, ensure_ascii=False, indent=4)

    print(f"User data has been written to {output_file}")

def create_user_json():
    input_file = 'data/postCommentData.csv'  # Input CSV file with comment data
    output_file = 'data/users.json'  # Output JSON file to store user data

    users = process_comment_data(input_file)
    write_users_to_json(users, output_file)

# Function to extract conversations from the user data
def create_conversations(users_data):
    conversations = {}
    conversation_counter = 0  # A counter for generating unique conversation IDs

    comment_id_to_conversation = {}  # To track which comment belongs to which conversation

    for username, user_data in users_data.items():  # Accessing user_data properly
        for comment in user_data['comments']:
            # Add the username to the comment
            comment['username'] = username  # Attach the username to the comment
            
            # Check if the comment is a parent (has no parent_id) or a reply (has a parent_id)
            if comment['parent_id'] is None:
                # It's a parent comment, create a new conversation
                conversation_counter += 1
                conversation_id = f"conversation_{conversation_counter}"
                conversations[conversation_id] = {
                    'conversation_id': conversation_id,
                    'comments': [comment]  # Start with the parent comment
                }
                comment_id_to_conversation[comment['comment_id']] = conversation_id
            else:
                # It's a reply, add it to the corresponding conversation
                parent_conversation_id = comment_id_to_conversation.get(comment['parent_id'])
                if parent_conversation_id:
                    conversations[parent_conversation_id]['comments'].append(comment)
                else:
                    # If the parent is not found (which shouldn't happen), we create a new conversation
                    conversation_counter += 1
                    conversation_id = f"conversation_{conversation_counter}"
                    conversations[conversation_id] = {
                        'conversation_id': conversation_id,
                        'comments': [comment]
                    }
                    comment_id_to_conversation[comment['comment_id']] = conversation_id

    # Now, we will sort the comments in each conversation by timestamp
    for conversation_id, conversation in conversations.items():
        conversation['comments'] = sorted(conversation['comments'], key=lambda x: x['timestamp'])

    return conversations

def make_convo_file():
    # Load the users data (assuming the 'users.json' file is structured as shown)
    with open('data/users.json', 'r', encoding='utf-8') as file:
        users_data = json.load(file)

    # Create conversations from the user data
    conversations = create_conversations(users_data)

    # Save the conversations to a JSON file
    with open('data/conversations.json', 'w', encoding='utf-8') as file:
        json.dump(conversations, file, ensure_ascii=False, indent=4)

    print("Conversations have been saved to conversations.json.")

# Load the conversations.json data
def load_conversations(convo_file):
    with open(convo_file, 'r', encoding='utf-8') as file:
        return json.load(file)

# Generate a random color
def generate_random_color():
    return f"rgb({random.randint(100, 255)}, {random.randint(100, 255)}, {random.randint(100, 255)})"

# Function to generate random colors
def generate_random_color():
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def create_conversation_tree(conversations_data):
    # Create a PyVis network
    net = Network(notebook=True)

    created_nodes = set()  # To track the nodes we've already added
    conversation_colors = {}  # Store colors for each conversation

    # Create nodes for comments only
    for convo_id, convo_data in conversations_data.items():
        comments = convo_data["comments"]

        # Only process conversations with 3 or more comments
        if len(comments) >= 3:
            # Assign a unique color for each conversation
            if convo_id not in conversation_colors:
                conversation_colors[convo_id] = generate_random_color()

            # First, add the parent nodes (root comments)
            for comment in comments:
                if not comment["parent_id"]:  # This is a root comment, no parent
                    comment_id = comment["comment_id"]
                    net.add_node(
                        comment_id,
                        label=f"Comment {comment_id}",
                        title=f"Community: {convo_id} \nComment: {comment['text']}",
                        size=10,
                        color=conversation_colors[convo_id]
                    )
                    created_nodes.add(comment_id)

            # Add child nodes and links
            for comment in comments:
                if comment["parent_id"]:
                    comment_id = comment["comment_id"]
                    parent_id = comment["parent_id"]

                    if comment_id not in created_nodes:
                        net.add_node(
                            comment_id,
                            label=f"Comment {comment_id}",
                            title=f"Community: {convo_id}<br>{comment['text']}",
                            size=10,
                            color=conversation_colors[convo_id]
                        )
                        created_nodes.add(comment_id)

                    if parent_id not in created_nodes:
                        net.add_node(
                            parent_id,
                            label=f"Comment {parent_id}",
                            title=f"Community: {convo_id}<br>Unknown Parent",
                            size=10,
                            color=conversation_colors[convo_id]
                        )
                        created_nodes.add(parent_id)

                    net.add_edge(parent_id, comment_id)

    # Ensure the file is saved in the static directory
    static_folder = os.path.join(os.getcwd(), 'static')
    os.makedirs(static_folder, exist_ok=True)
    output_path = os.path.join(static_folder, "comment_tree.html")

    # Save the visualization
    net.show(output_path)

    # Modify the generated HTML file to ensure proper DOCTYPE
    with open(output_path, "r") as file:
        html_content = file.read()

    # Add the DOCTYPE declaration at the beginning of the HTML content
    html_content = "<!DOCTYPE html>\n" + html_content

    # Save the modified HTML content back to the file
    with open(output_path, "w") as file:
        file.write(html_content)

    print(f"The comment tree has been saved to {output_path}")

def create_top_users_table(conversations_file, output_html_file):
    # Load the JSON data
    with open(conversations_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Initialize the graph
    G = nx.Graph()
    G.add_node('post')

    comment_user_map = {}
    user_conversations = defaultdict(list)
    user_comments = defaultdict(list)

    for conversation_id, conversation_data in data.items():
        comments = conversation_data['comments']

        for comment in comments:
            username = comment['username']
            comment_id = comment['comment_id']
            parent_id = comment['parent_id']
            likes = comment.get('likes', 0)  # Default to 0 if 'likes' key is missing

            # Add the user to the graph and the 'post' node connection
            G.add_node(username)
            G.add_edge('post', username)

            # Map comment to user
            comment_user_map[comment_id] = username

            # Track which conversations each user is in
            if conversation_id not in user_conversations[username]:
                user_conversations[username].append(conversation_id)

            # Track comments and likes for each user
            user_comments[username].append(f"{comment['text']} (Likes: {likes})")

            # Add edges between users if there's a reply relationship
            if parent_id and parent_id in comment_user_map:
                parent_user = comment_user_map[parent_id]
                if username != parent_user:
                    G.add_edge(username, parent_user)

    # Centrality analysis (degree centrality for simplicity)
    centrality = nx.degree_centrality(G)

    # Sort nodes by centrality in descending order, excluding the 'post' node
    sorted_nodes = [node for node, _ in sorted(centrality.items(), key=lambda x: x[1], reverse=True) if node != 'post']

    # Get the top 5 most central nodes
    top_5_central_nodes = sorted_nodes[:5]

    # Build the HTML table
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Top 5 Central Users</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9; 
                margin: 2em;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                word-wrap: break-word;
                max-width: 300px;
            }
            th {
                background-color: #04647a;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f0fdfa;
            }
            tr:hover {
                background-color: #b7e4e5;
            }
            h1 {
                text-align: center;
                color: #04647a;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Top 5 Central Users in the Conversation Graph</h1>
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Comments</th>
                        <th>Conversations</th>
                    </tr>
                </thead>
                <tbody>
    """

    for user in top_5_central_nodes:
        user_comment_list = "<br>".join(user_comments[user])
        conversation_list = ", ".join(user_conversations[user])

        html_content += f"""
        <tr>
            <td>{user}</td>
            <td>{user_comment_list}</td>
            <td>{conversation_list}</td>
        </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    # Save the HTML file
    with open(output_html_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"Table saved to {output_html_file}")

def show_network():
    conversation_file = 'data/conversations.json'  # Input JSON file containing conversations data
    conversations_data = load_conversations(conversation_file)
    create_conversation_tree(conversations_data)
    create_top_users_table('data/conversations.json', 'static/top_users_table.html') 

create_top_users_table('data/conversations.json', 'static/top_users_table.html') 

