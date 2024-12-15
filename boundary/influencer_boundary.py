from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import networkVis
from entity.user import User
from entity.followers_hist_entity import FollowerHist

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

        # Fetch engagement metrics data from Firestore
        metrics_ref = db.collection('engagement_metrics') \
            .where('user_id', '==', user_id).order_by('date').stream()
        metrics = [doc.to_dict() for doc in metrics_ref]

        # Handle cases where no engagement data is available
        if not metrics:
            flash("No engagement metrics available.", "warning")
            return render_template(
                'dashboard/influencer_menu/engagement_metrics.html',
                user_id=user_id,
                user=user,
                metrics=None,
            )

        # Process the data (e.g., serialize dates)
        processed_metrics = [
            {
                **metric,
                "date": metric["date"].strftime("%Y-%m-%d")  # Format the date for display
            }
            for metric in metrics
        ]

        # Pass metrics to the template
        return render_template(
            'dashboard/influencer_menu/engagement_metrics.html',
            user_id=user_id,
            user=user,
            metrics=processed_metrics,
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

        # Ensure session is valid
        if not user_id or not user:
            flash("Session expired or user not found. Please log in again.", "danger")
            return redirect(url_for('auth_boundary.login'))  # Redirect to login if session is invalid

        # Generate the interactive plot for the user's network
        interactive_plot = User.visualize_followers_network(user['username'])

        # Check if the interactive plot was created successfully
        if not interactive_plot:
            flash("Unable to generate network visualization.", "warning")

        # Render the network visualization page
        return render_template(
            'dashboard/influencer_menu/network.html',  # Ensure this template exists
            user_id=user_id,
            user=user,
            interactive_plot=interactive_plot,
        )
    except Exception as e:
        # Handle unexpected errors
        print(f"Error in network visualization: {e}")
        flash("An error occurred while generating the network visualization.", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))

# ========================================================== #
