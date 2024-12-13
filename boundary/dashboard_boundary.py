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
        # Check if the linked social media account
        linked_account = User.check_if_social_account_linked(user_id)

        # Fetch historical data for the user
        historical_data = FollowerHist.get_followers_hist(user_id) # ~~~~~~~unsure of followerHist~~~~~~~~~~~
        if historical_data:
            forecast, error = FollowerHist.calculate_follower_growth(historical_data)

            if not error:
                last_month_followers = forecast['historical_data'][-2] if len(forecast['historical_data']) > 1 else 0
                this_month_followers = forecast['historical_data'][-1]
                followers_gained = (
                    (this_month_followers - last_month_followers) 
                    if last_month_followers > 0 else 0
                )
                followers_gained_percentage = ( 
                    ((this_month_followers - last_month_followers) / last_month_followers) * 100 
                )
            else:
                followers_gained = None
                followers_gained_percentage = None
        else:
            followers_gained = None
            followers_gained_percentage = None

        return render_template(
            'dashboard/influencer_dashboard.html', # html page for influencer dashboard, with needed paras
            user_id=user_id, user=user, 
            followers_gained=followers_gained, 
            followers_gained_percentage=followers_gained_percentage,
            linked_account=linked_account
        )
    
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ADMIN DASHBOARD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif account_type == 'admin':
        all_users = Admin.get_all_users()

        # Calculate the counts
        total_users = len(all_users)
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
