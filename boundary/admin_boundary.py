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
    
# ======================================================= #