import os

from flask import Blueprint, render_template, redirect, url_for, session, flash, request, current_app
from entity.user import User
from entity.followers_hist_entity import FollowerHist
import networkVisFinal, globals, influencer_centrality_ranking
import csv
from apify_client import ApifyClient

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

@influencer_boundary.route('/network')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def network():
    return render_template('dashboard/influencer_menu/network.html')


from flask import render_template, request
import csv
from apify_client import ApifyClient

@influencer_boundary.route('/display_network', methods=['POST'])
def display_network():
    # Get the username from the POST request
    username = request.form['username']

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
        "resultsLimit": 1,  # Modify this number as needed to capture more comments
    }

    # Run the Actor and wait for it to finish
    run = client.actor("SbK00X0JYCPblD2wp").call(run_input=run_input)

    # Open a CSV file to save the comments data
    with open('commentData.csv', 'w', newline='', encoding='utf-8') as csvfile:
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

    print("All comments saved to commentData.csv")
    
    # Return the template and pass the username as context only after all work is done
    return render_template('dashboard/influencer_menu/network.html', username=username, fetched=True)
    
@influencer_boundary.route('/dashboard/ranking')
def ranking():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)  # Fetch user profile using your custom method
    username = user['username']

    # CHECKING IF ACCOUNT IS LINKEDDDDDDDDDDDDDDDDDDDDDDDDDDD 
    if user['linked_social_account'] == "":
        flash("Please link to your social media acccount first", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

    # Get ranked influencers (assuming it returns a dictionary {username: centrality_score})
    ranked_influencers = influencer_centrality_ranking.build_graph_and_calculate_centrality()

    # Sort influencers by centrality score in descending order
    sorted_influencers = sorted(ranked_influencers.items(), key=lambda x: x[1], reverse=True)

    # Prepare top 3 influencers
    top_3_users = [
        {"rank": i + 1, "username": user, "score": score}
        for i, (user, score) in enumerate(sorted_influencers[:3])
    ]

    # Find the current user's rank and score
    user_rank = next((i + 1 for i, (user, _) in enumerate(sorted_influencers) if user == username), None)
    user_score = ranked_influencers.get(username, 0)
    score_diff = ranked_influencers.get(sorted_influencers[0][0], 0) - user_score if user_rank != 1 else None

    # Get 3 users above and below the current user (if available)
    if user_rank:
        surrounding_indices = range(max(0, user_rank - 4), min(len(sorted_influencers), user_rank + 3))
        surrounding_users = [
            {"rank": i + 1, "username": user, "score": score}
            for i, (user, score) in enumerate(sorted_influencers) if i in surrounding_indices
        ]
    else:
        surrounding_users = []

    return render_template(
        'dashboard/influencer_menu/ranking.html',
        username=username,
        top_3_users=top_3_users,
        surrounding_users=surrounding_users,
        current_user=username,
        user_rank=user_rank,
        user_score=user_score,
        score_diff=score_diff,
    )
