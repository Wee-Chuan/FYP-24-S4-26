import os
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for, session, flash, jsonify, send_from_directory
from dotenv import load_dotenv
from boundary.navbar import navbar
from boundary.dashboard_boundary import dashboard_boundary
from boundary.admin_boundary import admin_boundary
from boundary.influencer_boundary import influencer_boundary
from boundary.profile_boundary import profile_boundary
from boundary.rate_and_review_boundary import rate_and_review_boundary
from entity.admin import Admin

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Set session timeout to 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)

# Register blueprints
app.register_blueprint(navbar)
app.register_blueprint(dashboard_boundary)
app.register_blueprint(admin_boundary)
app.register_blueprint(influencer_boundary)
app.register_blueprint(profile_boundary)
app.register_blueprint(rate_and_review_boundary)

@app.before_request
def make_session_permanent():
    """Make the session permanent to respect the lifetime configuration."""
    session.permanent = True

@app.route('/')
def index():
    hero_content = Admin.get_hero_content()
    about_content = Admin.get_about_content()
    feature_content = Admin.get_features_content()
    influencer_features = Admin.get_influencer_features()
    if 'user_id' in session:
        return redirect(url_for('dashboard_boundary.dashboard'))
    return render_template('index.html', 
                           hero_content=hero_content, 
                           about_content=about_content, 
                           feature_content=feature_content,
                           influencer_features=influencer_features,)
  
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    flash("You have been logged out", "info")

    return redirect(url_for('index'))

# Custom route to serve files from 'templates/dashboard/influencer_menu'
@app.route('/dashboard/influencer_menu/<filename>')
def serve_graphs(filename):
    # Serve the file from the 'templates/dashboard/influencer_menu' folder
    return send_from_directory(
        os.path.join(app.root_path, 'templates', 'dashboard', 'influencer_menu'), 
        filename
    )

if __name__ == "__main__":
    app.run(debug=True)
