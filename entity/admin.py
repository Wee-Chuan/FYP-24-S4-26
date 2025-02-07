import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import os
from entity.user import bucket

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
    print("admin initialised")
    cred = credentials.Certificate(firebase_credentials) 
    firebase_admin.initialize_app(cred, {'storageBucket': 'fyp-24-s4-26.firebasestorage.app' })
    bucket = storage.bucket()

db = firestore.client()

# file storage functions
def upload_to_firebase(file_path, destination_blob_name):
    """
    Upload a file to Firebase Storage.
    :param file_path: Path to the file you want to upload
    :param destination_blob_name: The name of the file in Firebase Storage
    :return: URL of the uploaded file
    """
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    blob.make_public()  # Make the file publicly accessible
    return blob.public_url

def file_exists_in_firebase(destination_blob_name):
    """
    Check if a file exists in Firebase Storage.
    :param destination_blob_name: The name of the file to check
    :return: Boolean indicating whether the file exists
    """
    print("HEHEHEHEHEHE")
    print(destination_blob_name)
    blob = bucket.blob(destination_blob_name)
    return blob.exists()

def retrieve_from_firebase(destination_blob_name, local_file_path):
    """
    Retrieve a file from Firebase Storage and save it locally.
    :param destination_blob_name: The name of the file in Firebase Storage
    :param local_file_path: Path where the file will be saved locally
    """
    blob = bucket.blob(destination_blob_name)
    blob.download_to_filename(local_file_path)

