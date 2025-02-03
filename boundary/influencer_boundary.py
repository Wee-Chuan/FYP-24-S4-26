import network as nw
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from entity.user import User
from entity.followers_hist_entity import FollowerHist
import csv, os
from apify_client import ApifyClient
import createUsers as cu

from werkzeug.utils import secure_filename

influencer_boundary = Blueprint('influencer_boundary', __name__)

# =================== Influencer Dashboard Menu =================== #

@influencer_boundary.route('/dashboard/engagement_metrics', methods=['GET'])
def engagement_metrics():
    """
    Route to visualize the user's engagement metrics.
    """
    try:
        # Get the logged-in user ID and account type
        user_id = session.get('user_id')
        account_type = session.get('account_type')

        # Check if the user exists and is an influencer
        user = User.get_profile(user_id)
        if not user or account_type != 'influencer':
            flash("Unauthorized access. Only influencers can view engagement metrics.", "danger")
            return redirect(url_for('dashboard_boundary.dashboard'))
        
        
        # CHECKING IF ACCOUNT IS LINKEDDDDDDDDDDDDDDDDDDDDDDDDDDD 
        if user['linked_social_account'] == "":
            flash("Please link to your social media acccount first", "danger")
            return redirect(url_for('dashboard_boundary.dashboard'))

        metrics = User.visualize_engagement_metrics(user_id)

        # Check if any field is None or undefined
        for metric in metrics:
            for key, value in metric.items():
                if value is None:
                    print(f"Missing value for {key} in metric: {metric}")

        # Handle cases where no engagement data is available
        if not metrics:
            flash("No engagement metrics available.", "danger")
            return render_template(
                'dashboard/influencer_menu/engagement.html',
                user_id=user_id,
                user=user,
                metrics=None,
            )

        # Pass metrics to the template
        return render_template(
            'dashboard/influencer_menu/engagement.html',
            user_id=user_id,
            user=user,
            metrics=metrics,
        )

    except Exception as e:
        # Handle unexpected errors and log them
        print(f"Error fetching engagement metrics: {e}")
        flash("An error occurred while fetching engagement metrics.", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

@influencer_boundary.route('/followers', methods=['GET', 'POST'])
def followers():
    """
    Route to display followers forecast for the user.
    """
    try:
        user_id = session.get('user_id')
        print(f"User ID from session: {user_id}")

        user = User.get_profile(user_id)

        # Ensure session is valid
        if not user_id or not user:
            flash("Session expired or user not found. Please log in again.", "danger")
            print("Session expired or user_id not found") 
            return redirect(url_for('navbar.login'))  # Redirect to login if session is invalid
        
        # Handle file upload if present
        if request.method == 'POST' and 'folder_zip' in request.files:
            file = request.files['folder_zip']
            if file and FollowerHist.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # upload_folder = current_app.config['UPLOAD_FOLDER']
                
                # # Ensure the uploads folder exists
                # if not os.path.exists(upload_folder):
                #     os.makedirs(upload_folder) 

                # file_path = os.path.join(upload_folder, filename)
                # file.save(file_path)

                # # Unzip the file
                # folder_path = os.path.join(upload_folder, filename.rsplit('.', 1)[0])
                # with zipfile.ZipFile(file_path, 'r') as zip_ref:
                #     for member in zip_ref.namelist():
                #         if 'connections/followers_and_following' in member:
                #             zip_ref.extract(member, folder_path)

                ## Process the extracted folder
                #followers_data = FollowerHist.process_uploaded_folder(folder_path)
                
                # Upload to Firebase Storage
                file_url = FollowerHist.upload_to_firebase(file, filename)
                
                if not file_url:
                    flash("Error uploading file to Firebase.", "danger")
                    return redirect(url_for('influencer_boundary.followers'))  # Redirect to avoid errors
                
                print("file url:", file_url)
                
                # Process from firebase
                followers_data = FollowerHist.process_uploaded_folder_from_firebase(file_url)

                if not followers_data:
                    flash('No follower data found for this user.', 'danger')
                    return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)

                forecast, error = FollowerHist.calculate_follower_growth(followers_data)
                if error:
                    flash(error, 'warning')
                    print(f"Error in calculating follower growth: {error}")

                print(f"Forecast data: {forecast}") 

                # Render the template with data
                return render_template(
                    'dashboard/influencer_menu/followers.html',
                    user_id=user_id,
                    user=user,
                    forecast=forecast,
                )
        # If no file is uploaded, return the followers page without any forecast
        return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)
    
    except Exception as e:
        # Handle unexpected errors
        print(f"Error in followers route: {e}")
        flash("An error occurred while fetching followers data.", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

@influencer_boundary.route('/post_page')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def post_page():
    return render_template('dashboard/influencer_menu/post_network.html')

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
        "resultsLimit": 50
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
    cu.create_user_json()
    cu.make_convo_file()
    cu.show_network()

    # Return success in JSON response
    return jsonify({
        'message': 'Post analysis completed.',
        'comment_tree_url': '/static/comment_tree.html'
    })

@influencer_boundary.route('/network')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def network():
    return render_template('dashboard/influencer_menu/network.html')

@influencer_boundary.route('/display_network', methods=['POST'])
def display_network():
    # Get the username from the POST request
    username = request.form.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Replace with your APIFY token
    APIFY_API_TOKEN = "apify_api_iGbTvXBtw6Lawc81y3AvuZnoyKZ2IT156FKk"

    # Initialize the ApifyClient with your API token
    client = ApifyClient(APIFY_API_TOKEN)

    # Prepare the Actor input for the Instagram Post scraper using the username entered in the form
    run_input = {
        "username": [username],  # Dynamically pass the username from the form
        "resultsLimit": 1,  # Get 1 post to fetch comments from
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
        "resultsLimit": 100,  # Modify this number as needed to capture more comments
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
    
    nw.generateGraphs(username)
    
    # Return the username in a JSON response (no need for full page render)
    return jsonify({
        'username': username,
    })

@influencer_boundary.route('/check-file', methods=['POST'])
def check_file():
    data = request.json
    file_path = data.get('file_path')
    if file_path and os.path.exists(file_path):
        return jsonify({"exists": True, "message": "File exists."})
    return jsonify({"exists": False, "message": "File does not exist."})

@influencer_boundary.route('/display_sentiment_graph')
def display_sentiment_graph():
    return render_template('dashboard/influencer_menu/sentimentgraph.html')

@influencer_boundary.route('/display_topic_graph')
def display_topic_graph():
    return render_template('dashboard/influencer_menu/topicnetwork.html')
