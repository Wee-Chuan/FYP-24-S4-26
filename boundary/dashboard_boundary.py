from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify

from entity.user import User
from entity.admin import Admin
from entity.followers_hist_entity import FollowerHist

dashboard_boundary = Blueprint('dashboard_boundary', __name__)

@dashboard_boundary.route('/dashboard') # endpoint reached when successful login
def dashboard():
    account_type = session.get('account_type')
    user_id = session.get('user_id') 
    user = User.get_profile(user_id)
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BUSINESS ANALYST DASHBOARD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if account_type == 'business_analyst':
        return render_template('dashboard/business_dashboard.html', user_id=user_id, user=user)
    
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INFLUENCER DASHBOARD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif account_type == 'influencer':
        
        # if user['linked_social_account']:
        #     # get the ranking
        #     ranking_dict = influencer_centrality_ranking.build_graph_and_calculate_centrality()
        #     rank = next((i for i, key in enumerate(ranking_dict.keys()) if key == user['username']), None) + 1
        # else:
        #     rank = "Not available"
        
        # ~~~ can be removed ~~~ #
        # # Check if the linked social media account
        # linked_account = User.check_if_social_account_linked(user_id)

        # Fetch total engagement metrics for the user
        metrics = User.visualize_engagement_metrics(user_id)
    
        if metrics:
            total_likes = sum([metric['likes'] for metric in metrics])
            total_comments = sum([metric['comments'] for metric in metrics])
            total_shares = sum([metric['shares'] for metric in metrics])
        else:
            total_likes = total_comments = total_shares = 0

        return render_template(
            'dashboard/influencer_dashboard.html', # html page for influencer dashboard, with needed paras
            user_id=user_id, user=user,  
            # linked_account=linked_account,
            total_likes=total_likes, 
            total_comments=total_comments, 
            total_shares=total_shares,
            # rank = rank
        )
    
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ADMIN DASHBOARD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif account_type == 'admin':
        all_users = Admin.get_all_users()

        # Filter out admins
        non_admin_users = [user for user in all_users if user['account_type'] != 'admin']

        # Calculate the counts
        total_users = len(non_admin_users)
        total_influencers = sum(1 for user in all_users if user['account_type'] == 'influencer')
        total_business_accounts = sum(1 for user in all_users if user['account_type'] == 'business_analyst')

        return render_template(
            'dashboard/system_admin_dashboard.html', 
            user_id=user_id, 
            user=user, 
            all_users=all_users,
            total_users=total_users,
            total_influencers=total_influencers,
            total_business_accounts=total_business_accounts
            )
    else:
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))
