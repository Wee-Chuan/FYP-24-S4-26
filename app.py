import os

from flask import Flask, render_template, redirect, url_for, session, flash, request
from dotenv import load_dotenv
from boundary.navbar import navbar
from boundary.dashboard_boundary import dashboard_boundary
from boundary.profile_boundary import profile_boundary

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Register blueprints
app.register_blueprint(navbar)
app.register_blueprint(dashboard_boundary)
app.register_blueprint(profile_boundary)


@app.route('/')
def index():
    return render_template('index.html')
  
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id', None)
    session.pop('access_token', None)
    session.pop('threads_user_id', None)
    flash("You have been logged out", "info")

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)