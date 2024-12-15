from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from entity.user import User

rate_and_review_boundary = Blueprint('rate_and_review_boundary', __name__)

@rate_and_review_boundary.route('/rate_and_review', methods=['GET', 'POST'])
def rate_and_review():
    user_id = session.get('user_id')
    user = User.get_profile(user_id)
    username = user['username']

    if request.method == 'POST':
        rating = request.form.get('rating')
        review = request.form.get('review')

        # Save the review
        if rating and review:
            User.save_rate_and_review(user_id, rating, review, username)
            flash('Review Submitted', 'success')
            return redirect(url_for('dashboard_boundary.dashboard'))
        else:
            flash('Please provide both rating and review', 'error')
    
    return render_template('rate_and_review/rate_and_review.html')

