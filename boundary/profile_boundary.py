from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from entity.user import User
import bcrypt

profile_boundary = Blueprint('profile_boundary', __name__)
    
@profile_boundary.route("/update_account", methods=['GET', 'POST'])
def update_account():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('navbar.login'))
    
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

@profile_boundary.route("/link_social", methods=['GET', 'POST'])
def link_social():
    user_id = session.get('user_id')

    # Only logged-in users should be able to link social accounts
    if not user_id:
        flash('You must be logged in to link social media accounts.', 'danger')
        return redirect(url_for('navbar.login'))
    
    # Check if the social media account is already linked
    linked_account = User.check_if_social_account_linked(user_id)
    
    if request.method == 'POST':
        social_media = request.form.get('social_media')
        username = request.form.get('username')
        password = request.form.get('password')

        if not social_media or not username or not password:
            flash('Please provide both social media platform and login details.', 'danger')
            return redirect(url_for('profile_boundary.link_social'))
        
        # Check which platform to process
        platform = f"{social_media}_social_accounts"

        if linked_account == social_media:
            flash(f"This {social_media.capitalize()} account is already linked.", 'danger')
            return render_template('profile_page/link_social.html')

        # Retrieve the stored account details
        social_account = User.get_social_account(user_id, platform)
        if social_account:
            # Validate username and password
            stored_username = social_account.get('username')
            stored_password = social_account.get('password')  # Assumes password is hashed

            if username == stored_username and bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                User.update_linked_social(user_id, social_media)
                flash(f'{social_media.capitalize()} account linked successfully.', 'success')
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        else:
            flash(f"{social_media.capitalize()} account does not exist", "danger")
    
    return render_template('profile_page/link_social.html')