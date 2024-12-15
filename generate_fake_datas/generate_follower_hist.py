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
                'follower_count': record['follower_count'],
                'likes': record['likes'],
                'comments': record['comments'],
                'shares': record['shares']
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
        # {'date': '2022-01-01', 'follower_count': 50, 'likes': 10, 'comments': 2, 'shares': 1},
        # {'date': '2022-02-01', 'follower_count': 55, 'likes': 15, 'comments': 3, 'shares': 2},
        # {'date': '2022-03-01', 'follower_count': 60, 'likes': 20, 'comments': 4, 'shares': 3},
        # {'date': '2022-04-01', 'follower_count': 65, 'likes': 25, 'comments': 5, 'shares': 4},
        # {'date': '2022-05-01', 'follower_count': 70, 'likes': 30, 'comments': 6, 'shares': 5},
        # {'date': '2022-06-01', 'follower_count': 75, 'likes': 35, 'comments': 7, 'shares': 6},
        # {'date': '2022-07-01', 'follower_count': 80, 'likes': 40, 'comments': 8, 'shares': 7},
        # {'date': '2022-08-01', 'follower_count': 85, 'likes': 45, 'comments': 9, 'shares': 8},
        # {'date': '2022-09-01', 'follower_count': 90, 'likes': 50, 'comments': 10, 'shares': 9},
        # {'date': '2022-10-01', 'follower_count': 95, 'likes': 55, 'comments': 11, 'shares': 10},
        # {'date': '2022-11-01', 'follower_count': 100, 'likes': 60, 'comments': 12, 'shares': 11},
        # {'date': '2022-12-01', 'follower_count': 110, 'likes': 65, 'comments': 13, 'shares': 12},

        # Data for 2023
        {'date': '2023-01-01', 'follower_count': 120, 'likes': 70, 'comments': 14, 'shares': 13},
        {'date': '2023-02-01', 'follower_count': 125, 'likes': 75, 'comments': 15, 'shares': 14},
        {'date': '2023-03-01', 'follower_count': 130, 'likes': 80, 'comments': 16, 'shares': 15},
        {'date': '2023-04-01', 'follower_count': 135, 'likes': 85, 'comments': 17, 'shares': 16},
        {'date': '2023-05-01', 'follower_count': 140, 'likes': 90, 'comments': 18, 'shares': 17},
        {'date': '2023-06-01', 'follower_count': 145, 'likes': 95, 'comments': 19, 'shares': 18},
        {'date': '2023-07-01', 'follower_count': 150, 'likes': 100, 'comments': 20, 'shares': 19},
        {'date': '2023-08-01', 'follower_count': 155, 'likes': 105, 'comments': 21, 'shares': 20},
        {'date': '2023-09-01', 'follower_count': 160, 'likes': 110, 'comments': 22, 'shares': 21},
        {'date': '2023-10-01', 'follower_count': 165, 'likes': 115, 'comments': 23, 'shares': 22},
        {'date': '2023-11-01', 'follower_count': 170, 'likes': 120, 'comments': 24, 'shares': 23},
        {'date': '2023-12-01', 'follower_count': 175, 'likes': 125, 'comments': 25, 'shares': 24},

        # Data for 2024
        {'date': '2024-01-01', 'follower_count': 180, 'likes': 130, 'comments': 26, 'shares': 25},
        {'date': '2024-02-01', 'follower_count': 185, 'likes': 135, 'comments': 27, 'shares': 26},
        {'date': '2024-03-01', 'follower_count': 190, 'likes': 140, 'comments': 28, 'shares': 27},
        {'date': '2024-04-01', 'follower_count': 195, 'likes': 145, 'comments': 29, 'shares': 28},
        {'date': '2024-05-01', 'follower_count': 200, 'likes': 150, 'comments': 30, 'shares': 29},
        {'date': '2024-06-01', 'follower_count': 205, 'likes': 155, 'comments': 31, 'shares': 30},
        {'date': '2024-07-01', 'follower_count': 210, 'likes': 160, 'comments': 32, 'shares': 31},
        {'date': '2024-08-01', 'follower_count': 215, 'likes': 165, 'comments': 33, 'shares': 32},
        {'date': '2024-09-01', 'follower_count': 220, 'likes': 170, 'comments': 34, 'shares': 33},
        {'date': '2024-10-01', 'follower_count': 225, 'likes': 175, 'comments': 35, 'shares': 34},
        {'date': '2024-11-01', 'follower_count': 230, 'likes': 180, 'comments': 36, 'shares': 35},
        {'date': '2024-12-01', 'follower_count': 500, 'likes': 200, 'comments': 50, 'shares': 40},
    ]

    user_id = "0da5a462-1a7b-4b35-84be-04aa6bb29e72"
    platform = "twitter_social_accounts"
    success = update_follower_hist(user_id, platform, new_history)

    if success:
        print("Follower history replaced successfully.")
    else:
        print("Failed to update follower history.")