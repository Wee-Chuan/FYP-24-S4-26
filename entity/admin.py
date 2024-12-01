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
    def search_users_by_query(query):
        """Search for users by query string."""
        try:
            # Query for matching usernames
            user_ref_username = db.collection('users').where('username', '>=', query).where('username', '<=', query + '\uf8ff')
            # Query for matching account types
            user_ref_account_type = db.collection('users').where('account_type', '>=', query).where('account_type', '<=', query + '\uf8ff')

            # Execute both queries
            users_by_username = user_ref_username.stream()
            users_by_account_type = user_ref_account_type.stream()

            # Combine results
            user_list = []
            for user in users_by_username:
                user_data = user.to_dict()
                if user_data.get('account_type') != 'admin':  # Exclude admin accounts
                    user_list.append(user_data)

            for user in users_by_account_type:
                user_data = user.to_dict()
                if user_data.get('account_type') != 'admin':  # Exclude admin accounts
                    # Add to list only if not already present (optional)
                    if user_data not in user_list:
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