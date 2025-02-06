from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import zipfile
import tempfile

import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

from bs4 import BeautifulSoup
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

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

    # firebase_admin.initialize_app(cred)

    firebase_admin.initialize_app(cred)

db = firestore.client()

bucket = storage.bucket('fyp-24-s4-26.firebasestorage.app')

class FollowerHist:
    @staticmethod
    def allowed_file(filename):
        # This is a helper to check if the file is a zip file
        return filename.lower().endswith('.zip')
    
    @staticmethod
    def upload_to_firebase(file, filename):
        """
        Upload file to Firebase Storage.
        """
        try:
            print(bucket.name)
            blob = bucket.blob(f'uploads/{filename}')
            blob.upload_from_file(file)

            # Make the file publicly accessible
            blob.make_public()
            
            # Get the file's URL
            file_url = blob.public_url
            print(f"File uploaded and accessible at: {file_url}")

            return blob.name
        except Exception as e:
            print(f"Error uploading file to Firebase: {e}")
            return None
        
    @staticmethod
    def process_uploaded_folder_from_firebase(file_path):
        """
        Process the uploaded folder from Firebase storage.
        """
        try:
            # Download file from Firebase Storage
            blob = bucket.blob(file_path)
            file_bytes = blob.download_as_bytes()

            # Save the file temporarily and unzip
            temp_dir = tempfile.gettempdir()
            temp_zip_path = os.path.join(temp_dir, "temp.zip")
            folder_path = os.path.join(temp_dir, "unzipped_folder")

            # Save the file temporarily and unzip
            with open(temp_zip_path, 'wb') as f:
                f.write(file_bytes)

            # Now process the downloaded zip file as normal
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(folder_path)

            # Process the extracted folder to retrieve follower data
            followers_data = FollowerHist.process_uploaded_folder(folder_path)

            return followers_data

        except zipfile.BadZipFile:
            print("Error: The uploaded file is not a valid ZIP file.")
            return None
        except Exception as e:
            print(f"Error processing file from Firebase: {e}")
            return None

    @staticmethod
    def process_uploaded_folder(folder_path):
        """
        Process the uploaded folder and extract follower data.
        """
        try:
            # Define path to followers HTML file (assuming the zip contains a specific structure)
            folder = os.path.join(folder_path, "connections", "followers_and_following")
            followers_file = os.path.join(folder, "followers_1.html")

            # Extract followers data from the HTML file
            if not os.path.exists(followers_file):
                raise FileNotFoundError(f"{followers_file} not found.")
            
            followers_data = FollowerHist.get_followers_data(followers_file)

            # Return the followers data
            return followers_data

        except Exception as e:
            print(f"Error processing uploaded folder: {e}")
            return None
        
    @staticmethod
    def get_followers_data(followers_file):
        if not os.path.exists(followers_file):
            raise FileNotFoundError(f"{followers_file} not found.")

        def extract_followers(file_path):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{file_path} not found.")
            
            with open(file_path, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, "html.parser")
                follower_divs = soup.find_all('div', class_="pam _3-95 _2ph- _a6-g uiBoxWhite noborder")

                # Check if we found any follower divs
                if not follower_divs:
                    raise ValueError(f"No follower divs found in {file_path}.")
            
                followers_data = []
                for div in follower_divs:
                    username = div.find('a').text.strip()  # Extract username
                    follow_date = div.find_all('div')[-1].text.strip()  # Extract follow date
                    # Convert follow_date to datetime format
                    try:
                        follow_date = datetime.strptime(follow_date, '%b %d, %Y %I:%M %p')  # Adjust format as needed
                    except ValueError:
                        print(f"Skipping invalid date: {follow_date}")
                        continue  # Skip invalid dates
                    followers_data.append({'username': username, 'follow_date': follow_date})
                
                # Check if followers data is empty
                if not followers_data:
                    raise ValueError("No valid follower data collected.")
                
                return followers_data

        try:
            # Extract followers data
            followers_data = extract_followers(followers_file)

            # Check if data was collected properly
            if not followers_data:
                return {"error": "No followers data found."}
            
            # Aggregate followers data by date to count the number of followers for each date
            followers_df = pd.DataFrame(followers_data)

            # Check if the DataFrame is created successfully
            if followers_df.empty:
                return {"error": "Followers data frame is empty."}
            
            # Extract year and month from follow_date
            followers_df['year_month'] = followers_df['follow_date'].dt.to_period('M')

            # Group by year_month and aggregate both follower counts and usernames
            grouped_data = followers_df.groupby('year_month').agg(
                follower_count=('username', 'count'),
                usernames=('username', lambda x: list(x))
            ).reset_index()

            # Create a list of dicts with 'date' and 'follower_count' for analysis
            followers_data_for_analysis = grouped_data.to_dict(orient='records')

            return followers_data_for_analysis
        
        except Exception as e:
            return {"error": str(e)}

    @staticmethod    
    def calculate_follower_growth(followers_data):

        # Validate input data
        if not followers_data:
            return None, "No followers data available."

        # Verify all required fields are present
        required_keys = {'year_month', 'follower_count', 'usernames'}
        if not all(required_keys.issubset(record.keys()) for record in followers_data):
            return None, "Invalid data structure. Missing required fields."

        # Convert data to Dataframe
        followers_data_df = pd.DataFrame(followers_data)

        # Ensure 'year_month' column is in Period format and sort data by date (ascending)
        followers_data_df['year_month'] = pd.to_datetime(followers_data_df['year_month'].astype(str)).dt.to_period('M')
        followers_data_df.sort_values('year_month', ascending=True)

        # Handle missing months by creating a complete date range of months covering the last year
        last_month_in_data = followers_data_df['year_month'].max().to_timestamp()
        
        # Ensure 'last_month' reflects the current date (take the later of the two)
        current_month = datetime.now().replace(day=1)                                               # Get the first day of the current month
        last_month = max(last_month_in_data, current_month)                                         # Use the later of the two
        all_months = pd.period_range(last_month - pd.DateOffset(months=11), last_month, freq='M')   # Range of months for the past 12 months

        # Merge the complete month range with the existing data, filling missing months with 0 follower count
        complete_df = pd.DataFrame({'year_month': all_months})
        merged_df = pd.merge(complete_df, followers_data_df, on='year_month', how='left').fillna(0)

        # Ensure 'follower_count' column is of integer type
        merged_df['follower_count'] = merged_df['follower_count'].astype('int')

        print("Merged DataFrame: \n", merged_df)  # Inspect the dataframe after merge and fill

        if merged_df.empty:
            return None, "Not enough data for follower growth calculation."

        # Prepare features (months) and target variable (follower_count) for prediction
        months = (merged_df['year_month'].dt.to_timestamp() - merged_df['year_month'].dt.to_timestamp().min()).dt.days.values.reshape(-1, 1)
        follower_counts = merged_df['follower_count'].values

        # Check if there's enough variation in the months
        if len(set(months.flatten())) <= 1:
            return None, "Insufficient variation in the time data for polynomial regression."

        # Polynomial regression for forecasting
        degree = 2
        poly = PolynomialFeatures(degree=degree)
        months_poly = poly.fit_transform(months) # Transform the months data to polynomial features

        model = LinearRegression()              # Create a Linear Regression model
        model.fit(months_poly, follower_counts) # Fit the model to the data

        # Forecast future data (next 6 months)
        last_date = merged_df['year_month'].max().to_timestamp()
        reference_date = merged_df['year_month'].min().to_timestamp()

        future_dates = [
            (last_date + relativedelta(months=i)).strftime('%b %Y') for i in range(1, 7)
        ]
        future_months_as_days = [
            (last_date + relativedelta(months=i) - reference_date).days for i in range(1, 7)
        ]

        future_months_poly = poly.transform(np.array(future_months_as_days).reshape(-1, 1)) # Transform future months to polynomial features
        future_growth_predictions = np.maximum(model.predict(future_months_poly), 0)        # Ensure no negative predictions

        # Round the predictions to the nearest integer to avoid decimals
        future_growth_predictions = np.round(future_growth_predictions).astype(int)

        return {
            "historical_data": merged_df['follower_count'].tolist(),                    # Historical follower counts
            "usernames": merged_df['usernames'].tolist(),                               # Usernames corresponding to the historical data
            "future_data": future_growth_predictions.tolist(),                          # Predicted follower counts for the next 6 months
            "historical_labels": merged_df['year_month'].dt.strftime('%b %Y').tolist(), # Month labels for historical data
            "future_labels": future_dates,                                              # Labels for the predicted future months
            "granularity": "Monthly"
        }, None
