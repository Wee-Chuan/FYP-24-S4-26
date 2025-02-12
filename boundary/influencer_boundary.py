import os
import csv
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify, current_app
from werkzeug.utils import secure_filename
from apify_client import ApifyClient
import entity.admin as adm
from firebase_admin import credentials, storage

#---------------------------------Gemini API------------------------
from boundary.influencer_ai_summary import process_ai_summary
#--------------------------------------------------------------------

# Custom modules
import entity.network as nw
import entity.createUsers as cu
from entity.user import User
from entity.followers_hist_entity import FollowerHist

# Define Flask Blueprint
influencer_boundary = Blueprint('influencer_boundary', __name__)

###################################################################################################################

@influencer_boundary.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@influencer_boundary.route('/followers', methods=['GET', 'POST'])
def followers():
    """
    Route to display followers forecast for the user.
    Handles file uploads, processes follower data, and calculates follower growth forecasts.
    """
    try:
        # Retrieve user_id from the session
        user_id = session.get('user_id')
        print(f"User ID from session: {user_id}")

        # Fetch user profile using user_id
        user = User.get_profile(user_id)

        # Validate session and user existence
        if not user_id or not user:
            flash("Session expired or user not found. Please log in again.", "danger")
            print("Session expired or user_id not found") 
            return redirect(url_for('navbar.login'))  # Redirect to login if session is invalid
        
        # Handle POST request (file upload)
        if request.method == 'POST' and 'folder_zip' in request.files:
            session.pop('forecast', None)  

            file = request.files['folder_zip']

            # Check if the file is allowed and process it
            if file and FollowerHist.allowed_file(file.filename):

                followers_data, error_message = FollowerHist.extract_files_from_zip(file)

                if not followers_data:
                    flash(f"Error processing file: {error_message}", "danger")
                    return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)

                # Calculate follower growth forecast
                forecast, error = FollowerHist.calculate_follower_growth(followers_data)
                if error:
                    flash(error, 'warning')
                    print(f"Error in calculating follower growth: {error}")

                print(f"Forecast data: {forecast}") 

                # Save forecast data and file URL to session for persistence
                session['forecast'] = forecast

                # Render the template with data
                return render_template(
                    'dashboard/influencer_menu/followers.html',
                    user_id=user_id,
                    user=user,
                    forecast=forecast,
                )
            else:
                # If the file extension is not allowed
                flash("Invalid file format. Please upload a valid ZIP file.", "danger")
                return redirect(url_for('influencer_boundary.followers'))
            
        # For GET requests or when no file is uploaded, check for existing data in the session
        forecast = session.get('forecast')

        # Render the template with existing data (if any)
        return render_template(
            'dashboard/influencer_menu/followers.html', 
            user_id=user_id, 
            user=user, 
            forecast=forecast,
        )
    
    except Exception as e:
        # Handle unexpected errors
        print(f"Error in followers route: {e}")
        flash("An error occurred while fetching followers data.", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

@influencer_boundary.route('/post_page')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def post_page():
    account_type = session.get('account_type')
    user_id = session.get('user_id') 
    user = User.get_profile(user_id) 
    return render_template('dashboard/influencer_menu/post_network.html', user_id=user_id, user=user)

@influencer_boundary.route('/commenttree')  
def commenttree():
    return render_template('templates/comment_tree.html')

import shutil

@influencer_boundary.route('/post_analysis', methods=['POST'])
def post_analysis():
    # Get the post URL from the form input
    post_url = request.form.get('URL')

    if not post_url:
        return jsonify({'error': 'Post URL is required'}), 400

    # Replace with your APIFY token
    APIFY_API_TOKEN = "apify_api_iGbTvXBtw6Lawc81y3AvuZnoyKZ2IT156FKk"

    # Initialize the ApifyClient with your API token
    client = ApifyClient(APIFY_API_TOKEN)

    # Prepare the input for the Instagram Comments scraper
    comments_scraper_input = {
        "directUrls": [post_url],
        "includeNestedComments": True,
        "isNewestComments": False,
        "resultsLimit": 30
    }

    # Run the Actor and wait for it to finish
    comments_run = client.actor("SbK00X0JYCPblD2wp").call(run_input=comments_scraper_input)

    # Temporary file to save the comments data
    temp_csv_file_path = 'data/temp_postCommentData.csv'
    final_csv_file_path = 'data/postCommentData.csv'
    comment_count = 0

    with open(temp_csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Fetch all the unique keys across all items
        all_fieldnames = set()

        # Fetch all items and find all the keys
        for item in client.dataset(comments_run["defaultDatasetId"]).iterate_items():
            all_fieldnames.update(item.keys())

        # Convert the set to a sorted list for consistent column order
        all_fieldnames = sorted(list(all_fieldnames))

        # Initialize the CSV writer
        writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)

        # Write the header row with dynamic fields
        writer.writeheader()

        # Fetch and save Actor results from the run's dataset (all comments)
        for item in client.dataset(comments_run["defaultDatasetId"]).iterate_items():
            writer.writerow(item)
            comment_count += 1

    print(f"Comments temporarily saved to {temp_csv_file_path}. Total comments: {comment_count}")

    # Handle file logic based on comment count
    if comment_count < 50:
        # Cleanup the temporary file
        os.remove(temp_csv_file_path)
        return jsonify({
            'message': f'Post analysis completed. Only {comment_count} comments found, which is less than the required threshold.'
        })
    else:
        # Move the temp file to the final location
        shutil.move(temp_csv_file_path, final_csv_file_path)
        print(f"Data moved to {final_csv_file_path}")

    # Generate the network graph
    user_id = session.get('user_id')
    cu.create_user_json()
    cu.make_convo_file()
    cu.show_network(User.get_username_by_user_id(user_id))

    # Return success in JSON response
    return jsonify({
        'message': 'Post analysis completed.',
        'comment_tree_url': '/static/comment_tree.html'
    })

@influencer_boundary.route('/network')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def network():
    account_type = session.get('account_type')
    user_id = session.get('user_id') 
    user = User.get_profile(user_id) 
    return render_template('dashboard/influencer_menu/network.html', user_id=user_id, user=user)

#------------------------------------------------GEMINI_API -----------------------------------------------

@influencer_boundary.route('/display_network', methods=['POST'])
def display_network():
    user_id = session.get('user_id') 
    
    # Get the username from the POST request
    username = request.form.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Replace with your APIFY token
    APIFY_API_TOKEN = "apify_api_iGbTvXBtw6Lawc81y3AvuZnoyKZ2IT156FKk"

    # Initialize the ApifyClient with your API token
    client = ApifyClient(APIFY_API_TOKEN)

    try:
        # Prepare the Actor input for the Instagram Post scraper using the username entered in the form
        run_input = {
            "username": [username],  # Dynamically pass the username from the form
            "resultsLimit": 10,  # Get 1 post to fetch comments from
        }

        # Run the Actor and wait for it to finish
        run = client.actor("nH2AHrwxeTRJoN5hX").call(run_input=run_input)

        # Collect the post URLs from the results
        postURLs = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            post_url = item.get("url")  # Access the post URL
            postURLs.append(post_url)

        # Prepare the Actor input for the Instagram Comments scraper
        run_input = {
            "directUrls": postURLs,
            "resultsLimit": 10,  # Modify this number as needed to capture more comments
            "includeReplies": False,
        }

        # Run the Actor and wait for it to finish
        run = client.actor("SbK00X0JYCPblD2wp").call(run_input=run_input)

        # Open a CSV file to save the comments data
        with open('data/commentData.csv', 'w', newline='', encoding='utf-8') as csvfile:
            # Fetch all the unique keys across all items
            all_fieldnames = set()

            # Fetch all items and find all the keys
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_fieldnames.update(item.keys())

            # Convert the set to a sorted list for consistent column order
            all_fieldnames = sorted(list(all_fieldnames))

            # Initialize the CSV writer
            writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)

            # Write the header row with dynamic fields
            writer.writeheader()

            # Fetch and save Actor results from the run's dataset (all comments)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                # Write each comment as a new row in the CSV file
                writer.writerow(item)

        print("All comments saved to data/commentData.csv")

        # Generate graphs using the username from the user_id
        nw.generateGraphs(User.get_username_by_user_id(user_id))

        # ✅ Generate AI Summary AFTER Processing Comments
        ai_summary = process_ai_summary(username)

        # ✅ Return AI Summary in API Response
        return jsonify({
            'username': username,
            'ai_summary': ai_summary
        })
    
    except Exception as e:
        # Catch any error that occurs during the process and return an error message
        print(f"Error during Instagram scraping: {e}")
        flash("Username does not exist or user is private")
        return jsonify({
            'error': 'Failed to retrieve comments or process data. Please try again later.'
        }), 500

