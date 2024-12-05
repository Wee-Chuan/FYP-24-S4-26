from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify

from entity.user import User
from entity.admin import Admin
from entity.followers_hist_entity import FollowerHist

dashboard_boundary = Blueprint('dashboard_boundary', __name__)

@dashboard_boundary.route('/dashboard')
def dashboard():
    account_type = session.get('account_type')
    user_id = session.get('user_id') 
    user = User.get_profile(user_id)
    if account_type == 'business_analyst':
        return render_template('dashboard/business_dashboard.html', user_id=user_id, user=user)
    
    elif account_type == 'influencer':
        # Fetch historical data for the user
        historical_data = FollowerHist.get_followers_hist(user_id)
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
            'dashboard/influencer_dashboard.html', 
            user_id=user_id, user=user, 
            followers_gained=followers_gained, 
            followers_gained_percentage=followers_gained_percentage
        )
    
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

# ================ Admin-specific routes ================ #
@dashboard_boundary.route('/dashboard/admin/manage_accounts')
def manage_accounts():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()
    return render_template('dashboard/admin_menu/manage_accounts.html', all_users=all_users, current_page='manage_accounts')

@dashboard_boundary.route('/dashboard/admin/get_users')
def get_users():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()

    # Return the users as a JSON response
    return jsonify(all_users)

@dashboard_boundary.route('/dashboard/admin/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query', '').strip()  # Get the search query from URL parameters

    if not query:
        return jsonify({"error": "No search query provided"}), 400  # Return an error if query is empty
    
    
    results = Admin.search_users_by_query(query)

    return jsonify(results)  # Return the search results as JSON


@dashboard_boundary.route('/dashboard/admin/approve_user', methods=['POST', 'GET'])
def approve_user():
    # Check if the request is from an admin
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')  # Retrieve the user ID from the form data
        success, message = Admin.approve_user(user_id)  # Call Admin class to approve the user

        # Flash success or error message based on the outcome
        flash(message, "success" if success else "danger")

        # Redirect back to the 'approve_accounts' page
        return redirect(url_for('dashboard_boundary.approve_accounts'))

@dashboard_boundary.route('/dashboard/admin/approve_accounts')
def approve_accounts():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()
    business_analysts = [user for user in all_users if user['account_type'] == 'business_analyst']

    return render_template('dashboard/admin_menu/approve_accounts.html', business_analysts=business_analysts, current_page='approve_accounts')


@dashboard_boundary.route('/dashboard/admin/user/<string:user_id>', methods=['GET'])
def get_user_details(user_id):
    if session.get('account_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    user_data = Admin.get_user_details(user_id)
    print(user_data)
    if user_data:
        return jsonify(user_data)  # Return user data as JSON
    else:
        return jsonify({"error": "User not found"}), 404

@dashboard_boundary.route('/dashboard/admin/suspend_user/<user_id>', methods=['POST'])
def suspend_user(user_id):
    if session.get('account_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Call the suspend_user method from the Admin class
    result = Admin.suspend_user(user_id)
    # success, message = Admin.suspend_user(user_id)

    # flash(message, "success" if success else "danger")
    return jsonify(result)
    # # Redirect back to the 'approve_accounts' page
    # return redirect(url_for('dashboard_boundary.manage_accounts'))
    
# ======================================================= #

# ================ Influencer dashbaord menu ================ #
@dashboard_boundary.route('/dashboard/engagement')
def engagement():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)
    # You can add logic to fetch engagement data here
    return render_template('dashboard/influencer_menu/engagement.html', user_id=user_id, user=user)

@dashboard_boundary.route('/dashboard/followers')
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

@dashboard_boundary.route('/dashboard/network')
def network():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)
    interactive_plot   = User.visualize_followers_network(user['username'])

    # You can add logic to fetch network data here
    return render_template('dashboard/influencer_menu/network.html', user_id=user_id, user=user, interactive_plot=interactive_plot)
# ========================================================== #


# ================ Business dashbaord menu ================= #


# ========================================================== #


