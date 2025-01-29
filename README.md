# FYP-24-S4-26 #
Run 'python app.py' 

# CREATE VIRTUAL ENVIRONTMENT #
python -m venv fyp_env

For MacOS:
source fyp_env/bin/activate # Activate the environment

FOR Windows:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
fyp_env\Scripts\activate  # Activate the environment

# LIBRARIES #:

# REQUIREMENTS #:
pip install flask
pip install python-dotenv
pip install matplotlib
pip install networkx
pip install mpld3
pip install faker
pip install firebase-admin
pip install bcrypt
pip install requests
pip install python-louvain

pip install scikit-learn 
pip install pandas
pip install plotly
pip install python-louvain
pip install seaborn
pip install bs4
pip install apify-client
pip install bertopic
pip install classes
pip install pyvis


# BOUNDARY #
- All the different routes of the website
    ## dashboard_boundary.py:  
        Routes for user dashboards.
        Functionality for different types of users (Business, Inlfuencer, Admin) to access and interact with their respective dashboards.
    
    ## navbar.py:
        Routes for User registration, login, and other general pages such as About and Customer support page

    ## profile_boundary.py:
        Routes for User Profile management

# ENTITY #
- The linkage to firebase and its functions to upload/get data to/from firebase
    ## admin.py
        Admin user management functions to manage accounts stored in firebase
        These functions interact with the Firestore database to retrieve and manipulate user data.

    ## followers_hist_entity.py
        Retrieving follower history data and calculating follower growth
        The data is pulled from a Firestore collection, processed, and then used for growth analysis and prediction.

    ## user.py
        Handles user-related actions within a system, particularly focused on Firebase Firestore.

# STATIC #
- All the CSS 

# TEMPLATES #
- All the html design for the pages

# GENERATE_FAKE_DATAS #
- All the files that is used to generate fake datas