#----------------------------------------------------------------------------------------------
@influencer_boundary.route('/display_sentiment_graph')
def display_sentiment_graph():
    return render_template('dashboard/influencer_menu/sentimentgraph.html')

@influencer_boundary.route('/display_topic_graph')
def display_topic_graph():
    return render_template('dashboard/influencer_menu/topicnetwork.html')

# Flask routes
@influencer_boundary.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    destination_blob_name = request.form['destination_blob_name']
    file_path = f"temp_{file.filename}"
    file.save(file_path)
    
    try:
        file_url = adm.upload_to_firebase(file_path, destination_blob_name)
        os.remove(file_path)  # Clean up the temporary file
        return jsonify({"message": "File uploaded successfully", "url": file_url}), 200
    except Exception as e:
        return jsonify({"message": f"Error uploading file: {str(e)}"}), 500

# @influencer_boundary.route('/check_file', methods=['POST'])  # Use POST instead of GET to match JS request method
# def check_file():
#     # Get the JSON body from the request
#     file_data = request.get_json()  
#     destination_blob_name = file_data['file_path']  # Extract the file path

#     # Check if the file exists in Firebase Storage
#     file_exists = adm.file_exists_in_firebase(destination_blob_name)
    
#     # Return the response based on whether the file exists or not
#     if file_exists:
#         print("hello")
#         return jsonify({"exists": True, "message": "File exists in Firebase Storage."}), 200
#     else:
#         print("hellono")
#         return jsonify({"exists": False, "message": "File does not exist in Firebase Storage."}), 404

