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

        # Calculate the counts
        total_users = len(all_users)
        total_influencers = sum(1 for user in all_users if user['account_type'] == 'influencer')
        total_admin_accounts = sum(1 for user in all_users if user['account_type'] == 'admin')

        return render_template(
            'dashboard/system_admin_dashboard.html', 
            user_id=user_id, 
            user=user, 
            all_users=all_users,
            total_users=total_users,
            total_influencers=total_influencers,
            total_admin_accounts=total_admin_accounts
            )
    else:
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))
