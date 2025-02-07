# **Project Title: FYP-24-S4-26**

---

Before running the app, ensure that you have the following installed:
- **Python 3.x**
- **pip** (Python package manager)
- **Virtual environment** (recommended for isolating dependencies)

---

## **Setting Up the Project**
### **1. Clone the Repository**

First, clone the repository to your local machine:

```bash
git clone https://github.com/Wee-Chuan/FYP-24-S4-26.git
cd FYP-24-S4-26
```

### **2. Create Virtual Environment**
#### For MacOS:
```bash
python3 -m venv fyp_env
source fyp_env/bin/activate
```

#### FOR Windows:
```bash
python -m venv fyp_env
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
fyp_env\Scripts\activate
```

This command will create a virtual environment called fyp_env and activate it. You’ll see (fyp_env) in your terminal prompt.

### **3. Install Required Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set up environment variables**
#### To interact with Firebase and configure the app, create a .env file in the root directory of your project.
```bash
FLASK_SECRET_KEY="your_secret_key_here"
GOOGLE_CLOUD_TYPE="your_google_cloud_type_here"
GOOGLE_CLOUD_PROJECT_ID="your_project_id_here"
GOOGLE_CLOUD_PRIVATE_KEY_ID="your_google_cloud_private_key_id_here"
GOOGLE_CLOUD_PRIVATE_KEY="your_google_cloud_private_key_here"
GOOGLE_CLOUD_CLIENT_EMAIL="your_google_cloud_client_email_here"
GOOGLE_CLOUD_CLIENT_ID="your_google_cloud_client_id_here"
GOOGLE_CLOUD_AUTH_URI="your_google_cloud_auth_uri_here"
GOOGLE_CLOUD_TOKEN_URI="your_google_cloud_token_uri_here"
GOOGLE_CLOUD_AUTH_PROVIDER_X509_CERT_URL="your_google_cloud_auth_provider_x509_cert_url_here"
GOOGLE_CLOUD_CLIENT_X509_CERT_URL="your_google_cloud_client_x509_cert_url_here"
GOOGLE_CLOUD_UNIVERSE_DOMAIN="your_google_cloud_universe_domain_here"
MAIL_USERNAME="your_email_username_here"
MAIL_PASSWORD="your_email_password_here"
FIREBASE_API_KEY="your_firebase_api_key"
```
> **Important:**  
> - Ensure that the `.env` file is **not** committed to version control (e.g., Git).  
> - Add `.env` to your `.gitignore` file to prevent exposing sensitive information.  
> - This file contains critical credentials (e.g., private keys, email passwords). Keep it **private** and **secure**.

> **Important**
> - Ensure that the `MAIL_PASSWORD` value in the .env file is correct. For Gmail users, if you have 2-step verification enabled, you may need to generate an App Password instead of using your regular Gmail password.

### **5. Run the Flask Application**
#### Once the dependencies are installed and the environment variables are set, you can start the Flask server:
```bash
python app.py
```
#### This will start the Flask development server, and you should see output like:
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

### **6. Access the Application**
#### Open your web browser and go to:
```bash
http://127.0.0.1:5000/
```

This will load the homepage of the Flask app.

### **7. Stop the Flask Server**
To stop the Flask server, you can press CTRL+C in your terminal.

### Troubleshooting
* If you encounter issues with dependencies, ensure that all packages are installed in your virtual environment.
* If the app doesn't run, check for errors in the terminal output and verify that your environment variables are properly set.
* Ensure you have the correct Firebase credentials and keys for integration.

### How to Get the .env File Credentials
- For Firebase:
  - If the app uses Firebase, the credentials can be accessed from your Firebase Console (under **Project Settings > Service Accounts > Firebase Admin SDK**).
  - Download the JSON file containing your Firebase credentials.
  - Copy the credentials into the `.env` file as shown above. You may need to fill in values like `GOOGLE_CLOUD_PROJECT_ID`, `GOOGLE_CLOUD_PRIVATE_KEY_ID`, etc., based on the contents of the JSON file.