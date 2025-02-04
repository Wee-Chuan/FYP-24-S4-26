import os
import sys
import uuid
import random
import json
import bcrypt
from datetime import datetime, timedelta
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpld3
import networkx as nx
import pandas as pd
import numpy as np

from bertopic import BERTopic
from wordcloud import WordCloud
from faker import Faker
from dotenv import load_dotenv
from transformers import pipeline
import torch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.decomposition import NMF

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Ensure NLTK Vader Lexicon is available
nltk.download('vader_lexicon', quiet=True)

# Load AI Summarization Model (Runs Locally)
device = "cuda" if torch.cuda.is_available() else "cpu"
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0 if torch.cuda.is_available() else -1)

nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Load environment variables
load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests

# Firebase Initialization
if not firebase_admin._apps:
    # Prepare the credentials dictionary from environment variables
    firebase_credentials = {
        "type": os.getenv("GOOGLE_CLOUD_TYPE"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY").replace('\\n', '\n'),  # Ensure newlines are correctly formatted
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

db = firestore.client()

class User:    
    @staticmethod
    def create_user(username, email, gender, age, niche, password, account_type):
        """Creates a new user and stores the hashed password in Firestore."""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = str(uuid.uuid4())  # Generate a unique UUID for admin reference

        user_data = {
            'username': username,
            'email': email,  
            'gender': gender,
            'age': age,
            'niche': niche,
            'password': hashed_password.decode('utf-8'),  # Store as string
            'account_type': account_type,
            'user_id': user_id,
            'is_suspended': False,
        }
            
        db.collection('users').document(user_id).set(user_data)

        print(f"User {username} with account type {account_type} created successfully.")

    @staticmethod
    def user_exists(username, email):
        """Checks if a user with the given user_id or email already exists in Firestore."""
        # Check if user_id exists
        username_exists = db.collection('users').document(username).get().exists

        # Check if email exists
        email_exists = db.collection('users').where(field_path='email', op_string='==', value=email).limit(1).stream()
        
        # Return True if either user_id or email already exists
        return username_exists or any(email_exists)

    @staticmethod
    def authenticate(username, password):
        """Authenticate the user by username and password."""
        # Query Firestore to find the user by username
        users_ref = db.collection('users').where(field_path='username', op_string='==', value=username).limit(1)
        doc = list(users_ref.stream())
        
        if doc:
            data = doc[0].to_dict()

            # Check if user is suspended
            is_suspended = data.get('is_suspended', False)
            
            stored_hashed_password = data.get('password')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):  # Verify hashed password
                user_id = data.get('user_id')
                account_type = data.get('account_type')
                return True, user_id, account_type, is_suspended
    
        return False, None, None, False # Invalid password
    
    @staticmethod
    def get_profile(user_id):
        """Retrieve user profile details from Firestore."""
        try:
            doc = db.collection('users').document(user_id).get()
            print("Attempting to retrieve user profile...")
            print(f"Using user_id: {user_id}")

            if doc.exists:
                print(f"User profile for {user_id} retrieved ")
                data = doc.to_dict()
                return data
            else:
                return None

        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return None
        
    @staticmethod
    def update_user(user_id, username, email=None, gender=None, age=None, niche=None, password=None, account_type=None):
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
        if gender is not None:
            update_data['gender'] = gender
        if age is not None:
            update_data['age'] = age
        if niche is not None:
            update_data['niche'] = niche
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash new password
            update_data['password'] = hashed_password
        if account_type is not None:
            update_data['account_type'] = account_type

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
    
    #=======================KEVIN======================================================================#
    @staticmethod
    def process_engagement_data(csv_path):
        """
        Reads engagement data, filters required columns, and creates engagement_metrics.csv.
        Returns post URLs and engagement data.
        """
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError("CSV file not found!")

            df = pd.read_csv(csv_path)

            # Required columns
            required_columns = {'id', 'likesCount', 'repliesCount', 'text', 'owner/is_verified', 'postUrl'}
            missing_columns = required_columns - set(df.columns)

            if missing_columns:
                raise ValueError(f"CSV is missing required columns: {missing_columns}")

            # Filter and rename columns
            df_filtered = df[list(required_columns)].rename(columns={
                'likesCount': 'likes',
                'repliesCount': 'comments',
                'owner/is_verified': 'verified'
            })

            # Compute engagement score
            df_filtered["engagement_score"] = df_filtered["likes"] + df_filtered["comments"]

            # Save processed engagement data
            df_filtered.to_csv("engagement_metrics.csv", index=False)

            # Get unique post URLs for selection
            post_urls = df_filtered["postUrl"].dropna().unique().tolist()

            return post_urls, df_filtered.to_dict(orient="records")

        except Exception as e:
            print(f"❌ Error processing engagement CSV: {e}")
            return [], []

    @staticmethod
    def get_post_engagement(csv_path, post_url):
        """
        Retrieves engagement data for a single post.
        """
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError("CSV file not found!")

            df = pd.read_csv(csv_path)
            post_data = df[df["postUrl"] == post_url]

            if post_data.empty:
                return []

            return post_data.to_dict(orient="records")

        except Exception as e:
            print(f"❌ Error retrieving post engagement: {e}")
            return []

    @staticmethod
    def generate_ai_summary(post_data):
        """
        Generates AI summary based on engagement metrics with more depth.
        """
        try:
            if isinstance(post_data, list) and len(post_data) > 0:
                post_data = post_data[0]  # Take the first post entry
            elif isinstance(post_data, dict):
                pass  # Already in dictionary format
            else:
                return "⚠️ AI Summary not available (Invalid post data format)."

            # Extract engagement data
            post_text = post_data.get("text", "No caption available")
            likes = post_data.get("likesCount", 0)
            comments = post_data.get("repliesCount", 0)
            engagement_score = likes + comments
            verified = "✅ Verified Account" if post_data.get("owner/is_verified", False) else "❌ Non-Verified Account"

            # Create structured input for AI summarization
            summary_input = f"""
            Post Analysis:
            - {verified}
            - Likes: {likes}
            - Comments: {comments}
            - Engagement Score: {engagement_score}
            - Caption Preview: {post_text[:300]}...  # Limit text for AI input
            - Observations:
                * Higher engagement means better reach.
                * Verified accounts typically get more engagement.
                * Posts with questions or emotional words tend to perform better.
            """

            # Generate detailed summary with increased `max_length`
            summary = summarizer(summary_input, max_length=120, min_length=50, do_sample=False)[0]["summary_text"]

            # Final formatted summary
            final_summary = (
                f"📊 **Post Engagement Analysis**\n"
                f"📌 **Account Status:** {verified}\n"
                f"👍 **Likes:** {likes} | 💬 **Comments:** {comments} | 🔥 **Engagement Score:** {engagement_score}\n"
                f"📝 **Caption Preview:** \"{post_text[:150]}...\"\n\n"
                f"🔍 **AI Insights:** {summary}\n\n"
                
            )

            return final_summary

        except Exception as e:
            print(f"❌ Error generating AI summary: {e}")
            return "⚠️ AI Summary not available."


    @staticmethod
    def extract_most_used_emojis(comments):
        """
        Extracts the most frequently used emojis from comments.
        """
        try:
            emoji_list = []
            for comment in comments.dropna():
                emoji_list.extend([char for char in comment if char in emoji.EMOJI_DATA])

            return dict(Counter(emoji_list).most_common(10))

        except Exception as e:
            print(f"❌ Error extracting emojis: {e}")
            return {}

    @staticmethod
    def generate_wordcloud(comments):
        """
        Generates a word cloud from comment text.
        """
        try:
            text = " ".join(comments.dropna())
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
            wordcloud.to_file("static/wordcloud.png")
            return "static/wordcloud.png"

        except Exception as e:
            print(f"❌ Error generating word cloud: {e}")
            return None
    #===================== Ratings and Reviews ==============================#
    def save_rate_and_review(user_id, rating, category, review, username):
        """
        Add ratings and reviews into Firestore.
        """
        try:
            # Get a reference to the 'ratings_and_reviews' collection
            user_ref = db.collection('ratings_and_reviews').document(user_id)

            # Set the user data (user_id, username) in the user document
            user_ref.set({
                'user_id': user_id,
                'username': username
            })

            # Get a reference to the 'ratings_and_reviews' collection
            reviews_ref = user_ref.collection('reviews')

            # Add the rating and review as a new document in the 'reviews' subcollection
            reviews_ref.add({
                'rating': rating,
                'category': category,
                'review': review,
                'date': datetime.now(),
                'is_selected': False
            })
        except Exception as e:
            print(f"Error saving review: {e}")
            return False
        return True
    
    @staticmethod
    def get_influencer_data():
        """Retrieves influencer data from Firebase."""
        influencer_data = []
        try:
            # Assuming degree_of_centrality is a collection in Firebase
            influencers_ref = db.collection('degree_of_centrailty').stream()

            # Loop through the collection to fetch the data
            for influencer in influencers_ref:
                data = influencer.to_dict()
                influencer_info = {
                    'username': data.get('username'),
                    'follower_count': data.get('follower_count'),
                    'following_count': data.get('following_count'),
                    'uid': data.get('user_id')
                }
                influencer_data.append(influencer_info)

            return influencer_data
        except Exception as e:
            print(f"Error retrieving influencer data: {e}")
            return []

    @staticmethod
    def calculate_centrality():
        """Calculates centrality for the influencers in the network."""
        influencer_data = User.get_influencer_data()
        
        if not influencer_data:
            print("No influencer data available.")
            return None

        # Create a directed graph (since followers follow influencers)
        G = nx.DiGraph()

        # Add nodes and edges based on the influencer data
        for influencer in influencer_data:
            username = influencer['username']
            follower_count = influencer['follower_count']
            following_count = influencer['following_count']
            
            # Add the influencer node (itself) with follower and following counts as attributes
            G.add_node(username, follower_count=follower_count, following_count=following_count)
            
            # Assume each influencer follows others in the dataset (simplified relationship)
            for other_influencer in influencer_data:
                if other_influencer['username'] != username:
                    G.add_edge(username, other_influencer['username'])  # Add directed edge from username to others

        # Calculate centrality measures
        centrality = {}
        centrality['degree_centrality'] = nx.degree_centrality(G)  # Degree centrality
        centrality['betweenness_centrality'] = nx.betweenness_centrality(G)  # Betweenness centrality
        centrality['closeness_centrality'] = nx.closeness_centrality(G)  # Closeness centrality
        centrality['eigenvector_centrality'] = nx.eigenvector_centrality(G)  # Eigenvector centrality
        
        return centrality
    
    
    @staticmethod

    def get_ranked_influencers():
        """Fetches influencer data and ranks them based on centrality."""
        influencers = User.get_influencer_data()
        
        if not influencers:
            print("No influencer data to rank.")
            return []

        # Step 1: Calculate raw centrality score for each influencer
        for influencer in influencers:
            # Raw centrality score (un-normalized score)
            influencer["unormalized_score"] = User.calculate_centrality_for_influencer(influencer)

        # Step 2: Find the maximum raw centrality score
        max_score = max(influencer["unormalized_score"] for influencer in influencers)

        # Step 3: Normalize the scores (top influencer gets a score of 1)
        for influencer in influencers:
            if max_score != 0:  # Prevent division by zero if all scores are the same
                influencer["centrality_score"] = round(influencer["unormalized_score"] / max_score, 3)
            else:
                influencer["centrality_score"] = 0  # If all scores are 0, set to 0

        # Step 4: Sort influencers by normalized centrality score (descending order)
        sorted_influencers = sorted(influencers, key=lambda x: x["centrality_score"], reverse=True)
        
        return sorted_influencers
    
    
    @staticmethod
    def calculate_centrality_for_influencer(influencer):
        """Calculates a simplified centrality score for an individual influencer."""
        # Simplified centrality based on follower and following counts
        follower_count = influencer['follower_count']
        following_count = influencer['following_count']
        
        # You can define a more sophisticated formula based on the specific centrality measure you want
        centrality_score = follower_count - following_count  # Example formula
        return centrality_score

    @staticmethod
    def compare_with_top_user(user_id):
        """Compares the centrality of a user with the top influencer."""
        ranked_influencers = User.get_ranked_influencers()

        # Ensure there are influencers in the list
        if not ranked_influencers:
            print("No ranked influencers available.")
            return None, None, None

        # Get the top influencer (the one with the highest centrality score)
        top_user = ranked_influencers[0]

        # Find the influencer with the given user_id
        user = next((u for u in ranked_influencers if u["username"] == user_id), None)

        if user:
            # Calculate the score difference between the top influencer and the user
            score_diff = top_user["centrality_score"] - user["centrality_score"]
            return top_user, user, score_diff
        else:
            print(f"User with ID {user_id} not found.")
            return None, None, None
    