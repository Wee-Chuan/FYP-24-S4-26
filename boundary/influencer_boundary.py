from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from entity.user import User
from entity.followers_hist_entity import FollowerHist
import networkVisFinal, globals

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

    # Get ranked influencers
    ranked_influencers = User.get_ranked_influencers()
    
    # Find the rank of the current user
    user_data = next((u for u in ranked_influencers if u['uid'] == user_id), None)
    if not user_data:
        flash('Unable to determine your rank.', 'danger')
        return render_template('dashboard/influencer_menu/ranking.html', user_id=user_id, user=user)

    user_rank = ranked_influencers.index(user_data) + 1  # Rankings are 1-indexed
    user_score = user_data['centrality_score']

    # Determine nearby users
    total_users = len(ranked_influencers)

    # Adjust start and end indices for users near the top or bottom
    start_index = max(0, user_rank - 6)  # Default: 5 users before + 1 current user
    end_index = min(total_users, user_rank + 5)  # Default: 5 users after
    
    if user_rank <= 5:  # Top 5 users
        start_index = 0  # Include all users from the beginning
        end_index = min(total_users, 11)  # Ensure up to 10 users if possible
    elif user_rank > total_users - 5:  # Bottom 5 users
        start_index = max(0, total_users - 11)  # Ensure up to the last 10 users
        end_index = total_users  # Include all users till the end

    nearby_users = ranked_influencers[start_index:end_index]
    nearby_users_labels = [u['username'] for u in nearby_users]
    nearby_users_followers = [u['follower_count'] for u in nearby_users]
    nearby_users_following = [u['following_count'] for u in nearby_users]
    nearby_users_scores = [u['centrality_score'] for u in nearby_users]

    # Top user comparison
    top_user = ranked_influencers[0] if user_rank != 1 else ranked_influencers[1]
    top_user_labels = [user_data['username'], top_user['username']]
    top_user_followers = [user_data['follower_count'], top_user['follower_count']]
    top_user_following = [user_data['following_count'], top_user['following_count']]
    top_user_scores = [user_data['centrality_score'], top_user['centrality_score']]
    score_diff = top_user['centrality_score'] - user_score


    #Bar chart
    chart_data = {
    "labels_nearby": nearby_users_labels,  # Usernames of nearby users
    "followers_nearby": nearby_users_followers,  # Follower counts of nearby users
    "following_nearby": nearby_users_following,  # Following counts of nearby users
    "labels_top": top_user_labels,  # Usernames for top influencer comparison
    "followers_top": top_user_followers,  # Follower counts for top influencer comparison
    "following_top": top_user_following,  # Following counts for top influencer comparison
}

    # Table data
    ranking_table = []
    for i, influencer in enumerate(ranked_influencers):
        rank = i + 1
        if rank <= 3 or (start_index <= i < end_index):  # Top 3 or nearby
            ranking_table.append({
                'rank': rank,
                'username': influencer['username'],
                'score': influencer['centrality_score'],
                'is_user': influencer['uid'] == user_id,
                'use_ellipsis': False
            })
        elif rank == 4 or rank == end_index + 1:  # Ellipses between skipped ranges
            ranking_table.append({'rank': None, 'username': '...', 'score': None, 'is_user': False, 'use_ellipsis': True})



    return render_template(
        'dashboard/influencer_menu/ranking.html',
        user_id=user_id,
        user=user,
        user_rank=user_rank,
        user_score=user_score,
        nearby_users_labels=nearby_users_labels,
        nearby_users_followers=nearby_users_followers,
        nearby_users_following=nearby_users_following,
        nearby_users_scores=nearby_users_scores,
        top_user_labels=top_user_labels,
        top_user_followers=top_user_followers,
        top_user_following=top_user_following,
        top_user_scores=top_user_scores,
        score_diff=score_diff,
        is_top_user=(user_rank == 1),
        ranking_table=ranking_table,
        chart_data=chart_data,
    )

    
# ========================================================== #


