from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import networkVis
from entity.user import User
from entity.followers_hist_entity import FollowerHist

influencer_boundary = Blueprint('influencer_boundary', __name__)

# ================ Influencer dashbaord menu ================ #
@influencer_boundary.route('/dashboard/engagement')
def engagement():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)
    # You can add logic to fetch engagement data here
    return render_template('dashboard/influencer_menu/engagement.html', user_id=user_id, user=user)

@influencer_boundary.route('/dashboard/followers')
def followers():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)

    historical_data = FollowerHist.get_followers_hist(user_id)
    if not historical_data:
        flash('No follower data found for this user.', 'danger')
        return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)
    
    forecast, error = FollowerHist.calculate_follower_growth(historical_data)
    if error:
        flash(error, 'warning')
        return render_template('dashboard/influencer_menu/followers.html', user_id=user_id, user=user)

    return render_template(
        'dashboard/influencer_menu/followers.html', 
        user_id=user_id, 
        user=user, 
        forecast=forecast
    )

@influencer_boundary.route('/dashboard/network')
def network():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)
    interactive_plot   = User.visualize_followers_network(user['username'])
    networkVis.main()

    # You can add logic to fetch network data here
    return render_template('dashboard/influencer_menu/network.html', user_id=user_id, user=user, interactive_plot=interactive_plot)
# ========================================================== #