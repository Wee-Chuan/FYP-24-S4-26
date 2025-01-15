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
                    success = Admin.update_influencer_feature(feature_id, title, paragraph)
            
            # Handle deleted features
            deleted_features = request.form.get("deleted_features")
            if deleted_features:
                deleted_feature_ids = deleted_features.split(',')
                for feature_id in deleted_feature_ids:
                    success = Admin.delete_influencer_feature(feature_id)
            
            # Handle newly added features
            added_features = request.form.get("added_features")
            if added_features:
                added_feature_ids = added_features.split(',')
                for feature_id in added_feature_ids:
                    title = request.form.get(f"influencer_title_{feature_id}")
                    paragraph = request.form.get(f"influencer_paragraph_{feature_id}")
                    print("Feature ID:", feature_id)
                    success = Admin.add_influencer_feature(title, paragraph)
        else:
            flash("Invalid section", "error")
            return redirect(url_for('admin_boundary.manage_landing_page'))

        # Handle success or failure
        if success:
            flash(f"{section.capitalize()} content updated successfully!", "success")
        else:
            flash(f"Failed to update {section} content", "danger")
        
        return redirect(url_for('admin_boundary.manage_landing_page', section=section))

@admin_boundary.route('/admin/manage-about-us-page', methods=['GET', 'POST', 'PUT'])
def manage_about_us_page():
    # Get the section from query parameters (default to 'overview' if not provided) 
    current_section = request.args.get('section', 'overview') 

    # Fetch content for each section from the Admin model
    overview_content = Admin.get_overview_content() 
    goals_heading = Admin.get_goals_heading()  
    our_goals = Admin.get_our_goals()
    testimonials = Admin.get_testimonials()

    # Handle GET requests: Render the template with the fetched data
    if request.method == 'GET':
        return render_template(
            'dashboard/admin_menu/manage_about_us_page.html',
            current_section=current_section,
            overview_content=overview_content,
            goals_heading=goals_heading,
            our_goals=our_goals,
            testimonials=testimonials
        )
    
    # Handle POST requests for form submissions
    if request.method == 'POST':
        success = False  # Flag to track success of updates

        # Determine the section
        section = request.args.get('section')
        
        # Handle form for 'overview' section 
        if section == 'overview':
            # Update overview content
            overview_title = request.form['overview_title']
            overview_paragraph = request.form['overview_paragraph']
            overview_paragraph2 = request.form['overview_paragraph2']
            success = Admin.update_overview_content(overview_title, overview_paragraph, overview_paragraph2) 
            
        # Handle form for 'goals' section
        elif section == 'goals':
            # Update main goals title
            goals_heading = request.form['goals_heading']
            success = Admin.update_goals_heading(goals_heading)  
            
            # Extract data from the form for goals
            goals_data = request.form.to_dict(flat=False)
            for key, value in goals_data.items():
                if key.startswith('goal_title_'):  # Identify the goal ID
                    goal_id = key.split('_')[-1]
                    title = request.form.get(f'goal_title_{goal_id}')
                    description = request.form.get(f'goal_description_{goal_id}')
                    icon = request.form.get(f'goal_icon_{goal_id}')
                    # Update each goal based on its ID
                    success = Admin.update_our_goals(goal_id, title, description, icon)

        # Handle form for 'testimonials' section
        elif section == 'testimonials':
            # Get all testimonials selected by the admin
            selected_testimonial_ids = [
                key.split('_')[-1]
                for key in request.form if key.startswith('testimonial_display')
            ]

            # Fetch currently selected testimonial IDs from the database
            current_selected_ids = {testimonial['id'] for testimonial in testimonials if testimonial['is_selected']}

            # Identify changes: testimonials to select and deselect
            to_select = set(selected_testimonial_ids) - current_selected_ids
            to_deselect = current_selected_ids - set(selected_testimonial_ids)
            
            # If there are changes, update testimonials in Firestore
            if to_select or to_deselect:
                success = True
                for review_id in to_select:
                    success = Admin.update_testimonial_selection(review_id, is_selected=True)
                for review_id in to_deselect:
                    success = Admin.update_testimonial_selection(review_id, is_selected=False)
        
        # After processing, reload the page with updated data
        if success:
            flash(f"{section.capitalize()} content updated successfully!", "success")
        else:
            flash(f"Failed to update {section} content", "danger")
        
        return redirect(url_for('admin_boundary.manage_about_us_page', section=section))

@admin_boundary.route('/admin/manage-customer-support-page', methods=['GET', 'POST', 'PUT'])
def manage_customer_support_page():
    # Get the section from query parameters (default to 'overview' if not provided) 
    current_section = request.args.get('section', 'faqs')

    faq_content = Admin.get_faq_content()
    faqs = Admin.get_faqs()

    # Handle GET requests: Render the template with the fetched data
    if request.method == 'GET':
        return render_template(
            'dashboard/admin_menu/manage_customer_support_page.html',
            current_section=current_section,
            faq_content=faq_content,
            faqs=faqs
        )
    
    # Handle POST requests for form submissions
    if request.method == 'POST':
        success = False  # Flag to track success of updates

        # Determine the section
        section = request.args.get('section')
        
        # Handle form for 'overview' section 
        if section == 'faqs':
            # Update overview content
            main_heading = request.form['main_heading']
            main_paragraph = request.form['main_paragraph']
            faq_heading = request.form['faq_heading']
            faq_paragraph = request.form['faq_paragraph']
            contact_heading = request.form['contact_heading']
            contact_paragraph = request.form['contact_paragraph']
            success = Admin.update_faq_content(faq_heading, faq_paragraph, contact_heading, contact_paragraph, main_heading, main_paragraph)

            # Handle updated FAQs
            faqs = request.form.to_dict(flat=False)
            for key, value in faqs.items():
                if key.startswith('faq_question_'):
                    faq_id = key.split('_')[-1]
                    question = request.form.get(f'faq_question_{faq_id}')
                    answer = request.form.get(f'faq_answer_{faq_id}')
                    if question and answer:
                        success = Admin.update_faq(faq_id, question, answer)

            # Handle added FAQs
            added_faqs = request.form.get('added_faqs', '')
            if added_faqs:
                added_faqs_id = added_faqs.split(',')
                for faq_id in added_faqs_id:
                    if faq_id:
                        question = request.form.get(f'faq_question_{faq_id}', '')
                        answer = request.form.get(f'faq_answer_{faq_id}', '')
                        if question and answer:
                            success = Admin.add_faq(question, answer)

            # Handle deleted FAQs
            deleted_faqs = request.form.get('deleted_faqs', '')
            if deleted_faqs:
                deleted_faqs_ids = deleted_faqs.split(',')
                for faq_id in deleted_faqs_ids:
                    if faq_id:
                        success = Admin.delete_faq(faq_id) 

        # Return an appropriate response based on success or failure
        if success:
            flash('FAQs updated successfully!', 'success')
        else:
            flash('Failed to update FAQs. Please try again.', 'error')

        return redirect(url_for('admin_boundary.manage_customer_support_page', section=section))

            
        
# ======================================================= #