from entity.user import db  # Import the Firestore client from user.py
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clear_existing_data(user_id):
    """
    Clear existing test data for a specific user ID.
    """
    logging.info(f"Clearing existing test data for user_id: {user_id}")

    try:
        # Delete user document
        user_ref = db.collection('users').document(user_id)
        if user_ref.get().exists:
            user_ref.delete()
            logging.info(f"Deleted user document for user_id: {user_id}")

        # Delete engagement metrics documents
        metrics_ref = db.collection('engagement_metrics').where('user_id', '==', user_id).stream()
        for doc in metrics_ref:
            doc.reference.delete()
        logging.info(f"Deleted engagement metrics for user_id: {user_id}")
    except Exception as e:
        logging.error(f"Error clearing existing data for user_id {user_id}: {e}")


def populate_test_data(user_id, username):
    """
    Populate Firestore with test data for a given user ID.
    """
    clear_existing_data(user_id)

    try:
        # Test User Data
        test_user = {
            "user_id": user_id,
            "username": username,
            "email": f"{username}@gmail.com",
            "account_type": "influencer",
            "follower_count": 10,
            "follower_list": ["user_a", "user_b", "user_c", "user_d"],
            "following_count": 5,
            "following_list": ["user_x", "user_y", "user_z"],
            "is_suspended": False
        }

        # Engagement Metrics Data
        engagement_metrics = [
            {
                "user_id": user_id,
                "date": datetime(2024, 12, 1),
                "likes": 120,
                "comments": 45,
                "shares": 15,
                "followers": 200
            },
            {
                "user_id": user_id,
                "date": datetime(2024, 12, 2),
                "likes": 150,
                "comments": 50,
                "shares": 20,
                "followers": 220
            },
            {
                "user_id": user_id,
                "date": datetime(2024, 12, 3),
                "likes": 180,
                "comments": 60,
                "shares": 30,
                "followers": 300
            }
        ]

        # Add test user to Firestore
        logging.info(f"Adding test user '{username}'...")
        db.collection('users').document(test_user["user_id"]).set(test_user)
        logging.info(f"Test user '{username}' added successfully.")

        # Add engagement metrics to Firestore
        logging.info("Adding engagement metrics...")
        for metric in engagement_metrics:
            db.collection('engagement_metrics').add(metric)
        logging.info("Engagement metrics added successfully.")
    except Exception as e:
        logging.error(f"Error populating test data for user_id {user_id}: {e}")


def fetch_engagement_metrics(user_id):
    """
    Fetch engagement metrics for a given user ID.
    Returns the metrics as a list.
    """
    try:
        logging.info(f"Fetching engagement metrics for user_id: {user_id}")
        metrics_ref = db.collection('engagement_metrics') \
            .where('user_id', '==', user_id) \
            .order_by('date') \
            .stream()
        metrics = [doc.to_dict() for doc in metrics_ref]
        return metrics
    except Exception as e:
        logging.error(f"Error fetching engagement metrics for user_id {user_id}: {e}")
        return []


def test_engagement_metrics(user_id, username):
    """
    Fetch and display engagement metrics for a given user ID.
    """
    metrics = fetch_engagement_metrics(user_id)

    # Display the fetched metrics
    if metrics:
        logging.info(f"\nFetched Engagement Metrics for '{username}':")
        for metric in metrics:
            logging.info(metric)
    else:
        logging.warning(f"No engagement metrics found for user_id: {user_id}")


if __name__ == "__main__":
    # Test for User 1
    user_1_id = "2b740aad-0db4-43da-8653-9e5781aa2e89"  # Test User 1 ID
    user_1_username = "test_influencer"
    logging.info("\nPopulating test data for User 1...")
    populate_test_data(user_1_id, user_1_username)
    logging.info("\nTesting engagement metrics for User 1...")
    test_engagement_metrics(user_1_id, user_1_username)

    # Test for User 2
    user_2_id = "e6d5299c-2c5d-4dba-a207-1f17ab9ed907"  # Test User 2 ID
    user_2_username = "another_influencer"
    logging.info("\nPopulating test data for User 2...")
    populate_test_data(user_2_id, user_2_username)
    logging.info("\nTesting engagement metrics for User 2...")
    test_engagement_metrics(user_2_id, user_2_username)
