from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from bson.objectid import ObjectId
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
from flask_talisman import Talisman
import secrets
from datetime import datetime, timedelta
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from bson.json_util import dumps
import json
 
import requests
import logging
 
# Load environment variables
load_dotenv()

# Debugging line to check MAIL_PORT
print("MAIL_PORT:", os.getenv('MAIL_PORT'))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_mongodb_connection():
    """
    Diagnose MongoDB connection issues and return detailed information
    about potential problems.
    """
    results = {
        "env_variables": False,
        "uri_format": False,
        "connection": False,
        "auth": False,
        "database": False,
        "details": []
    }
    
    # Check environment variables
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        results["details"].append("MONGO_URI environment variable is not set")
        return results
    
    results["env_variables"] = True
    
    # Check URI format
    if mongo_uri.startswith(('mongodb://', 'mongodb+srv://')):
        results["uri_format"] = True
    else:
        results["details"].append("Invalid MongoDB URI format")
        return results
    
    # Test connection
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test server connection
        client.admin.command('ping')
        results["connection"] = True
        
        # Test authentication
        try:
            client.list_database_names()
            results["auth"] = True
            
            # Test database access
            db_name = mongo_uri.split('/')[-1].split('?')[0]
            if db_name:
                db = client[db_name]
                db.list_collection_names()
                results["database"] = True
            else:
                results["details"].append("No database specified in URI")
        except Exception as e:
            results["details"].append(f"Authentication error: {str(e)}")
            
    except Exception as e:
        results["details"].append(f"Connection error: {str(e)}")
    
    return results

# Initialize Flask app
app = Flask(__name__)

# Enable debug mode
app.debug = True

# Get MAIL_PORT and ensure it's set
mail_port = os.getenv('MAIL_PORT')
if mail_port is None:
    raise ValueError("MAIL_PORT environment variable is not set.")
else:
    mail_port = 587

# Basic configuration
app.config.update(
    SECRET_KEY='your-secret-key',  # Replace with your actual secret key
    MONGO_URI="mongodb+srv://kabarak:22360010s@cluster0.8ehdgpg.mongodb.net/flaskdb?retryWrites=true&w=majority",
    DEBUG=True,  # Enable Flask debug mode
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_PORT=mail_port,
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS') == 'True',
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
)

logger.info(f"Attempting to connect with URI: {app.config['MONGO_URI']}")

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize Talisman for security
Talisman(app, force_https=True)

# Initialize MongoDB with collections
try:
    logger.debug("Starting MongoDB connection setup...")
    mongo = PyMongo(app)
    
    # Test connection and create collections
    with app.app_context():
        # Initialize collections
        db = mongo.db
        users = db.users
        contacts = db.contacts
        
        # Create indexes
        users.create_index('username', unique=True)
        users.create_index('email', unique=True)
        contacts.create_index('registration_number', unique=True)
        
        # Insert a test document to ensure database is created
        try:
            users.insert_one({
                'username': 'testuser',
                'email': 'test@example.com',
                'password': generate_password_hash('testpass'),
                'reset_token': ''
            })
        except:
            # Document might already exist, that's okay
            pass
            
        logger.info("MongoDB collections initialized!")
        
        # List all databases to verify
        client = MongoClient(app.config['MONGO_URI'])
        dbs = client.list_database_names()
        logger.info(f"Available databases: {dbs}")
        client.close()
        
except Exception as e:
    logger.error(f"MongoDB setup error: {str(e)}")
    mongo = None

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    if mongo is None:
        return None
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route('/check-connection')
def check_connection():
    try:
        if not mongo:
            return {"status": "error", "message": "MongoDB not initialized"}
        
        # Test the connection
        mongo.db.command('ping')
        
        return {
            "status": "success",
            "message": "MongoDB connected",
            "database": mongo.db.name,
            "collections": mongo.db.list_collection_names()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "details": "MongoDB connection failed"
        }

