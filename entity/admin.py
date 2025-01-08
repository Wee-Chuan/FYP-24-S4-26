import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os

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

class Admin:
    @staticmethod
    def get_all_users():
        """Retrieve all user profiles for admin view."""
        try:
            users = db.collection('users').stream()
            user_list = []

            for user in users:
                user_data = user.to_dict()
                # Exclude admins
                if user_data.get('account_type') != 'admin':
                    user_list.append(user_data)
        
            return user_list
        except Exception as e:
            print(f"Error retrieving users: {e}")
            return []

    @staticmethod
    def delete_user(user_id):
        """Delete a specific user account."""
        try:
            user_ref = db.collection('users').document(user_id)
            if user_ref.get().exists:
                user_ref.delete()
                print(f"User {user_id} deleted successfully.")
                return True
            else:
                print(f"User {user_id} does not exist.")
                return False
        except Exception as e:
            print(f"Error deleting user account: {e}")
            return False

    @staticmethod
    def update_user_account(user_id, updates):
        """Update details for a specific user account."""
        try:
            user_ref = db.collection('users').document(user_id)

            if user_ref.get().exists:
                user_ref.update(updates)
                print(f"User {user_id} updated successfully.")
        except Exception as e:
            print(f"Error updating user account: {e}")
            return False
    
    @staticmethod
    def get_user_details(user_id):
        """Retrieve details for a specific user account."""
        try:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            if user_doc.exists:
                return user_doc.to_dict()  # Return user data as a dictionary
            else:
                print(f"User {user_id} does not exist.")
                return None
        except Exception as e:
            print(f"Error retrieving user details: {e}")
            return None
    
    @staticmethod
    def search_users_by_query(query, account_type='all'):
        """Search for users by query string."""
        try:
            # Query for matching usernames
            user_ref = db.collection('users').where('username', '>=', query).where('username', '<=', query + '\uf8ff')

            # Execute the query
            users_by_username = user_ref.stream()

            # Prepare the list of user data
            user_list = []
            for user in users_by_username:
                user_data = user.to_dict()
                # Exclude admins
                if user_data['account_type'] == 'admin':
                    continue

                # If account_type is not 'all', filter in memory
                if account_type != 'all' and user_data['account_type'] == account_type:
                    user_list.append(user_data)
                elif account_type == 'all':
                    user_list.append(user_data)

            return user_list
        except Exception as e:
            print(f"Error searching users: {e}")
            return []
    
    @staticmethod
    def filter_users(query):
        """Filter users by query."""
        try:
            # Query for matching usernames
            user_ref = db.collection('users').where('username', '>=', query).where('username', '<=', query + '\uf8ff')

            # Execute the query
            users_by_username = user_ref.stream()

            # Prepare the list of user data
            user_list = []
            for user in users_by_username:
                user_data = user.to_dict()
                user_list.append(user_data)

            return user_list
        except Exception as e:
            print(f"Error searching users: {e}")
            return []

    @staticmethod
    def get_pending_users():
        """Retrieve all user profiles that are not yet approved."""
        try:
            users_ref = db.collection('users')
            pending_users = users_ref.where('is_approved', '==', False).stream()
            pending_user_list = []
            
            for user in pending_users:
                user_data = user.to_dict()
                if user_data.get('account_type') != 'admin':  # Exclude admin accounts
                    pending_user_list.append(user_data)

            return pending_user_list
        except Exception as e:
            print(f"Error retrieving pending users: {e}")
            return []

    @staticmethod
    def approve_user(user_id):
        """Approve a specific user account by setting is_approved to True."""
        try:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_ref.update({'is_approved': True})
                print(f"User {user_id} approved successfully.")
                message = f"User {user_data['username']} approved successfully."
                return True, message
            else:
                print(f"User {user_data['username']} does not exist.")
                return False
        except Exception as e:
            print(f"Error approving user: {e}")
            message = f"Error approving user: {e}"
            return False, message
    
    @staticmethod
    def suspend_user(user_id):
        """Suspends a user by setting 'is_suspended' to True."""
        try:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                if user_data['is_suspended'] == True:
                    # message = f"User already suspended"
                    # return False, message
                    return {'success': False, 'message': 'User already suspended'}
                else:
                    # Suspend the user
                    user_ref.update({'is_suspended': True})
                    # message = f"User {user_data['username']} has been suspended successfully."
                    # return True, message
                    return {'success': True, 'message': f'User {user_data['username']} has been suspended successfully.'}
                    
                
            else:
                # message = f"User {user_data['username']} does not exist."
                # return False, message
                return {'success': False, 'message': f'User {user_data['username']} does not exist.'}

        except Exception as e:
            # message = f"Error suspending user: {e}"
            # return False, message
        
            return {'success': False, 'message': f'Error suspending user: {e}'}
        
    @staticmethod
    def get_hero_content():
        """Fetch hero content from Firestore."""
        try:
            hero_ref = db.collection('landing_page').document('default')
            
            hero_doc = hero_ref.get()
            
            # Check if the document exists
            if hero_doc.exists:
                return hero_doc.to_dict()
            else:
                print("Hero content not found.")
        except Exception as e:
            print(f"Error fetching hero content: {e}")
            return None

    @staticmethod
    def update_hero_content(data):
        """Update hero content in Firestore."""
        try:
            hero_ref = db.collection('landing_page').document('default')

            # Set the new data (overwrites if the document exists)
            hero_ref.set({
                'title': data.get('title'),
                'paragraph': data.get('paragraph')
            }, merge=True)

            print("Hero content updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating hero content: {e}")
            return False
        
    @staticmethod
    def get_about_content():
        """Fetch about content from Firestore."""
        try:
            about_ref = db.collection('landing_page').document('about')
            
            about_doc = about_ref.get()
            
            # Check if the document exists
            if about_doc.exists:
                return about_doc.to_dict()
            else:
                print("About content not found.")
        except Exception as e:
            print(f"Error fetching About content: {e}")
            return None
        
    @staticmethod
    def update_about_content(data):
        """Update hero content in Firestore."""
        try:
            about_ref = db.collection('landing_page').document('about')

            # Set the new data (overwrites if the document exists)
            about_ref.set({
                'title': data.get('title'),
                'paragraph': data.get('paragraph')
            }, merge=True)

            print("About content updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating About content: {e}")
            return False
    
    @staticmethod
    def get_features_content():
        """Fetch content based on type from Firestore."""
        try:
            content_ref = db.collection('landing_page').document('features')
            content_doc = content_ref.get()

            if content_doc.exists:
                return content_doc.to_dict()
            else:
                print(f"Feature content not found.")
                return None
        except Exception as e:
            print(f"Error fetching Feature content: {e}")
            return None
    
    @staticmethod
    def update_features_content(data):
        """Update content in Firestore based on type."""
        try:
            content_ref = db.collection('landing_page').document('features')
            # Set the new data (overwrites if the document exists)
            content_ref.set({
                'title': data.get('title'),
                'paragraph': data.get('paragraph')
            }, merge=True)

            print(f"Feature content updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating Feature content: {e}")
            return False
        
    @staticmethod
    def get_influencer_features():
        # Reference to the 'features' document inside 'landing_page' collection
        features_ref = db.collection('landing_page').document('features')
        
        # Fetch the 'features' document
        features_doc = features_ref.get()

        if not features_doc.exists:
            return {"error": "Features document not found"}
        
        # Reference to the influencer_features subcollection
        influencer_features_ref = features_ref.collection('influencer_features')
        
        # Fetch all documents in influencer_features subcollection
        influencer_features_docs = influencer_features_ref.stream()
        
        influencer_features = []
        for feature in influencer_features_docs:
            feature_data = feature.to_dict()
            influencer_features.append({
                "id": feature.id,
                "title": feature_data.get("title"),
                "paragraph": feature_data.get("paragraph")
            })
        
        return influencer_features

    @staticmethod
    def update_influencer_feature(feature_id, title, paragraph):
        # Reference to the 'features' document inside 'landing_page' collection
        features_ref = db.collection('landing_page').document('features')

        # Reference to the influencer_features subcollection
        influencer_features_ref = features_ref.collection('influencer_features')

        # Fetch the influencer feature document by ID
        influencer_feature_ref = influencer_features_ref.document(feature_id)

        # Prepare the updated data
        updated_data = {
            "title": title,
            "paragraph": paragraph
        }

        try:
            # Update the influencer feature document
            influencer_feature_ref.update(updated_data)
            return True  # Indicate success
        except Exception as e:
            print(f"Error updating influencer feature: {e}")
            return False  # Indicate failure