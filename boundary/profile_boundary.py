from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from entity.user import User

profile_boundary = Blueprint('profile_boundary', __name__)

@profile_boundary.route("/profile")
def profile():
    user_id = session.get('user_id')
    print("Session user_id:", user_id)

    if user_id:
        user_data = User.get_profile(user_id)
        if user_data:
            return render_template('profile_page/profile.html', user=user_data)
        else:
            flash("User not found.", "danger")
            return redirect(url_for('dashboard_boundary.dashboard'))
    else:
        flash("User not logged in.", "danger")
        return redirect(url_for('auth.login'))
    
@profile_boundary.route("/update_account", methods=['GET', 'POST'])
def update_account():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('auth.login'))
    
    # Check if any data is changed
    current_user_data = User.get_profile(user_id)
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form.get('password')  
        confirm_password = request.form['confirm_password']
        account_type = request.form['account_type'] 

        # Only fetch business-specific fields if the user is a business account
        business_name = request.form.get('business_name') if account_type == 'business_analyst' else None
        business_number = request.form.get('business_number') if account_type == 'business_analyst' else None

        changes_made = False

        if current_user_data['username'] != username:
            changes_made = True
        if current_user_data['email'] != email:
            changes_made = True
        if current_user_data['account_type'] != account_type:
            changes_made = True

        if password:  
            # Check if password and confirm_password match
            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('profile_boundary.update_account'))
            changes_made = True

        # Check for changes in business-specific fields
        if account_type == 'business_analyst':
            if current_user_data.get('business_name') != business_name:
                changes_made = True
            if current_user_data.get('business_number') != business_number:
                changes_made = True

        # If there is changes
        if changes_made:
            # Call the update_user method with the new data
            User.update_user(user_id, username, email, password, account_type, business_name, business_number)
            flash("Account details updated successfully!", "success")
        else:
            flash("No changes were made to your account.", "info")  # Notify the user

        return redirect(url_for('profile_boundary.update_account')) # Redirect to profile page

    # If GET request, fetch current user details
    current_user_data = User.get_profile(user_id)

    return render_template('profile_page/update_account.html', user=current_user_data)

@profile_boundary.route("/delete_account", methods=['GET', 'POST'])
def delete_account():
    user_id = session.get('user_id')

    # Error check
    if user_id is None:
        flash('You need to be logged in to delete your account.', 'error')
        return redirect(url_for('login'))

    if user_id:
        User.delete_account(user_id)
        flash('Your account has been successfully deleted.', 'success')

        session.pop('user_id', None) # End session
    else:
        flash('Account not found.', 'error')

    return redirect(url_for('index'))