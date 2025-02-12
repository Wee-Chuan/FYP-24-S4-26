import os
import uuid
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, storage
import firebase_admin

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
    print("user initialised")
    cred = credentials.Certificate(firebase_credentials) 
    firebase_admin.initialize_app(cred, {'storageBucket': 'fyp-24-s4-26.firebasestorage.app' })
    bucket = storage.bucket()

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
    def get_username_by_user_id(user_id):
        """Retrieves the username for a given user_id from Firestore."""
        try:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                return user_data.get('username', None)
            else:
                print(f"User with user_id {user_id} not found.")
                return None
        except Exception as e:
            print(f"Error retrieving username: {str(e)}")
            return None

    
    @staticmethod
    def user_exists(username, email):
        """Checks if a user with the given user_id or email already exists in Firestore."""
        # Check if username exists
        username_query = db.collection('users').where('username', '==', username).limit(1).stream()
        username_exists = any(username_query)

        # Check if email exists
        email_query = db.collection('users').where('email', '==', email).limit(1).stream()
        email_exists = any(email_query)
        
        # Return True if either user_id or email already exists
        return username_exists or email_exists

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
    def update_user(user_id, username, email=None, gender=None, age=None, niche=None, password=None):
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
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash new password
            update_data['password'] = hashed_password
        if niche is not None:
            update_data['niche'] = niche

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
    

