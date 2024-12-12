import os
import json
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

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

# Get Firestore client
db = firestore.client()

# Define the Firestore collection to upload to
collection_name = 'user_interactions'  # You can change this to the collection you want

# Read the JSON data from file
with open('interaction_data.json', 'r') as file:
    interaction_data = json.load(file)

# Upload each user's interaction data from the JSON to Firestore
for user in interaction_data:
    try:
        # Reference to the user document by username
        user_ref = db.collection(collection_name).document(user['username'])
        
        # Set the user's interaction data in Firestore
        user_ref.set({
               'username' : user.get('username', []),
            'followers_list': user.get('followers_list', []),
            'following_list': user.get('following_list', []),
            'interactions': user.get('interactions', {}),
            'hashtags': user.get('hashtags', [])
        })
        
        print(f"Added user: {user['username']}")
    except Exception as e:
        print(f"Error adding user {user['username']}: {e}")
