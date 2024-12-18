from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from entity.user import User
from entity.followers_hist_entity import FollowerHist
import networkVisFinal, globals, influencer_centrality_ranking
import numpy as np


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

@influencer_boundary.route('/followers')
def followers():
    """
    Route to display followers forecast for the user.
    """
    try:
        user_id = session.get('user_id')
        user = User.get_profile(user_id)

        # Ensure session is valid
        if not user_id or not user:
            flash("Session expired or user not found. Please log in again.", "danger")
            return redirect(url_for('auth_boundary.login'))  # Redirect to login if session is invalid

        # CHECKING IF ACCOUNT IS LINKEDDDDDDDDDDDDDDDDDDDDDDDDDDD 
        if user['linked_social_account'] == "":
            flash("Please link to your social media acccount first", "danger")
            return redirect(url_for('dashboard_boundary.dashboard'))

        # Fetch historical data and calculate forecast
        historical_data = FollowerHist.get_followers_hist(user_id)
        if not historical_data:
            flash('No follower data found for this user.', 'danger')
            return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)

        forecast, error = FollowerHist.calculate_follower_growth(historical_data)
        if error:
            flash(error, 'warning')

        # Render the template with data
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

@influencer_boundary.route('/network')  # when 'Network Visualization' is clicked in the sidebar from influencer's side
def network():
    """
    Route to generate and display the network visualization for the user.
    """
    try:
        user_id = session.get('user_id')
        user = User.get_profile(user_id)
        username = user['username']
        print(username)

        # Ensure session is valid
        if not user_id or not user:
            flash("Session expired or user not found. Please log in again.", "danger")
            return redirect(url_for('auth_boundary.login'))  # Redirect to login if session is invalid

        # CHECKING IF ACCOUNT IS LINKEDDDDDDDDDDDDDDDDDDDDDDDDDDD 
        if user['linked_social_account'] == "":
            flash("Please link to your social media acccount first", "danger")
            return redirect(url_for('dashboard_boundary.dashboard'))

        # render the graph html files!
        nodes = networkVisFinal.plot_user_network_with_3d(username, save_as_html=True)
        
        if nodes == None:
            flash("An error occurred while generating the network visualization.", "danger")
            return render_template(
            'dashboard/influencer_menu/network.html',  
            user_id=user_id,
            user=user,
            graph = False
        )
        
        # Render the network visualization page
        return render_template(
            'dashboard/influencer_menu/network.html',  
            user_id=user_id,
            user=user,
            graph = True,
            central_nodes = nodes
        )
    except Exception as e:
        # Handle unexpected errors
        print(f"Error in network visualization: {e}")
        flash("An error occurred while generating the network visualization.", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

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