@influencer_boundary.route('/retrieve', methods=['GET'])
def retrieve():
    destination_blob_name = request.args.get('destination_blob_name')
    local_file_path = request.args.get('local_file_path')
    print(destination_blob_name)
    try:
        adm.retrieve_from_firebase(destination_blob_name, local_file_path)
        print ("{local_file_path} saved")
        return jsonify({"message": f"File downloaded successfully to {local_file_path}."}), 200
    except Exception as e:
        return jsonify({"message": f"Error retrieving file: {str(e)}"}), 500


import json
from flask import jsonify

@influencer_boundary.route('/data/conversations', methods=['GET'])
def get_conversations():
    file_path = 'data/conversations.json'  # Define the file path
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in the file"}), 500

@influencer_boundary.route('/check_file', methods=['POST'])
def check_file():
    
    data = request.get_json()
    file_path = data.get('file_path')
    
    if not file_path:
        print("here")
        return jsonify({"exists": False, "message": "No file path provided"}), 400
    
    # Extract username and filename (without extension) from the provided file path
    username, filename_with_extension = file_path.split('/', 1)  # Split only once to get the username and filename
    filename = filename_with_extension.split('.')[0]  # Get the filename without the extension
    print("username:"+username)
    # Set the path prefix to search for all files under the username (excluding the filename)
    path_prefix = f"{username}/"  # This will match all files under 'username/'

    # List all files in Firebase Cloud Storage with the prefix
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=path_prefix)
    print(path_prefix)
    # Variables to store the latest blob and its timestamp
    latest_blob = None
    latest_time = None
    
    # Iterate over the blobs and find the latest file based on the timestamp
    for blob in blobs:
        # Check if the current blob's name contains the requested filename without extension
        if filename in blob.name and blob.name.endswith(('png', 'html')):  # Check if it has the correct extension
            if not latest_time or blob.updated > latest_time:
                latest_blob = blob
                latest_time = blob.updated

    if latest_blob:
    # Extract the file URL starting from the username onward
        file_url = latest_blob.public_url.split('fyp-24-s4-26.firebasestorage.app/')[1]
        print(file_url)
        return jsonify({
            "exists": True,
            "message": f"Latest file for {file_path}: {file_url}",
            "file_url": file_url
        })
    else:
        return jsonify({"exists": False, "message": "No files found for the specified path"}), 404
