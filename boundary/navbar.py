from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_mail import Message
from entity.user import User
from entity.admin import Admin
import re

navbar = Blueprint('navbar', __name__)

@navbar.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard_boundary.dashboard'))
    
    # SUBMISSION OF REGISTRATION FORM
    if request.method == 'POST':
        account_type = request.form['account_type']
        email = request.form['email']
        gender = request.form['gender']
        age = request.form['age']
        niche = request.form['niche']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        username = request.form['username']

        # Check if the email format is valid
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash("Invalid email format. Please provide a valid email address.", "danger")
            return render_template('navbar/register.html')

        # Check if password and confirm password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template('navbar/register.html')

        # Check if user with the same user_id or email already exists
        if User.user_exists(username, email):
            flash("Username or email already exists. Please use a different username or email.", "danger")
            return render_template('navbar/register.html')
        
        User.create_user(username, email, gender, age, niche, password, account_type)
        #    
        flash("User registered successfully!", "success")
        return redirect(url_for('navbar.login')) # navbar/login endpoint

    
    # navigates to registration page if not logged in
    return render_template('navbar/register.html')

@navbar.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard_boundary.dashboard'))
    
    if request.method == 'POST':
        session.permanent = True

        username = request.form['username']
        password = request.form['password']

        # Authenticate and retrieve account_type
        authenticated, user_id, account_type, is_suspended = User.authenticate(username, password)

        # Authenticate using Firebase Authentication
        if authenticated:
            # Check if user is suspended
            if is_suspended:
                flash("Account suspended. Please contact support for assistance.", "danger")
                return render_template('navbar/login.html')
            
            # Set user ID in session after successful authentication
            session['user_id'] = user_id
            session['account_type'] = account_type
            flash("Login successful", "success")
            return redirect(url_for('dashboard_boundary.dashboard')) # Access this endpoint WHEN LOGIN SUCCEEDS
        else:
            flash("Failed to log in: Invalid username or password", "danger")


    # if not logging in yet, just display the login page
    return render_template('navbar/login.html')

@navbar.route('/about', methods=['GET'])
def about():
    testimonials = [testimonial for testimonial in Admin.get_testimonials() if testimonial['is_selected']] # Only get selected testimonials
    overview_content_about_us = Admin.get_overview_content()
    goals_heading = Admin.get_goals_heading()
    our_goals = Admin.get_our_goals()
    return render_template('navbar/about.html', 
                           testimonials=testimonials, 
                           overview_content_about_us=overview_content_about_us,
                           goals_heading=goals_heading,
                           our_goals=our_goals)

@navbar.route('/customer_support')
def customer_support():
    faq_content = Admin.get_faq_content()
    faqs = Admin.get_faqs()
    return render_template('navbar/customer_support.html',
                           faq_content=faq_content,
                           faqs=faqs)

@navbar.route('/submit_contact_form', methods=['POST'])
def submit_contact_form():
    from app import mail

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        query = request.form.get('query')

        # Validate form fields (add your validation logic)
        if not name or not email or not query:
            flash("Please fill in all the fields.", "danger")
            return redirect(url_for('navbar.customer_support'))  # Redirect back to the contact page (or a confirmation page)

        try:
            # Create a new message
            msg = Message('New Customer Support Query', 
                          recipients=['fyp24s426@gmail.com'])  # Replace with your support email address
            
            # Set the email body
            msg.html = f"""
                <p><strong>Customer Name:</strong> {name}</p>
                <p><strong>Customer Email:</strong> {email}</p>
                <p><strong>Message:</strong><br>{query}</p>
            """
            
            # Send the email using Flask-Mail
            mail.send(msg)
            
            flash("Your message has been sent successfully.", "success")
        except Exception as e:
            flash("There was an error submitting your form. Please try again later.", "danger") 
            print(f"Error occured: {e}")
        
        return redirect(url_for('navbar.customer_support'))  # Redirect to the index or customer support page with a success message