class Admin:
    @staticmethod
    def get_all_users():
        """Retrieve all user profiles for admin view."""
        try:
            users = db.collection('users').stream()
            user_list = []

            for user in users:
                user_data = user.to_dict()
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
    
    # ============================== Manage landing page ==================================#
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
        """Update about content in Firestore."""
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
        influencer_feature_doc = influencer_features_ref.document(feature_id)

        # Prepare the updated data
        updated_data = {
            "title": title,
            "paragraph": paragraph
        }

        try:
            # Update the influencer feature document
            influencer_feature_doc.update(updated_data)
            return True  # Indicate success
        except Exception as e:
            print(f"Error updating influencer feature: {e}")
            return False  # Indicate failure
    
    @staticmethod
    def delete_influencer_feature(feature_id):
        # Reference to the 'features' document inside 'landing_page' collection
        features_ref = db.collection('landing_page').document('features')

        # Reference to the influencer_features subcollection
        influencer_features_ref = features_ref.collection('influencer_features')

        # Fetch the influencer feature document by ID
        influencer_feature_ref = influencer_features_ref.document(feature_id)

        try:
            # Delete the influencer feature document
            influencer_feature_ref.delete()
            print(f"Influencer feature with ID {feature_id} successfully deleted.")
            return True  # Indicate success
        except Exception as e:
            print(f"Error deleting influencer feature with ID {feature_id}: {e}")
            return False  # Indicate failure
    
    @staticmethod
    def add_influencer_feature(title, paragraph):
        # Reference to the 'features' document inside 'landing_page' collection
        features_ref = db.collection('landing_page').document('features')

        # Reference to the influencer_features subcollection
        influencer_features_ref = features_ref.collection('influencer_features')

        try:
            # Add a new document to the influencer_features subcollection
            new_feature_ref = influencer_features_ref.add({
                "title": title,
                "paragraph": paragraph
            })

            print(f"Influencer feature successfully created with ID {new_feature_ref[1].id}.")
            return True  # Indicate success
        except Exception as e:
            print(f"Error creating influencer feature: {e}")
            return False  # Indicate failure


    # ============================== Manage about us page ==================================#
    @staticmethod
    def get_overview_content():
        """Fetch overview content from Firestore."""
        try:
            overview_ref = db.collection('about_us_page').document('overview')
            
            overview_doc = overview_ref.get()
            
            # Check if the document exists
            if overview_doc.exists:
                return overview_doc.to_dict()
            else:
                print("Overview content not found.")
        except Exception as e:
            print(f"Error fetching Overview content: {e}")
            return None
        
    @staticmethod
    def update_overview_content(overview_title, overview_paragraph, overview_paragraph2):
        """Update overview content in Firestore."""
        try:
            overview_ref = db.collection('about_us_page').document('overview')
            # Set the new data (overwrites if the document exists)
            overview_ref.set({
                'title': overview_title,
                'paragraph': overview_paragraph,
                'paragraph2': overview_paragraph2
            }, merge=True)

            print(f"Overview content updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating Overview content: {e}")
            return False
        
    @staticmethod
    def get_goals_heading():
        """Get goals heading in Firestore."""
        try:
            goals_ref = db.collection('about_us_page').document('goals')

            goals_doc = goals_ref.get()

            # Check if the document exists
            if goals_doc.exists:
                return goals_doc.to_dict()
            else:
                print("Goals content not found.")
        except Exception as e:
            print(f"Error fetching Goals content: {e}")
            return None
        
    @staticmethod
    def update_goals_heading(goals_title):
        """Update goals heading in Firestore."""
        try:
            goals_ref = db.collection('about_us_page').document('goals')
            # Set the new data (overwrites if the document exists)
            goals_ref.set({
                'heading': goals_title
            }, merge=True)

            print(f"Goals title updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating Goals title: {e}")
            return False
         
        
    @staticmethod
    def get_our_goals():
        try:
            # Reference to the 'goals' document inside 'about_us_page' collection
            goals_ref = db.collection('about_us_page').document('goals')
            
            # Fetch the 'goals' document
            goals_doc = goals_ref.get()

            if not goals_doc.exists:
                return {"error": "Goals document not found"}
            
            # Reference to the our_goals subcollection
            our_goals_ref = goals_ref.collection('our_goals')
            
            # Fetch all documents in our_goals subcollection
            our_goals_docs = our_goals_ref.stream()
            
            our_goals = []
            for goals in our_goals_docs:
                goals_data = goals.to_dict()
                our_goals.append({
                    "id": goals.id,
                    "icon": goals_data.get("icon", "fas fa-project-diagram"),
                    "title": goals_data.get("title"),
                    "description": goals_data.get("description")
                })
            
            return our_goals
        except Exception as e:
            print(f"Error fetching our goals: {e}")
            return {"error": "An error occurred while fetching the goals"}

    @staticmethod
    def update_our_goals(goal_id, title, description, icon):
        # Reference to the 'goals' document inside 'about_us_page' collection
        goals_ref = db.collection('about_us_page').document('goals')

        # Reference to the our_goals subcollection
        our_goals_ref = goals_ref.collection('our_goals')

        # Fetch our_goals documents by ID
        our_goals_ref = our_goals_ref.document(goal_id)

        # Prepare the updated data
        updated_data = {
            "title": title,
            "description": description,
            "icon": icon
        }

        try:
            # Update the influencer feature document
            our_goals_ref.update(updated_data)
            return True  # Indicate success
        except Exception as e:
            print(f"Error updating our goals: {e}")
            return False  # Indicate failure
    
    @staticmethod
    def get_testimonials():
        """
        Fetch all ratings and reviews from Firestore, grouped by users.
        """
        try:
            reviews_ref = db.collection('ratings_and_reviews')
            all_reviews = []

            # Loop through each user document in the 'ratings_and_reviews' collection
            for user_doc in reviews_ref.stream():
                user_data = user_doc.to_dict()
                user_id = user_data.get('user_id')
                username = user_data.get('username')
                reviews_subcollection = user_doc.reference.collection('reviews')

                # Fetch reviews for the user
                for review in reviews_subcollection.stream():
                    review_data = review.to_dict()
                    # Add 'rating', 'review' and 'date' fields to the reviews list
                    all_reviews.append({
                        'id': review.id,
                        'user_id': user_id,
                        'username': username,
                        'rating': review_data.get('rating'),
                        'category': review_data.get('category'),
                        'review': review_data.get('review'),
                        'date': review_data.get('date'),
                        'is_selected': review_data.get('is_selected')
                    })

            return all_reviews
        except Exception as e:
            print(f"Error retrieving reviews: {e}")
            return []
    
    @staticmethod
    def update_testimonial_selection(review_id, is_selected=True):
        try:
            # Reference the main 'ratings_and_reviews' collection
            reviews_ref = db.collection('ratings_and_reviews')

            # Loop through each user document
            for user_doc in reviews_ref.stream():
                # Access the 'reviews' subcollection for the user
                reviews_subcollection = user_doc.reference.collection('reviews')
                
                 # Iterate through each review in the subcollection
                for review_doc in reviews_subcollection.stream():
                    if review_doc.id == review_id:  # Check if the document ID matches the given review_id
                        # Update the 'is_selected' field for the matching document
                        review_doc.reference.update({'is_selected': is_selected})
                        print(f"Updated review ID {review_id} in user {user_doc.id}: is_selected = {is_selected}")
                        return True  # Exit after updating the first match

            print(f"Review ID {review_id} not found in any subcollection.")
            return False
        except Exception as e:
            print(f"Error updating review ID {review_id}: {e}")
            return False
    
    # ============================== Manage customer support page ==================================#
    @staticmethod
    def get_faq_content():
        try:
            faq_section_ref = db.collection('customer_support_page').document('faq_section')

            faq_section_doc = faq_section_ref.get()

            # Check if the document exists
            if faq_section_doc.exists:
                return faq_section_doc.to_dict()
            else:
                print("FAQ content not found.")
        except Exception as e:
            print(f"Error fetching FAQ content: {e}")
            return None
    
    @staticmethod
    def update_faq_content(faq_heading=None, faq_paragraph=None, contact_heading=None, contact_paragraph=None, main_heading=None, main_paragraph=None):
        try:
            faq_section_ref = db.collection('customer_support_page').document('faq_section')

            # Prepare the updated data dictionary
            updated_data = {}

            if main_heading is not None:
                updated_data['heading'] = main_heading
            if main_paragraph is not None:
                updated_data['heading_paragraph'] = main_paragraph
            if faq_heading is not None:
                updated_data['title1'] = faq_heading
            if faq_paragraph is not None:
                updated_data['paragraph1'] = faq_paragraph
            if contact_heading is not None:
                updated_data['title2'] = contact_heading
            if contact_paragraph is not None:
                updated_data['paragraph2'] = contact_paragraph

            if not updated_data:
                print("No fields to update.")
                return False
            
            # Perform the update
            faq_section_ref.update(updated_data)
            print("FAQ content updated successfully.")
            return True
        
        except Exception as e:
            print(f"Error fetching FAQ content: {e}")
            return None

    @staticmethod
    def get_faqs():
        try:
            # Reference to the 'faq_section' document inside 'customer_support_page' collection
            faq_section_ref = db.collection('customer_support_page').document('faq_section')
            
            # Reference to the faqs subcollection
            faqs_ref = faq_section_ref.collection('faqs')
            
            # Fetch all documents in our_goals subcollection
            faqs_docs = faqs_ref.stream()
            
            faqs = []
            for faq in faqs_docs:
                faqs_data = faq.to_dict()
                faqs.append({
                    "id": faq.id,
                    "question": faqs_data.get("question"),
                    "answer": faqs_data.get("answer")
                })

            return faqs
        except Exception as e:
            print(f"Error fetching FAQs: {e}")
            return {"error": "An error occurred while fetching the faqs"}
    
    @staticmethod
    def update_faq(faq_id, question, answer):
        # Reference to the 'faq_section' document inside 'customer_support_page' collection
        faq_section_ref = db.collection('customer_support_page').document('faq_section')

        # Reference to the faqs subcollection
        faqs_ref = faq_section_ref.collection('faqs')

        # Fetch the faqs document by ID
        faqs_doc = faqs_ref.document(faq_id)

        # Prepare the updated data
        updated_data = {
            "question": question,
            "answer": answer
        }

        try:
            # Update the FAQ document
            faqs_doc.update(updated_data)
            return True  # Indicate success
        except Exception as e:
            print(f"Error updating faqs feature: {e}")
            return False  # Indicate failure
    
    @staticmethod
    def delete_faq(faq_id):
        # Reference to the 'faq_section' document inside 'customer_support_page' collection
        faq_section_ref = db.collection('customer_support_page').document('faq_section')

        # Reference to the faqs subcollection
        faqs_ref = faq_section_ref.collection('faqs')

        # Fetch the faqs document by ID
        faqs_doc = faqs_ref.document(faq_id)

        try:
            # Delete the FAQ document
            faqs_doc.delete()
            print(f"FAQ with ID {faq_id} successfully deleted.")
            return True  # Indicate success
        except Exception as e:
            print(f"Error deleting FAQ with ID {faq_id}: {e}")
            return False  # Indicate failure
    
    @staticmethod
    def add_faq(question, answer):
        # Reference to the 'faq_section' document inside 'customer_support_page' collection
        faq_section_ref = db.collection('customer_support_page').document('faq_section')

        # Reference to the influencer_features subcollection
        faqs_ref = faq_section_ref.collection('faqs')

        try:
            # Add a new document to the influencer_features subcollection
            new_faq_ref = faqs_ref.add({
                "question": question,
                "answer": answer
            })

            print(f"FAQ successfully created with ID {new_faq_ref[1].id}.")
            return True  # Indicate success
        except Exception as e:
            print(f"Error FAQ feature: {e}")
            return False  # Indicate failure