@app.route('/')
def index():
    """Redirect root URL to signup page"""
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # Validate input
            if not all([username, email, password]):
                flash('All fields are required', 'error')
                return render_template('signup.html')

            # Check if username already exists
            if mongo.db.users.find_one({'username': username}):
                flash('Username already exists', 'error')
                return render_template('signup.html')

            # Check if email already exists
            if mongo.db.users.find_one({'email': email}):
                flash('Email already exists', 'error')
                return render_template('signup.html')

            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Create new user
            new_user = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'created_at': datetime.utcnow()
            }
            
            # Insert user into database
            mongo.db.users.insert_one(new_user)
            
            # Success message
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('signup.html')

    # GET request - show signup form
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please provide both username and password')
                return redirect(url_for('login'))
                
            user = mongo.db.users.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                user_obj = UserMixin()
                user_obj.id = str(user['_id'])
                login_user(user_obj)
                return redirect(url_for('dashboard'))
            
            flash('Invalid username or password')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred. Please try again.')
            
    return render_template('login.html')

# Store reset tokens temporarily (in production, use a database)
reset_tokens = {}

# Brevo API configuration
BREVO_API_KEY="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"
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY

def send_reset_email(email, reset_url):
    try:
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        sender = {"name": "kabarak", "email": "francismwaniki630@gmail.com"}
        to = [{"email": email}]
        
        subject = "Password Reset Request"
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>To reset your password, click on the following link:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>If you did not request this password reset, please ignore this email.</p>
                <p>This link will expire in 24 hours.</p>
            </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            html_content=html_content,
            sender=sender,
            subject=subject
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent successfully to {email}")
        return True, None
        
    except ApiException as e:
        error_message = f"API Exception: {str(e)}"
        logger.error(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        return False, error_message

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required', 'error')
            return render_template('forgot_password.html')

        try:
            # Check if user exists
            user = mongo.db.users.find_one({'email': email})
            if not user:
                # Don't reveal if email exists
                flash('If an account exists with that email, you will receive reset instructions.', 'info')
                return redirect(url_for('login'))

            # Generate token
            token = secrets.token_urlsafe(32)
            
            # Update user with reset token
            result = mongo.db.users.update_one(
                {'email': email},
                {'$set': {
                    'reset_token': token,
                    'reset_token_expiry': datetime.utcnow() + timedelta(hours=1)
                }}
            )
            
            if result.modified_count > 0:
                # Debug info
                logger.info(f"Token generated for {email}: {token}")
                reset_url = url_for('reset_password_with_token', 
                                  token=token, _external=True)
                logger.info(f"Reset URL: {reset_url}")
                
                # For debugging, show token in flash message
                flash(f'Debug - Token: {token}', 'info')
                
                # Send email with reset link
                try:
                    send_reset_email(email, reset_url)
                    flash('Password reset instructions sent to your email.', 'success')
                except Exception as e:
                    logger.error(f"Email sending error: {e}")
                    flash('Error sending email. Please try again.', 'error')
                
                return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Error in forgot_password: {e}")
            flash('An error occurred. Please try again.', 'error')
            return render_template('forgot_password.html')

    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        address = request.form.get('address')
        registration_number = request.form.get('registration_number')
        
        mongo.db.contacts.insert_one({
            'user_id': current_user.id,
            'mobile': mobile,
            'email': email,
            'address': address,
            'registration_number': registration_number
        })
        flash('Contact details saved successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('contact_form.html')

@app.route('/search-contact', methods=['GET', 'POST'])
@login_required
def search_contact():
    if request.method == 'POST':
        registration_number = request.form.get('registration_number')
        contact = mongo.db.contacts.find_one({'registration_number': registration_number})
        
        if contact:
            return render_template('contact_details.html', contact=contact)
        else:
            flash('No contact found with that registration number.', 'error')
    
    return render_template('search_contact.html')

def generate_reset_token(email):
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token valid for 1 hour
    except Exception:
        return None
    return email

def reset_password(email, new_password):
    # Clear the reset token after password reset
    mongo.db.users.update_one(
        {'email': email},
        {'$unset': {'reset_token': ""}}  # Remove the reset_token field
    )
    
    # Update the user's password
    hashed_password = generate_password_hash(new_password)
    mongo.db.users.update_one(
        {'email': email},
        {'$set': {'password': hashed_password}}
    )

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    logger.info(f"Reset password route accessed. Method: {request.method}")
    logger.info(f"Request args: {request.args}")
    logger.info(f"Form data: {request.form if request.method == 'POST' else 'No form data'}")
    
    if request.method == 'POST':
        # Handle password reset logic here
        new_password = request.form.get('new_password')
        token = request.args.get('token')
        
        # Verify the token and update the password logic goes here
        # For example:
        # email = verify_reset_token(token)
        # if email:
        #     hashed_password = generate_password_hash(new_password)
        #     # Update the user's password in the database
        #     flash('Your password has been updated successfully!', 'success')
        # else:
        #     flash('Invalid or expired token.', 'error')
        
        return redirect(url_for('login'))  # Redirect after processing

    return render_template('reset_password.html', token=request.args.get('token'))

@app.route('/lander')
def lander():
    # Add debugging to see what's happening
    logger.info("Incoming request URL: %s", request.url)
    logger.info("Template requested: %s", request.args.get('template'))
    
    template_name = request.args.get('template')
    
    # Basic error checking
    if not template_name:
        logger.error("No template specified")
        return "Template required", 400
        
    try:
        # Check if the template file exists first
        template_path = f"{template_name.lower()}.html"
        if not os.path.exists(os.path.join(app.template_folder, template_path)):
            logger.error(f"Template file not found: {template_path}")
            return f"Template {template_name} not found", 404
            
        # Pass all URL parameters to the template
        return render_template(
            template_path,
            tdfs=request.args.get('tdfs'),
            s_token=request.args.get('s_token'),
            uuid=request.args.get('uuid'),
            showDomain=request.args.get('showDomain')
        )
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/reset_password', methods=['POST'])
def reset_password_request():
    email = request.form['email']
    token = serializer.dumps(email, salt='password-reset-salt')
    reset_url = url_for('reset_password_with_token', token=token, _external=True)
    # Send email with reset_url
    flash('A password reset link has been sent to your email.')
    return redirect(url_for('login'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_with_token(token):
    logger.debug(f"Accessing reset-password route with token: {token}")
    
    # First, verify the token exists
    user = mongo.db.users.find_one({'reset_token': token})
    
    if not user:
        logger.error(f"No user found with token: {token}")
        flash('Invalid or expired reset token. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        try:
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not password:
                flash('Password is required', 'error')
                return render_template('reset_password.html', token=token)

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('reset_password.html', token=token)

            # Hash and update password
            hashed_password = generate_password_hash(password)
            result = mongo.db.users.update_one(
                {'reset_token': token},
                {
                    '$set': {
                        'password': hashed_password,
                        'reset_token': None
                    }
                }
            )
            
            if result.modified_count > 0:
                flash('Password updated successfully! Please login.', 'success')
                return redirect(url_for('login'))
            
            flash('Password update failed. Please try again.', 'error')
            return render_template('reset_password.html', token=token)
                
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return render_template('reset_password.html', token=token)
    
    # GET request - show form
    return render_template('reset_password.html', token=token)

# Debug route to check if token exists in database
@app.route('/debug-check-token/<token>')
def check_debug_token(token):
    try:
        # Find user with this token
        user = mongo.db.users.find_one(
            {'reset_token': token},
            {'email': 1, 'reset_token': 1, '_id': 0}
        )
        if user:
            return f"Token found! Associated with email: {user['email']}"
        return "Token not found in database"
    except Exception as e:
        return f"Error checking token: {str(e)}"

# Debug route to list all tokens in database
@app.route('/debug-list-tokens')
def list_debug_tokens():
    try:
        # Find all users with reset tokens
        users = mongo.db.users.find(
            {'reset_token': {'$ne': None}},
            {'email': 1, 'reset_token': 1, '_id': 0}
        )
        return dumps(list(users))
    except Exception as e:
        return f"Error listing tokens: {str(e)}"

# Add this function to test MongoDB connection
@app.route('/test-db')
def test_db():
    try:
        # Test the connection
        mongo.db.command('ping')
        # Try to access the users collection
        users_count = mongo.db.users.count_documents({})
        return f"MongoDB is connected! Users count: {users_count}"
    except Exception as e:
        return f"MongoDB connection error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)  # Simplified to run the app in debug mode
 
 