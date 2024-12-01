from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from entity.user import User

navbar = Blueprint('navbar', __name__)

@navbar.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard_boundary.dashboard'))
    
    if request.method == 'POST':
        # user_id = request.form['user_id']
        account_type = request.form['account_type']
        # username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Handle the fields based on the account type
        if account_type == "business_analyst":
            business_name = request.form['business_name']
            business_number = request.form['business_number']
            username = business_name  # Using business_name as username
            
            # Ensure required fields for Business Analyst are filled
            if not business_name or not business_number:
                flash("Business Name and Business Number are required for Business Analysts.", "danger")
                return render_template('navbar/register.html')

        elif account_type == "influencer":
            username = request.form['username']  # Standard username for influencers

        # Check if password and confirm password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template('navbar/register.html')

        # Check if user with the same user_id or email already exists
        if User.user_exists(username, email):
            flash("Username or email already exists. Please use a different username or email.", "danger")
            return render_template('navbar/register.html')
        
        # Create user if password match
        if account_type == "business_analyst":
            User.create_user(username, email, password, account_type, business_number=business_number, business_name=business_name)
        else:
            User.create_user(username, email, password, account_type)
            
        flash("User registered successfully!", "success")
        return redirect(url_for('navbar.login'))

    return render_template('navbar/register.html')

@navbar.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard_boundary.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Authenticate and retrieve account_type
        authenticated, user_id, account_type = User.authenticate(username, password)

        # Authenticate using Firebase Authentication
        if authenticated:
            # Set user ID in session after successful authentication
            session['user_id'] = user_id
            session['account_type'] = account_type
            flash("Login successful", "success")
            return redirect(url_for('dashboard_boundary.dashboard'))
        else:
            flash("Failed to log in: Invalid username or password", "danger")

    return render_template('navbar/login.html')

@navbar.route('/about')
def about():
    return render_template('navbar/about.html')

@navbar.route('/customer_support')
def customer_support():
    return render_template('navbar/customer_support.html')