import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime

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

db = firestore.client()

def update_follower_hist(user_id, platform, new_history):
    """
    Deletes the current follower history for a user and uploads a new one
    in the format: follower_history (collection) > user_id (document) > history (subcollection).
    """
    try:
        # Reference to the Firestore collection
        user_doc_ref = db.collection(platform).document(user_id)
        
        # Check if the user document exists
        user_doc = user_doc_ref.get()
        if not user_doc.exists:
            print(f"User with ID {user_id} does not exist.")
            return False
        
        history_collection_ref = user_doc_ref.collection('history')

        # Fetch all existing documents in the user's history subcollection
        docs = history_collection_ref.stream()

        # Initialize a batch for atomic writes
        batch = db.batch()

        # Delete all existing history documents
        for doc in docs:
            batch.delete(doc.reference)

        # Add new history records
        for record in new_history:
            # Validate the date format
            try:
                datetime.strptime(record['date'], "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format in new history: {record['date']}")

            # Add the new document to the batch
            new_doc_ref = history_collection_ref.document()
            batch.set(new_doc_ref, {
                'date': record['date'],
                'follower_count': record['follower_count']
            })

        # Commit the batch
        batch.commit()
        print(f"Follower history for user_id {user_id} updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating follower history: {e}")
        return False

if __name__ == "__main__":
    new_history = [
            # Data for 2022
            {'date': '2022-01-01', 'follower_count': 50},
            {'date': '2022-02-01', 'follower_count': 55},
            {'date': '2022-03-01', 'follower_count': 60},
            {'date': '2022-04-01', 'follower_count': 65},
            {'date': '2022-05-01', 'follower_count': 70},
            {'date': '2022-06-01', 'follower_count': 75},
            {'date': '2022-07-01', 'follower_count': 80},
            {'date': '2022-08-01', 'follower_count': 85},
            {'date': '2022-09-01', 'follower_count': 90},
            {'date': '2022-10-01', 'follower_count': 95},
            {'date': '2022-11-01', 'follower_count': 100},
            {'date': '2022-12-01', 'follower_count': 110},

            # Data for 2023
            {'date': '2023-01-01', 'follower_count': 120},
            {'date': '2023-02-01', 'follower_count': 125},
            {'date': '2023-03-01', 'follower_count': 130},
            {'date': '2023-04-01', 'follower_count': 135},
            {'date': '2023-05-01', 'follower_count': 140},
            {'date': '2023-06-01', 'follower_count': 145},
            {'date': '2023-07-01', 'follower_count': 150},
            {'date': '2023-08-01', 'follower_count': 155},
            {'date': '2023-09-01', 'follower_count': 160},
            {'date': '2023-10-01', 'follower_count': 165},
            {'date': '2023-11-01', 'follower_count': 170},
            {'date': '2023-12-01', 'follower_count': 175},

            # Data for 2024
            {'date': '2024-01-01', 'follower_count': 180},
            {'date': '2024-02-01', 'follower_count': 185},
            {'date': '2024-03-01', 'follower_count': 190},
            {'date': '2024-04-01', 'follower_count': 195},
            {'date': '2024-05-01', 'follower_count': 200},
            {'date': '2024-06-01', 'follower_count': 205},
            {'date': '2024-07-01', 'follower_count': 300},
            {'date': '2024-08-01', 'follower_count': 215},
            {'date': '2024-09-01', 'follower_count': 220},
            {'date': '2024-10-01', 'follower_count': 225},
            {'date': '2024-11-01', 'follower_count': 230},
            {'date': '2024-12-01', 'follower_count': 500}
        ]

    user_id = "6512d5cb-066c-45f6-b6bc-4566698aed82"
    platform = "twitter_social_accounts"
    success = update_follower_hist(user_id, platform, new_history)

    if success:
        print("Follower history replaced successfully.")
    else:
        print("Failed to update follower history.")