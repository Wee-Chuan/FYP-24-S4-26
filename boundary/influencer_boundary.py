import os
import csv
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify, current_app
from werkzeug.utils import secure_filename
from apify_client import ApifyClient
import entity.admin as adm

# Custom modules
import network as nw
import createUsers as cu
from entity.user import User
from entity.followers_hist_entity import FollowerHist

# Define Flask Blueprint
influencer_boundary = Blueprint('influencer_boundary', __name__)

# Path for Engagement Metrics CSV
ENGAGEMENT_CSV_PATH = "engagement_metrics.csv"


@influencer_boundary.route("/dashboard/engagement_metrics", methods=["GET"])
def engagement_metrics():
    """
    Renders the engagement dashboard. Users can select a post to analyze.
    """
    try:
        if not os.path.exists(ENGAGEMENT_CSV_PATH):
            return "⚠️ Error: engagement_metrics.csv file not found!", 400

        # Process CSV and get post URLs
        post_urls, engagement_data = User.process_engagement_data(ENGAGEMENT_CSV_PATH)

        if not engagement_data:
            return render_template("dashboard/influencer_menu/engagement.html", post_urls=[], engagement_data=[])

        # Store engagement CSV path in session
        session["engagement_csv"] = ENGAGEMENT_CSV_PATH

        return render_template(
            "dashboard/influencer_menu/engagement.html",
            post_urls=post_urls,
            engagement_data=engagement_data
        )

    except Exception as e:
        print(f"❌ Error loading engagement dashboard: {e}")
        return f"An error occurred: {e}", 500


@influencer_boundary.route("/api/get_visualization_data", methods=["GET"])
def get_visualization_data():
    """
    API endpoint to retrieve engagement data for a selected post.
    """
    try:
        # Ensure engagement_metrics.csv exists
        csv_file = session.get("engagement_csv", ENGAGEMENT_CSV_PATH)

        if not os.path.exists(csv_file):
            return jsonify({"error": "⚠️ No CSV file found. Please generate engagement data first."}), 404

        post_url = request.args.get("post_url")
        if not post_url:
            return jsonify({"error": "⚠️ Missing post URL parameter."}), 400

        post_data = User.get_post_engagement(csv_file, post_url)
        if not post_data:
            return jsonify({"error": "⚠️ No data found for the selected post."}), 404

        # Generate AI Summary
        ai_summary = User.generate_ai_summary(post_data[0])

        return jsonify({
            "post_data": post_data,
            "ai_summary": ai_summary
        })

    except Exception as e:
        print(f"❌ Error fetching visualization data: {e}")
        return jsonify({"error": str(e)}), 500

###################################################################################################################

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
        "resultsLimit": 15
    }

    # Run the Actor and wait for it to finish
    comments_run = client.actor("SbK00X0JYCPblD2wp").call(run_input=comments_scraper_input)

    # Open a CSV file to save the comments data
    csv_file_path = 'data/postCommentData.csv'  # Save in the static folder
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
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

    print(f"All comments saved to {csv_file_path}")

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
        print(User.get_username_by_user_id(user_id))
        nw.generateGraphs(User.get_username_by_user_id(user_id))

        # Return the username in a JSON response
        return jsonify({
            'username': username,
        })
    
    except Exception as e:
        # Catch any error that occurs during the process and return an error message
        print(f"Error during Instagram scraping: {e}")
        flash("Username does not exist or user is private")
        return jsonify({
            'error': 'Failed to retrieve comments or process data. Please try again later.'
        }), 500

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

@influencer_boundary.route('/check_file', methods=['POST'])  # Use POST instead of GET to match JS request method
def check_file():
    # Get the JSON body from the request
    file_data = request.get_json()  
    destination_blob_name = file_data['file_path']  # Extract the file path

    # Check if the file exists in Firebase Storage
    file_exists = adm.file_exists_in_firebase(destination_blob_name)
    
    # Return the response based on whether the file exists or not
    if file_exists:
        print("hello")
        return jsonify({"exists": True, "message": "File exists in Firebase Storage."}), 200
    else:
        print("hellono")
        return jsonify({"exists": False, "message": "File does not exist in Firebase Storage."}), 404

@influencer_boundary.route('/retrieve', methods=['GET'])
def retrieve():
    destination_blob_name = request.args.get('destination_blob_name')
    local_file_path = request.args.get('local_file_path')
    
    try:
        adm.retrieve_from_firebase(destination_blob_name, local_file_path)
        return jsonify({"message": f"File downloaded successfully to {local_file_path}."}), 200
    except Exception as e:
        return jsonify({"message": f"Error retrieving file: {str(e)}"}), 500

