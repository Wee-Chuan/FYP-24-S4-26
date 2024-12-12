from entity.user import db  # Import the Firestore client from user.py
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)


def clear_existing_data(user_id):
    """
    Clear existing test data for a specific user ID.
    """
    logging.info("Clearing existing test data...")

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


def populate_test_data():
    """
    Populate Firestore with test data for users and engagement_metrics collections.
    """
    user_id = "2b740aad-0db4-43da-8653-9e5781aa2e89"  # Fixed test user ID
    clear_existing_data(user_id)  # Clear existing data first

    # Test User Data
    test_user = {
        "user_id": user_id,
        "username": "test_influencer",
        "email": "test_influencer@gmail.com",
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
    ]

    # Add test user to Firestore
    logging.info("Adding test user...")
    db.collection('users').document(test_user["user_id"]).set(test_user)
    logging.info("Test user added successfully.")

    # Add engagement metrics to Firestore
    logging.info("Adding engagement metrics...")
    for metric in engagement_metrics:
        db.collection('engagement_metrics').add(metric)
    logging.info("Engagement metrics added successfully.")


def test_engagement_metrics(user_id):
    """
    Fetch and display engagement metrics for a given user ID.
    """
    try:
        # Attempt to fetch data with ordering using `where` and `order_by`
        logging.info("Fetching engagement metrics with ordering...")
        metrics_ref = db.collection('engagement_metrics') \
            .where('user_id', '==', user_id) \
            .order_by('date') \
            .stream()
        metrics = [doc.to_dict() for doc in metrics_ref]
    except Exception as e:
        # Handle cases where an index is missing
        logging.warning("Index missing for query with ordering. Falling back to unordered fetch.")
        logging.error(f"Error: {e}")
        metrics_ref = db.collection('engagement_metrics').where('user_id', '==', user_id).stream()
        metrics = sorted([doc.to_dict() for doc in metrics_ref], key=lambda x: x['date'])

    # Display the fetched metrics
    if metrics:
        logging.info("\nFetched Engagement Metrics:")
        for metric in metrics:
            logging.info(metric)
    else:
        logging.warning("No engagement metrics found for this user.")


def add_engagement_metrics_for_brian():
    """
    Adds test engagement metrics for the user 'brian'.
    """
    user_id = "e6d5299c-2c5d-4dba-a207-1f17ab9ed907"  # User ID for 'brian'

    # Engagement metrics data
    engagement_metrics = [
        {
            "user_id": user_id,
            "date": datetime(2024, 12, 1),
            "likes": 100,
            "comments": 50,
            "shares": 20,
            "followers": 300,
        },
        {
            "user_id": user_id,
            "date": datetime(2024, 12, 2),
            "likes": 120,
            "comments": 60,
            "shares": 25,
            "followers": 320,
        },
        {
            "user_id": user_id,
            "date": datetime(2024, 12, 3),
            "likes": 140,
            "comments": 70,
            "shares": 30,
            "followers": 340,
        },
    ]

    # Add metrics to Firestore
    logging.info(f"Adding engagement metrics for user: {user_id}")
    for metric in engagement_metrics:
        db.collection('engagement_metrics').add(metric)
    logging.info("Engagement metrics added successfully.")


if __name__ == "__main__":
    # Populate test data for generic testing
    logging.info("Populating test data...")
    populate_test_data()

    # Add engagement metrics for a specific user ('brian')
    logging.info("Adding engagement metrics for 'brian'...")
    add_engagement_metrics_for_brian()

    # Test fetching engagement metrics for the initial test user
    logging.info("\nTesting engagement metrics fetching for the test user...")
    test_user_id = "2b740aad-0db4-43da-8653-9e5781aa2e89"  # ID for the test user
    test_engagement_metrics(test_user_id)

    # Optional: Test engagement metrics fetching for 'brian'
    logging.info("\nTesting engagement metrics fetching for 'brian'...")
    brian_user_id = "e6d5299c-2c5d-4dba-a207-1f17ab9ed907"  # ID for 'brian'
    test_engagement_metrics(brian_user_id)
