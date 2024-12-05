from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

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

class FollowerHist:
    @staticmethod
    def get_followers_hist(user_id):
        try:
            follower_history_ref = db.collection('follower_history').document(user_id).collection('history')\
            
            # Fetch all documents from the history subcollection
            docs = follower_history_ref.stream()

            history = []
            for doc in docs:
                data = doc.to_dict()
                date_value = data.get('date')
                try:
                    datetime.strptime(date_value, "%Y-%m-%d")  # Validate format
                except ValueError:
                    raise ValueError(f"Invalid date format: {date_value}")
                
                history.append({
                    'user_id': user_id,
                    'date': date_value,
                    'follower_count': data.get('follower_count', 0) # Default 0 if missing
                })

            # Sort the history list by date
            history = sorted(history, key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))

            return history
        except Exception as e:
            print(f"Error retrieving follower history: {e}")
            return []

    @staticmethod    
    def calculate_follower_growth(historical_data):
        # Prepare the data
        historical_data_df = pd.DataFrame(historical_data)
        if 'date' not in historical_data_df or 'follower_count' not in historical_data_df:
            return None, "Invalid data structure. Missing required fields."

        historical_data_df['date'] = pd.to_datetime(historical_data_df['date'])
        historical_data_df.set_index('date', inplace=True)

        one_year_ago = historical_data_df.index.max() - pd.DateOffset(years=1)
        filtered_data = historical_data_df[historical_data_df.index >= one_year_ago]

        if filtered_data.empty:
            return None, "Not enough data for the past year."

        monthly_data = filtered_data.resample('ME').last()
        monthly_data['growth'] = monthly_data['follower_count'].diff()
        monthly_data.dropna(inplace=True)

        if len(monthly_data) < 2:
            return None, "Not enough data to forecast follower growth."
      
        dates = (monthly_data.index - monthly_data.index.min()).days.values.reshape(-1, 1)
        follower_counts = monthly_data['growth'].values

        # Polynomial regression for forecasting
        degree = 2
        poly = PolynomialFeatures(degree=degree)
        dates_poly = poly.fit_transform(dates)

        model = LinearRegression()
        model.fit(dates_poly, follower_counts)

        last_date = monthly_data.index.max()
        reference_date = monthly_data.index.min()

        future_dates = [
            (last_date + relativedelta(months=i)).strftime('%b %Y') for i in range(1, 7)
        ]
        future_dates_as_days = [
            (last_date + relativedelta(months=i) - reference_date).days for i in range(1, 7)
        ]

        future_dates_poly = poly.transform(np.array(future_dates_as_days).reshape(-1, 1))
        future_growth_predictions = np.maximum(model.predict(future_dates_poly), 0)

        last_follower_count = monthly_data['follower_count'].iloc[-1]
        future_follower_counts = [last_follower_count]
        for growth in future_growth_predictions:
            future_follower_counts.append(future_follower_counts[-1] + growth)

        return {
            "historical_data": monthly_data['follower_count'].tolist(),
            "future_data": future_follower_counts[1:],  # Exclude the initial count
            "historical_labels": monthly_data.index.strftime('%b %Y').tolist(),
            "future_labels": future_dates,
            "granularity": "Monthly"
        }, None
