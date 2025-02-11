from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from entity.user import User
import re

profile_boundary = Blueprint('profile_boundary', __name__)
    
@profile_boundary.route("/update_account", methods=['GET', 'POST'])
def update_account():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('navbar.login'))
    
    # Check if any data is changed
    current_user_data = User.get_profile(user_id)

    if current_user_data is None:
        flash("Error retrieving user profile", "danger")
        return redirect(url_for('dashboard_boundary.dashboard'))
    
    # Safely handle missing fields
    current_gender = current_user_data.get('gender', '') 
    current_age = current_user_data.get('age', '') 
    current_niche = current_user_data.get('niche', '')
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        gender = request.form['gender']
        age = request.form['age']
        niche = request.form['niche'] if current_user_data['account_type'] != "admin" else None
        password = request.form.get('password')  
        confirm_password = request.form['confirm_password']

        error_fields = []
        changes_made = False

        # Check if username has changed and if it exists
        if current_user_data['username'] != username:
            if User.user_exists(username, None): # Check by only username
                error_fields.append('username')
                flash("Username or email already exists. Please use a different username or email.", "danger")
            else:
                changes_made = True

        # Check if emails has changed and if it exists
        if current_user_data['email'] != email:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                error_fields.append('email')
                flash("Invalid email format. Please provide a valid email address.", "danger")
            else:
                if User.user_exists(None, email): # Check by email only
                    error_fields.append('email')
                    flash("Username or email already exists. Please use a different username or email.", "danger")
                else:
                    changes_made = True
        
        if current_gender != gender:
            changes_made = True

        if current_age != age:
            changes_made = True

        if current_user_data['account_type'] != 'admin' and current_niche != niche:
            changes_made = True

        # Handle password update 
        if password:
            # Check if password and confirm password match
            if password != confirm_password:
                error_fields.append('password')
                error_fields.append('confirm_password')
                flash("Passwords do not match!", "danger")

            # Password validation 
            password_pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
            if not re.match(password_pattern, password):
                error_fields.append('password')
                flash("Password must be at least 6 characters, include an uppercase letter, a lowercase letter, a number, and a special character!", "danger")
            else:
                changes_made = True
        
        # Handle errors
        if error_fields:
            return render_template('profile_page/update_account.html', user=current_user_data, error_fields=error_fields)
        
        # If there is changes, proceed
        if changes_made:
            # Call the update_user method with the new data
            User.update_user(user_id, username, email, gender, age, niche, password)
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