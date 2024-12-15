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

def upload_to_firestore_from_json(json_file):
    """
    Reads a JSON file and uploads its content to Firestore as a collection.
    
    Args:
        json_file (str): Path to the JSON file.
    """
    try:
        # Read the JSON data from the file
        with open(json_file, 'r') as file:
            interaction_data = json.load(file)

        # Upload each user's interaction data from the JSON to Firestore
        for user in interaction_data:
            try:
                # Reference to the user document by username
                user_ref = db.collection(collection_name).document(user['username'])

                # Ensure that hashtags are included in the data, even if empty
                hashtags = user.get('hashtags', [])

                # Set the user's interaction data in Firestore
                user_ref.set({
                    'username': user.get('username', []),
                    'followers_list': user.get('followers_list', []),
                    'following_list': user.get('following_list', []),
                    'interactions': user.get('interactions', {}),
                    'hashtags': hashtags  # Ensure hashtags are included
                })

                print(f"Uploaded user: {user['username']} to Firestore")
            except Exception as e:
                print(f"Error uploading user {user['username']}: {e}")

    except FileNotFoundError:
        print(f"Error: The file {json_file} was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Ensure the file is properly formatted.")

# Specify the JSON file to upload
json_file = "0network.json"  # Replace with your JSON file name

# Call the function to upload the JSON data to Firestore
upload_to_firestore_from_json(json_file)

print(f"Data from {json_file} has been uploaded to Firestore.")
