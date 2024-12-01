import matplotlib
matplotlib.use('Agg')

import networkx as nx
import matplotlib.pyplot as plt
import mpld3

import uuid
import sys
import os
import bcrypt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import random
from faker import Faker

fake = Faker()

import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("config/credentials.json") 
    firebase_admin.initialize_app(cred)

db = firestore.client()

class User:
    @staticmethod
    def generate_followers_following(username, num_users, follower_limit=20):
        """Generate fake followers and following lists for a new user."""
        # Create a set to ensure unique usernames
        fake_usernames = set()
        
        # Generate fake usernames until we have enough, ensuring the new user's username is included
        while len(fake_usernames) < num_users:
            fake_usernames.add(fake.user_name())
        
        # Add the new user's username to the list
        fake_usernames.add(username)

        # Convert the set back to a list
        fake_usernames = list(fake_usernames)
        
        # Generate followers
        follower_count = random.randint(1, min(follower_limit, len(fake_usernames) - 1))  # Exclude the new user
        follower_list = random.sample([user for user in fake_usernames if user != username], follower_count)

        # Generate following (you could use a similar strategy or different logic)
        following_count = random.randint(1, min(follower_limit, len(fake_usernames) - 1))  # Exclude the new user
        following_list = random.sample([user for user in fake_usernames if user != username], following_count)

        return follower_list, following_list
    
    @staticmethod
    def create_user(username, email, password, account_type, business_number=0, business_name=""):
        """Creates a new user and stores the hashed password in Firestore."""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = str(uuid.uuid4())  # Generate a unique UUID for admin reference

        user_data = {
            # 'user_id': user_id,
            'username': username,
            'email': email,  
            'password': hashed_password.decode('utf-8'),  # Store as string
            #'password': password,
            'account_type': account_type,
            'user_id': user_id,
            'is_suspended': False
        }
        # Handle fields based on account type
        if account_type == "business_analyst":
            user_data['business_name'] = business_name  # Use 'username' as 'business_name'
            user_data['business_number'] = business_number  # Store business number
            user_data['is_approved'] = False
        else:
            # Generate fake followers and following lists
            follower_list, following_list = User.generate_followers_following(username, 10)
            user_data['follower_count'] = len(follower_list)
            user_data['follower_list'] = follower_list
            user_data['following_count'] = len(following_list)
            user_data['following_list'] = following_list
            
        db.collection('users').document(user_id).set(user_data)
        print(f"User {username} with account type {account_type} created successfully.")

    @staticmethod
    def user_exists(username, email):
        """Checks if a user with the given user_id or email already exists in Firestore."""
        # Check if user_id exists
        username_exists = db.collection('users').document(username).get().exists

        # Check if email exists
        email_exists = db.collection('users').where('email', '==', email).limit(1).stream()
        
        # Return True if either user_id or email already exists
        return username_exists or any(email_exists)

    @staticmethod
    def authenticate(username, password):
        """Authenticate the user by username and password."""
        # Query Firestore to find the user by username
        users_ref = db.collection('users').where('username', '==', username).limit(1)
        doc = list(users_ref.stream())
        
        if doc:
            data = doc[0].to_dict()
            
            stored_hashed_password = data.get('password')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):  # Verify hashed password
                user_id = data.get('user_id')
                account_type = data.get('account_type')
                return True, user_id, account_type
    
        return False, None, None # Invalid password
    
    @staticmethod
    def get_profile(user_id):
        """Retrieve user profile details from Firestore."""
        try:
            doc = db.collection('users').document(user_id).get()
            print("Attempting to retrieve document...")
            print(f"Using user_id: {user_id}")

            if doc.exists:
                print(f"Docs for {user_id} retrieved ")
                data = doc.to_dict()
                return data
            else:
                return None

        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return None
        
    @staticmethod
    def update_user(user_id, username, email=None, password=None, account_type=None, business_name=None, business_number=None):
        """Updates user details in Firestore."""
        user_ref = db.collection('users').document(user_id)

        # Get the current data to ensure we don't overwrite other fields
        current_data = user_ref.get().to_dict()

        # Prepare the update data
        update_data = {}
        if username is not None:
            update_data['username'] = username
        if email is not None:
            update_data['email'] = email
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash new password
            update_data['password'] = hashed_password
        if account_type is not None:
            update_data['account_type'] = account_type
        if account_type == 'business_analyst':
            if business_name is not None:
                update_data['business_name'] = business_name
            if business_number is not None:
                update_data['business_number'] = business_number

        # Update only if there's any data to change
        if update_data:
            user_ref.update(update_data)
            print(f"User {user_id} updated successfully with new data: {update_data}")
        else:
            print(f"No updates were made for user {user_id}.")
    
    @staticmethod
    def delete_account(user_id):
        """Deletes the user account from Firestore."""
        user_ref = db.collection('users').document(user_id)

        try:
            # Check if the user exists
            if user_ref.get().exists:
                user_ref.delete()  # Delete the user's document
                print(f"User {user_id} deleted successfully.")
            else:
                print(f"User {user_id} does not exist.")
        
        except Exception as e:
            print(f"Error deleting user account: {e}")

    @staticmethod
    def visualize_followers_network(username):
        """Visualizes the followers network for the given user."""
        # Fetch user data from Firestore
        user_ref = db.collection('users').where('username', '==', username).limit(1).get()
        
        if not user_ref:
            print(f"User {username} not found in Firestore.")
            return None

        user_data = user_ref[0].to_dict()
        followers_list = user_data.get('follower_list', [])
        
        user_subgraph = nx.DiGraph()
        user_subgraph.add_node(username)
        
        # Add edges from followers to the user
        for follower in followers_list:
            user_subgraph.add_edge(follower, username)

        # Fetch followers' following lists
        for follower in followers_list:
            follower_ref = db.collection('users').where('username', '==', follower).limit(1).get()
            if follower_ref:
                follower_data = follower_ref[0].to_dict()
                follower_following_list = follower_data.get('following_list', [])
                for other_follower in followers_list:
                    if other_follower in follower_following_list:
                        user_subgraph.add_edge(follower, other_follower)

        # Set up the Matplotlib figure
        fig, ax = plt.subplots(figsize=(8.4, 6))
        pos = nx.spring_layout(user_subgraph, k=1.0)  # Adjust 'k' to change spacing

        # Draw nodes and edges
        nx.draw_networkx_edges(user_subgraph, pos, arrowstyle='-|>', arrowsize=15, width=0.5, edge_color='black')
        node_colors = ['red' if node == username else 'blue' for node in user_subgraph.nodes()]
        nx.draw_networkx_nodes(user_subgraph, pos, node_color=node_colors, node_size=500)
        nx.draw_networkx_labels(user_subgraph, pos, font_size=12, font_family='sans-serif')

        ax.axis('off')  # Turn off the axis
        ax.grid(False)
        plt.tight_layout()  # Adjust layout

        # Use mpld3 to create an interactive plot
        interactive_plot = mpld3.fig_to_html(fig)
        plt.close(fig)  # Close the plot to avoid display issues

        return interactive_plot