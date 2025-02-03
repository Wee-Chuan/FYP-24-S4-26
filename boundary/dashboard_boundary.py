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
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INFLUENCER DASHBOARD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if account_type == 'influencer':
        
        return render_template(
            'dashboard/influencer_dashboard.html', # html page for influencer dashboard, with needed paras
            user_id=user_id, 
            user=user
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
