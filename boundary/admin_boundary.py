from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify

from entity.admin import Admin

admin_boundary = Blueprint('admin_boundary', __name__)

# ================ Admin-specific routes ================ #
@admin_boundary.route('/dashboard/admin/manage_accounts')
def manage_accounts():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()
    return render_template('dashboard/admin_menu/manage_accounts.html', all_users=all_users, current_page='manage_accounts')

@admin_boundary.route('/dashboard/admin/get_users')
def get_users():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()

    # Return the users as a JSON response
    return jsonify(all_users)

@admin_boundary.route('/dashboard/admin/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query', '').strip()  # Get the search query from URL parameters
    filter_type = request.args.get('filter', 'all')

    if not query:
        return jsonify({"error": "No search query provided"}), 400  # Return an error if query is empty
    
    try:
        # Search users by username using the method from the Admin class
        results = Admin.search_users_by_query(query, account_type=filter_type)
        
        # Check if results are valid
        if results is None:
            print(f"No results found for query: '{query}' with filter: '{filter_type}'")
            return jsonify({"error": "No users found"}), 404  # Return error if no users found
        elif not results:
            print(f"Empty result set for query: '{query}' with filter: '{filter_type}'")
            return jsonify({"error": "No users match the query and filter"}), 404  # Return error if empty results

        # Return the search results as JSON
        print(f"Found {len(results)} user(s) matching query: '{query}' with filter: '{filter_type}'")
        return jsonify(results)

    except Exception as e:
        print((f"Error occurred while searching users: {str(e)}"))
        return jsonify({"error": "An error occurred while processing your request"}), 500  # Return error if exception occurs

@admin_boundary.route('/dashboard/admin/get_filtered_users')
def get_filtered_users():
    query = request.args.get('query', '')
    filter_type = request.args.get('filter', 'all')

    # Get filtered users based on query and account type filter
    user_list = Admin.filter_users(query)
    if filter_type != 'all':
        user_list = [user for user in user_list if user['account_type'] == filter_type]

    return jsonify(user_list)

# Function to approve the business user account
@admin_boundary.route('/dashboard/admin/approve_user', methods=['POST', 'GET'])
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
        return redirect(url_for('admin_boundary.approve_accounts'))

# Function to display business accounts who needs approval page
@admin_boundary.route('/dashboard/admin/approve_accounts')
def approve_accounts():
    if session.get('account_type') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    all_users = Admin.get_all_users()
    business_analysts = [user for user in all_users if user['account_type'] == 'business_analyst']

    return render_template('dashboard/admin_menu/approve_accounts.html', business_analysts=business_analysts, current_page='approve_accounts')


@admin_boundary.route('/dashboard/admin/get_user_details/<string:user_id>', methods=['GET'])
def get_user_details(user_id):
    if session.get('account_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    user_data = Admin.get_user_details(user_id)
    if user_data:
        return jsonify(user_data)  # Return user data as JSON
    else:
        return jsonify({"error": "User not found"}), 404

@admin_boundary.route('/dashboard/admin/suspend_user/<user_id>', methods=['POST'])
def suspend_user(user_id):
    if session.get('account_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Call the suspend_user method from the Admin class
    result = Admin.suspend_user(user_id)
    # success, message = Admin.suspend_user(user_id)

    # flash(message, "success" if success else "danger")
    return jsonify(result)
    # # Redirect back to the 'approve_accounts' page
    # return redirect(url_for('admin_boundary.manage_accounts'))

@admin_boundary.route('/admin/manage-landing-page', methods=['GET', 'POST', 'PUT'])
def manage_landing_page():
    # Fetch all content for the page
    hero_content = Admin.get_hero_content()
    about_content = Admin.get_about_content()
    features_content = Admin.get_features_content()

    # Fetch influencer features for the 'features' section
    influencer_features = Admin.get_influencer_features() if features_content else []

    # Determine the current section
    current_section = request.args.get('section', 'hero')

    # Select the content for the current section
    if current_section == 'hero':
        current_content = hero_content
    elif current_section == 'about':
        current_content = about_content
    elif current_section == 'features':
        current_content = features_content
    else:
        return jsonify({"error": "Invalid section"}), 400

    if request.method == 'GET':
        # Render the template with all content
        return render_template(
            'dashboard/admin_menu/manage_landing_page.html',
            influencer_features=influencer_features,
            current_section=current_section,
            current_content=current_content
        )

    elif request.method == 'POST':
        # Determine which section is being updated
        section = request.form.get("section") 

        # Update the corresponding section
        if section == "hero":
            data = {
                "title": request.form.get("title"),
                "paragraph": request.form.get("paragraph"),
            }
            success = Admin.update_hero_content(data)

        elif section == "about":
            data = {
                "title": request.form.get("title"),
                "paragraph": request.form.get("paragraph"),
            }
            success = Admin.update_about_content(data)

        elif section == "features":
            data = {
                "title": request.form.get("title"),
                "paragraph": request.form.get("paragraph"),
            }
            success = Admin.update_features_content(data)

            # Update influencer features
            influencer_features = request.form.to_dict(flat=False)
            for key, value in influencer_features.items():
                if key.startswith('influencer_title_'):
                    feature_id = key.split('_')[-1]
                    title = request.form.get(f'influencer_title_{feature_id}')
                    paragraph = request.form.get(f'influencer_paragraph_{feature_id}')
                    # Update each influencer feature based on its ID
                    Admin.update_influencer_feature(feature_id, title, paragraph)

        else:
            return jsonify({"error": "Invalid section"}), 400

        # Handle success or failure
        if success:
            return redirect(url_for('admin_boundary.manage_landing_page', section=section))
        else:
            return jsonify({"error": f"Failed to update {section} content"}), 500

@admin_boundary.route('/admin/manage-about-us-page', methods=['GET', 'POST', 'PUT'])
def manage_about_us_page():
    overview_content = Admin.get_overview_content()
    goals_heading = Admin.get_goals_heading()  
    our_goals = Admin.get_our_goals()

    if request.method == 'GET':
        # Render the template with all content
        return render_template(
            'dashboard/admin_menu/manage_about_us_page.html',
            overview_content=overview_content,
            goals_heading=goals_heading,
            our_goals=our_goals
        )
    
    # Handle POST requests for form submissions
    if request.method == 'POST':
        section = request.args.get('section', '')
        
        if section == 'overview':
            # Update overview content
            overview_title = request.form['overview_title']
            overview_paragraph = request.form['overview_paragraph']
            Admin.update_overview_content(overview_title, overview_paragraph) 
            
        elif section == 'goals_heading':
            # Update main goals title
            goals_heading = request.form['goals_heading']
            Admin.update_goals_heading(goals_heading)  
            
        elif section == "goals":
            # Extract data from the form for goals
            goals_data = request.form.to_dict(flat=False)
            for key, value in goals_data.items():
                if key.startswith('goal_title_'):  # Identify the goal ID
                    goal_id = key.split('_')[-1]
                    title = request.form.get(f'goal_title_{goal_id}')
                    description = request.form.get(f'goal_description_{goal_id}')
                    icon = request.form.get(f'goal_icon_{goal_id}')
                    # Update each goal based on its ID
                    Admin.update_our_goals(goal_id, title, description, icon)

        elif section == 'testimonials':
            # Update testimonials 
            pass
        
        # After processing, reload the page with updated data
        return redirect(url_for('admin_boundary.manage_about_us_page'))


# ======================================================= #