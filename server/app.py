from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
#pip install reportlab
#pip install
import re
import io
import math

from io import BytesIO

import re

from bson import ObjectId
from bson.objectid import ObjectId
# pip install pymongo

from flask import Flask, render_template, request, redirect, url_for, session, abort, flash, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import jsonify
from dotenv import load_dotenv
# pip install flask

from pymongo import MongoClient
from pymongo import DESCENDING
from pymongo import ASCENDING
import pymongo
import math

# pip install pymongo

from werkzeug.security import generate_password_hash, check_password_hash
# pip install werkzeug

from datetime import datetime, timedelta, timezone
from collections import defaultdict
import calendar
import pickle
import os
from flask_limiter.util import get_remote_address

import pandas as pd
# pip install pandas

from bcrypt import hashpw, gensalt
import bcrypt
# pip install bcrypt

from functools import wraps





# Load environment variables from the .env file
load_dotenv()

# Get MongoDB URI and Flask Secret Key from environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

if not MONGO_URI or not SECRET_KEY:
    raise ValueError("MONGO_URI and SECRET_KEY must be set in the environment.")



# Initialize Flask app
app = Flask(__name__, static_folder='../client', template_folder='../client')
limiter = Limiter(key_func=get_remote_address, app=app)

# Secure cookies
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restrict cross-site cookie sharing
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session expires after 30 minutes

# Set Flask secret key for session management
app.secret_key = SECRET_KEY  # Get secret key from environment variable

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)  # Connect to MongoDB using the URI from environment variable
db = client.get_database('dbAdmin')

limiter.init_app(app)

# MongoDB collections
users_collection = db.users
assessment_collection = db.assessment_result
feedback_collection = db.feedback
questionnaires = db.stress_questions
responses_collection = db.response
recommendation_collection = db.recommendations
response_collection = db['response']
stress_questions_collection = db['stress_questions']

# Create index for responses collection (if necessary)
responses_collection.create_index([('timestamp', pymongo.DESCENDING)])

# Path to your saved models
model_path = 'models/knn_model.pkl'
preprocessor_path = 'models/preprocessor.pkl'

# Load the KNN model
if os.path.exists(model_path):
    with open(model_path, 'rb') as model_file:
        knn_model = pickle.load(model_file)
else:
    raise FileNotFoundError(f"KNN model file not found at {model_path}")

# Load the preprocessor
if os.path.exists(preprocessor_path):
    with open(preprocessor_path, 'rb') as preprocessor_file:
        preprocessor = pickle.load(preprocessor_file)
else:
    raise FileNotFoundError(f"Preprocessor file not found at {preprocessor_path}")

ALLOWED_ADMIN_IP = ['223.25.62.251', '175.176.60.65', '216.247.87.221']

@app.before_request
def restrict_admin_routes():
    admin_routes = [
        '/admin_dashboard',
        '/admin_login',
        '/admin/management',
        '/admin/add_user',
        '/admin/edit_user/<user_id>',
        '/admin/add_question',
        '/admin/stress_questions',
        '/admin/feedback',
        '/admin/data',
    ]

    if any(request.path.startswith(route) for route in admin_routes):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        app.logger.info(f"Admin access attempt from IP: {client_ip} for route {request.path}")

        if client_ip != ALLOWED_ADMIN_IP:
            flash("Access denied: Unauthorized IP address.", "error")
            return abort(403)


# Landing page
@app.route('/')
def index():
    return render_template('landing/landing.html')

# Utility functions
def validate_object_id(id):
    try:
        return ObjectId(id)
    except Exception:
        abort(400)  # Return 400 Bad Request for invalid IDs

def filter_allowed_fields(query_args, allowed_fields):
    return {key: value for key, value in query_args.items() if key in allowed_fields}


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session.get('role')  # Check user role stored in the session
            if user_role != role:
                flash('Access denied: insufficient permissions.', 'error')
                return redirect(url_for('login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Route for student login in the root folder
@app.route('/student_login', methods=['GET'])
def student_login():
    # Add your login logic here for students
    return render_template('login.html')  # Render the student login page

# Helper Function: Calculate Cooldown Time
def get_cooldown(attempt_count):
    """Return cooldown time (in seconds) based on the number of failed cycles."""
    if attempt_count == 1:
        return 60  # 1 minute
    elif attempt_count == 2:
        return 600  # 10 minutes
    else:
        return 1800  # 30 minutes (or longer for subsequent attempts)


# Login Route for Users
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'GET':
        return render_template('login.html', disable_login=False)

    # POST logic: Process login
    username_or_email = request.form.get('username')
    password = request.form.get('password')

    # Track failed login attempts and cooldown
    failed_attempts = session.get('user_failed_attempts', 0)
    first_attempt_time = session.get('user_first_attempt_time')
    attempt_cycles = session.get('user_attempt_cycles', 0)

    # Check if cooldown applies
    if first_attempt_time:
        remaining_cooldown = get_cooldown(attempt_cycles) - (datetime.utcnow() - datetime.fromisoformat(first_attempt_time)).total_seconds()
        if remaining_cooldown > 0:
            flash(f'Too many failed attempts. Please try again in {int(remaining_cooldown)} seconds.', 'error')
            return render_template('login.html', disable_login=True, remaining_time=int(remaining_cooldown))

    # Query database
    query_field = 'email' if '@' in username_or_email else 'username'
    existing_user = users_collection.find_one({query_field: username_or_email})

    if existing_user and existing_user.get('role') == 'user':
        if check_password_hash(existing_user['password'], password):
            # Successful login: Reset session variables
            session.clear()
            session['user_id'] = str(existing_user['_id'])
            session['username'] = existing_user['username']
            session['role'] = 'user'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard', username=existing_user['username']))

    # Failed login attempt
    failed_attempts += 1
    session['user_failed_attempts'] = failed_attempts

    if failed_attempts >= 5:
        # Initiate cooldown
        session['user_first_attempt_time'] = datetime.utcnow().isoformat()
        session['user_attempt_cycles'] = attempt_cycles + 1
        session['user_failed_attempts'] = 0  # Reset failed attempts after starting cooldown
        flash('Too many failed attempts. Please try again later.', 'error')
    else:
        flash('Invalid username or password.', 'error')

    return render_template('login.html', disable_login=False)



# Fixed time_remaining Function
def time_remaining(last_time):
    """Calculate remaining time in seconds until the next allowed login."""
    if last_time:
        # Convert last_time to datetime if it’s stored as a string
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time)

        now = datetime.utcnow()  # Use UTC timezone-naive time
        # Make both datetime objects naive for consistent subtraction
        if last_time.tzinfo:
            last_time = last_time.replace(tzinfo=None)

        diff = now - last_time
        cooldown = timedelta(seconds=60)  # 1-minute cooldown
        remaining = cooldown.total_seconds() - diff.total_seconds()
        return max(0, remaining)
    return 0





# Error Handler for Rate Limiting
@app.errorhandler(429)
def ratelimit_error(error):
    flash('Too many login attempts. Please try again later.', 'error')
    return render_template('login.html', disable_login=True)

# Ensure Sessions Expire Properly
@app.before_request
def manage_session():
    session.permanent = True
    now = datetime.now(timezone.utc)  # Use timezone-aware datetime in UTC
    if 'last_activity' in session:
        last_activity = session['last_activity']
        if isinstance(last_activity, str):  # Convert ISO string to datetime object
            last_activity = datetime.fromisoformat(last_activity)
        if last_activity.tzinfo is None:  # Ensure last_activity is timezone-aware
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        timeout = timedelta(minutes=30)
        if now - last_activity > timeout:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))
    session['last_activity'] = now.isoformat()  # Store datetime as ISO string




@app.route('/admin_login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Apply rate-limiting for both GET and POST
def admin_login():
    if request.method == 'GET':
        return render_template('admin/login.html')  # Render the admin login page

    # POST logic: Process admin login
    identifier = request.form.get('identifier')
    password = request.form.get('password')

    # Track failed login attempts and cooldown
    failed_attempts = session.get('admin_failed_attempts', 0)
    first_attempt_time = session.get('admin_first_attempt_time')
    attempt_cycles = session.get('admin_attempt_cycles', 0)

    # Check if cooldown applies
    if first_attempt_time:
        remaining_cooldown = get_cooldown(attempt_cycles) - (datetime.utcnow() - datetime.fromisoformat(first_attempt_time)).total_seconds()
        if remaining_cooldown > 0:
            # Rate limit exceeded: Return JSON response
            return jsonify({'error': f'Too many failed attempts. Please try again in {int(remaining_cooldown)} seconds.'}), 400

    # Query the database for a username or email match
    existing_user = users_collection.find_one({
        '$or': [{'username': identifier}, {'email': identifier}]
    })

    if existing_user and check_password_hash(existing_user.get('password'), password):
        # Check for admin role
        if existing_user.get('role', '').strip().lower() != 'admin':
            return jsonify({'error': 'Insufficient permissions!'}), 403  # Forbidden error

        # Successful login: Reset session variables
        session.clear()
        session['username'] = existing_user.get('username')
        session['role'] = 'admin'
        
        # Return JSON response on successful login
        return jsonify({
            'success': 'Login successful!',
            'redirect_url': url_for('admin_dashboard')
        })

    # Failed login attempt
    failed_attempts += 1
    session['admin_failed_attempts'] = failed_attempts

    if failed_attempts >= 5:
        # Initiate cooldown
        session['admin_first_attempt_time'] = datetime.utcnow().isoformat()
        session['admin_attempt_cycles'] = attempt_cycles + 1
        session['admin_failed_attempts'] = 0  # Reset failed attempts after starting cooldown
        return jsonify({'error': 'Too many failed attempts. Please try again later.'}), 400
    else:
        return jsonify({'error': 'Invalid username or password.'}), 400


# Error handler for rate-limiting issues (429 status code)
@app.errorhandler(429)
def handle_rate_limit_error(error):
    return jsonify({
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429
# admin dashboard =====================
    
# Admin route for admin dashboard
@app.route('/admin_dashboard')
@role_required('admin')
def admin_dashboard():
    username = session.get('username')
 
    if not username: 
        return redirect(url_for('admin_login_dashboard'))
    

     # Retrieve any success message from the session
    message = session.pop('success_message', None)


    # Retrieve general counts from the database
    user_count = users_collection.count_documents({})
    assessment_count = assessment_collection.count_documents({})
    feedback_count = db['feedback'].count_documents({})

    # Calculate stressor data for the bar chart
    stressor_data = assessment_collection.aggregate([
        {"$unwind": "$stressors"},  # Unwind the array of stressors
        {"$group": {"_id": "$stressors", "count": {"$sum": 1}}},  # Group by stressor and count occurrences
        {"$project": {"stressor": "$_id", "count": 1, "_id": 0}}  # Reshape the output
    ])

    # Convert to list and calculate percentages for stressor data
    stressor_data = list(stressor_data)
    total_students = sum(item['count'] for item in stressor_data)
    
    for item in stressor_data:
        item['percentage'] = (item['count'] / total_students) * 100
        item['student_count'] = item['count']  # Keep the raw student count for tooltip

    # Calculate stress level distribution (for the pie chart)
    stress_level_data = assessment_collection.aggregate([
        {"$sort": {"user_id": 1, "date_tested": DESCENDING}},  # Sort by user_id and date_tested in descending order
        {"$group": {"_id": "$user_id", "latest_stress_level": {"$first": "$stress_level"}}},  # Get latest stress level for each user
        {"$group": {"_id": "$latest_stress_level", "count": {"$sum": 1}}},  # Group by stress level and count occurrences
        {"$project": {"stress_level": "$_id", "count": 1, "_id": 0}}  # Reshape the output
    ])

    # Convert the aggregation result to a list and sort by stress level
    stress_level_data = sorted(list(stress_level_data), key=lambda x: x['stress_level'])

    # Calculate total assessments for percentage calculation
    total_assessments = sum(item['count'] for item in stress_level_data)
    
    # Add percentage for each stress level
    for item in stress_level_data:
        item['percentage'] = (item['count'] / total_assessments) * 100

    # Pass data to the template
    return render_template(
        'admin/dashboard.html',
        username=username,
        message=message,
        user_count=user_count,
        assessment_count=assessment_count,
        feedbacks_count=feedback_count,
        stressor_data=stressor_data,  # Data for the bar graph
        stress_level_data=stress_level_data  # Data for the pie chart
    )


@app.route('/admin/management', methods=['GET', 'POST'])
@role_required('admin')
def management():
    search = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 20  # Number of rows per page

    # Fetch all users from the database (or data source)
    all_users = list(users_collection.find())  # Ensure this fetches all users

    # Filter users based on the search term
    if search:
        search_terms = search.split()
        users = [
            user for user in all_users
            if any(
                term == word
                for word in f"{user['username']} {user['email']} {user['role']} {user['gender']} {user['year_level']}".lower().split()
                for term in search_terms
            )
        ]
    else:
        users = all_users


    # Paginate the filtered results
    total_pages = math.ceil(len(users) / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = users[start:end]

    # Handle POST requests
    if request.method == 'POST':
        if 'edit_user' in request.form:
            user_id = request.form.get('user_id')  # Get the user ID from the form
            app.logger.info(f"Edit request for user_id: {user_id}")
            if user_id:
                try:
                    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
                    if user_data:
                        app.logger.info(f"User data found: {user_data}")
                        return render_template('admin/edit_user.html', user=user_data)
                    else:
                        flash("No user found with the provided ID.", "error")
                except Exception as e:
                    app.logger.error(f"Error retrieving user data: {str(e)}")
                    flash("Error retrieving user data.", "error")

        elif 'delete_user' in request.form:
            # Handle delete request
            user_id = request.form.get('user_id')
            app.logger.info(f"Delete request for user_id: {user_id}")
            if user_id:
                try:
                    users_collection.delete_one({'_id': ObjectId(user_id)})
                    flash("User successfully deleted.", "success")
                except Exception as e:
                    app.logger.error(f"Error deleting user: {str(e)}")
                    flash("Error deleting user.", "error")
            return redirect(url_for('management'))

    # Render the user management page with pagination data
    start_page = max(1, page - 2)  # Adjust as per your pagination logic
    end_page = min(total_pages, page + 2)

    return render_template(
        'admin/management.html',
        users=paginated_users,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
        search=search
    )



@app.route('/admin/dashboard/')
@role_required('admin')
def home():
    # Count users with the role of "user"
    user_count = users_collection.count_documents({'role': 'user'})

    # Count the total number of assessments in the `assessment_result` collection
    assessment_count = assessment_collection.count_documents({})

    # Count the total number of feedback entries in the `feedback` collection
    feedback_count = feedback_collection.count_documents({})

    # Render the admin dashboard template with the user, assessment, and feedback counts
    return render_template('admin/dashboard.html', 
                           user_count=user_count, 
                           assessment_count=assessment_count,
                           feedbacks_count=feedback_count)



@app.route('/admin/data/', methods=['GET', 'POST'])
@role_required('admin')
def data():
    
    category_descriptions = {
    "Academic": "Academic stressors are related to the demands and pressures that come with academic life. This can include workload, deadlines, performance expectations, exams, assignments, and balancing academic life with other commitments.",
    "Environmental": "Environmental stressors refer to external factors in the student's surroundings that can contribute to stress. These can include noisy living conditions, inadequate study environments, lack of green spaces, or issues like overcrowding. Stress can also arise from changes in the environment, such as moving to a new location or dealing with natural disasters or extreme weather conditions. ",
    "socio_economic": "Socio-economic stressors encompass financial concerns, family support, living conditions, and other socio-economic factors that affect a student's well-being. These stressors can include worries about tuition fees, monthly living expenses, job pressures, or the inability to access resources. Students may experience stress from balancing studies with part-time jobs or dealing with financial instability. ",
    "psychological": "refers to the emotional and mental aspects of stress that students may experience. It includes issues like anxiety, depression, self-esteem, and mental health challenges. Psychological stressors may arise from personal experiences, internal conflicts, or cognitive patterns, such as worry, fear, or self-doubt.",
    }   

    # Initialize filter criteria
    filter_criteria = {}

    # Get date range from query parameters
    start_date = request.args.get('start_date')  # Format: YYYY-MM-DD
    end_date = request.args.get('end_date')      # Format: YYYY-MM-DD

    try:
        # Validate and parse dates if they are provided and not "None"
        if start_date and start_date.lower() != "none" and end_date and end_date.lower() != "none":
            filter_criteria["date_tested"] = {
                "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
                "$lte": datetime.strptime(end_date, "%Y-%m-%d")
            }
        else:
            # Default range if no filter is applied
            filter_criteria["date_tested"] = {
                "$gte": datetime(2000, 1, 1),
                "$lte": datetime.now()
            }
    except ValueError:
        return "Invalid date format. Please use 'YYYY-MM-DD'.", 400
        
   # Bar chart-specific filter
    stressor_category = request.args.get('stressor')  # Get stressor category from query parameters
    print(f"Received Stressor Category: '{stressor_category}'")  # Debugging

    bar_chart_filter = filter_criteria.copy()  # Start with the general filter

        # Custom mapping of categories to stressors
    category_to_stressors = {
        "Academic": ["Program Confidence", "Academic Stress", "Advisor Support"],
        "Environmental": ["Home Stress", "Commute Stress", "Noise Level", "Weather Conditions"],
        "Socio-Economic": ["Financial Satisfaction", "Friends Support", "Resources Access"],
        "Psychological": ["Sadness", "Anxious", "Peer Pressure", "Sleep Quality", "AI Tools", "Family Stress"]
    }

   # Determine the feature names based on the stressor category
    if stressor_category and stressor_category.lower() != "none":
        feature_names = category_to_stressors.get(stressor_category, [])
    else:
        feature_names = [stressor for stressors in category_to_stressors.values() for stressor in stressors]

    # Update the filter to include stressors
    if feature_names:
        bar_chart_filter["stressors"] = {"$in": feature_names}

    # Debugging
    print(f"Bar Chart Filter: {bar_chart_filter}")
    print(f"Feature Names: {feature_names}")

    # Aggregation pipeline for stressor data
    stressor_data = assessment_collection.aggregate([
        {"$match": bar_chart_filter},  # Apply the combined filter
        {"$unwind": "$stressors"},  # Decompose the array of stressors
        {"$group": {"_id": "$stressors", "count": {"$sum": 1}}},  # Group by stressor and count occurrences
        {"$project": {"stressor": "$_id", "count": 1, "_id": 0}}  # Format the output
    ])

    # Convert to list and process
    stressor_data = list(stressor_data)
    total_students = sum(item['count'] for item in stressor_data)
    for item in stressor_data:
        item['percentage'] = (item['count'] / total_students) * 100
        item['student_count'] = item['count']

    for item in stressor_data:
        item['percentage'] = (item['count'] / total_students) * 100
        item['student_count'] = item['count']  # Keep the raw student count for tooltip
        print(f"Stressor: {item['stressor']}, Count: {item['count']}, "
            f"Percentage: {item['percentage']:.2f}%, Category: {stressor_category}")

    # Total questions and unique categories are not filtered anymore
    # Remove database-derived categories and count logic
    category_count = len(category_to_stressors)  # Count unique keys in the custom mapping

    # Prepare category descriptions using the custom mapping
    categories_with_descriptions = [
        {"category": category, "description": category_descriptions.get(category, "No description available.")}
        for category in category_to_stressors.keys()
    ]


        # print("Final filter criteria:", filter_criteria)  # Debugging line to ensure the filter is correct

    # Use assessment collection for count
    assessment_count = assessment_collection.count_documents(filter_criteria)
    categories = stress_questions_collection.distinct("category")
    categories_with_descriptions = [
        {"category": category, "description": category_descriptions.get(category, "No description available.")}
        for category in categories
]
  

    # Calculate average stress level from assessment collection
    pipeline = [
        {"$match": filter_criteria},  # Apply filters
        {"$group": {"_id": None, "avgStressLevel": {"$avg": "$stress_level"}}}
    ]
    avg_stress_result = list(assessment_collection.aggregate(pipeline))
    avg_stress_level = avg_stress_result[0].get('avgStressLevel', 0.0) if avg_stress_result else 0.0
    avg_stress_level = round(avg_stress_level, 2) if avg_stress_level is not None else 0.0
    print(f"Avg Stress Level: {avg_stress_level}")  # Debugging line

    # Count total questions and unique categories in stress_questions collection
    question_count = stress_questions_collection.count_documents({})
    category_count = len(stress_questions_collection.distinct("category"))

    # Prepare line chart data (with filters)
    pipeline_for_line_chart = [
        {"$match": filter_criteria},  # Apply filters
        {"$project": {"month": {"$month": "$date_tested"}, "year": {"$year": "$date_tested"}, "stress_level": 1}},
        {"$group": {"_id": {"month": "$month", "year": "$year"}, "avgStressLevel": {"$avg": "$stress_level"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    avg_stress_result_for_chart = list(assessment_collection.aggregate(pipeline_for_line_chart))
    chart_data = [['Month', 'Avg Stress Level']]
    for entry in avg_stress_result_for_chart:
        month = entry['_id']['month']
        year = entry['_id']['year']
        chart_data.append([f"{year}-{month:02d}", round(entry['avgStressLevel'], 2)])

    # Prepare column chart data: Stress levels by year level (with filters)
    pipeline_for_column_chart = [
        {"$match": filter_criteria},  # Apply filters
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user_data"
        }},
        {"$unwind": "$user_data"},
        {"$group": {
            "_id": "$user_data.year_level",
            "avgStressLevel": {"$avg": "$stress_level"}
        }},
        {"$sort": {"_id": 1}}
    ]
    year_level_data = list(assessment_collection.aggregate(pipeline_for_column_chart))
    column_chart_data = [['Year Level', 'Avg Stress Level']]
    for entry in year_level_data:
        year_level = entry['_id']
        avg_stress = round(entry['avgStressLevel'], 2)
        column_chart_data.append([f"Year {year_level}", avg_stress])

    # Count total students per year level
    year_level_student_data = list(users_collection.aggregate([{"$group": {"_id": "$year_level", "count": {"$sum": 1}}}]))
    year_level_student_counts = [{'year_level': entry['_id'], 'count': entry['count']} for entry in year_level_student_data]

    # Calculate stressor data for the bar chart (with filters)
    stressor_data = assessment_collection.aggregate([
        {"$match": filter_criteria},  # Apply filters
        {"$unwind": "$stressors"},  # Unwind the array of stressors
        {"$group": {"_id": "$stressors", "count": {"$sum": 1}}},  # Group by stressor and count occurrences
        {"$project": {"stressor": "$_id", "count": 1, "_id": 0}}  # Reshape the output
    ])
    stressor_data = list(stressor_data)
    total_students = sum(item['count'] for item in stressor_data)
    for item in stressor_data:
        item['percentage'] = (item['count'] / total_students) * 100
        item['student_count'] = item['count']  # Keep the raw student count for tooltip

    # Calculate stress level distribution (for the pie chart, with filters)
    stress_level_data = assessment_collection.aggregate([
        {"$match": filter_criteria},  # Apply filters
        {"$sort": {"user_id": 1, "date_tested": DESCENDING}},  # Sort by user_id and date_tested in descending order
        {"$group": {"_id": "$user_id", "latest_stress_level": {"$first": "$stress_level"}}},  # Get latest stress level for each user
        {"$group": {"_id": "$latest_stress_level", "count": {"$sum": 1}}},  # Group by stress level and count occurrences
        {"$project": {"stress_level": "$_id", "count": 1, "_id": 0}}  # Reshape the output
    ])
    stress_level_data = sorted(list(stress_level_data), key=lambda x: x['stress_level'])
    total_assessments = sum(item['count'] for item in stress_level_data)
    for item in stress_level_data:
        item['percentage'] = (item['count'] / total_assessments) * 100

    # Pass all data and filter parameters to the template
    return render_template('admin/data.html',
                           avg_stress_level=avg_stress_level,
                           question_count=question_count,
                           category_count=category_count,
                           categories=categories_with_descriptions,
                           chart_data=chart_data,
                           column_chart_data=column_chart_data,
                           year_level_student_counts=year_level_student_counts,
                           stressor_data=stressor_data,
                           stress_level_data=stress_level_data,
                           assessment_count=assessment_count,  # Now using assessment_count
                           start_date=start_date,
                           end_date=end_date)



@app.route('/admin/generate_report/', methods=['GET'])
@role_required('admin')
def generate_report():
     # Initialize filter criteria
    filter_criteria = {}

    # Get date range from query parameters
    start_date = request.args.get('start_date')  # Format: YYYY-MM-DD
    end_date = request.args.get('end_date')      # Format: YYYY-MM-DD

    # Check if parameters are valid or default to full range
    if start_date and start_date.lower() != "none" and end_date and end_date.lower() != "none":
        try:
            # Parse the provided dates
            filter_criteria["date_tested"] = {
                "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
                "$lte": datetime.strptime(end_date, "%Y-%m-%d")
            }
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD'.", 400
    else:
        # Apply default range if no filter is provided or if "None" is passed
        filter_criteria["date_tested"] = {
            "$gte": datetime(2000, 1, 1),
            "$lte": datetime.now()
        }

    # Stress Trends Over Time
    pipeline_for_line_chart = [
        {"$match": filter_criteria},
        {"$project": {"month": {"$month": "$date_tested"}, "year": {"$year": "$date_tested"}, "stress_level": 1}},
        {"$group": {"_id": {"month": "$month", "year": "$year"}, "avgStressLevel": {"$avg": "$stress_level"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    avg_stress_result_for_chart = list(assessment_collection.aggregate(pipeline_for_line_chart))

    # Student Stress Levels per Year Level
    pipeline_for_column_chart = [
        {"$match": filter_criteria},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user_data"
        }},
        {"$unwind": "$user_data"},
        {"$group": {"_id": "$user_data.year_level", "avgStressLevel": {"$avg": "$stress_level"}}},
        {"$sort": {"_id": 1}}
    ]
    year_level_data = list(assessment_collection.aggregate(pipeline_for_column_chart))

      # Stress Trends Over Time
    pipeline_for_line_chart = [
        {"$match": filter_criteria},
        {"$project": {"month": {"$month": "$date_tested"}, "year": {"$year": "$date_tested"}, "stress_level": 1}},
        {"$group": {"_id": {"month": "$month", "year": "$year"}, "avgStressLevel": {"$avg": "$stress_level"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    avg_stress_result_for_chart = list(assessment_collection.aggregate(pipeline_for_line_chart))

     # Stress Level Distribution (Pie Chart Data)
    stress_level_data = assessment_collection.aggregate([
        {"$match": filter_criteria},
        {"$sort": {"user_id": 1, "date_tested": -1}},
        {"$group": {"_id": "$user_id", "latest_stress_level": {"$first": "$stress_level"}}},
        {"$group": {"_id": "$latest_stress_level", "count": {"$sum": 1}}},
        {"$project": {"stress_level": "$_id", "count": 1, "_id": 0}}
    ])
    stress_level_data = sorted(list(stress_level_data), key=lambda x: x['stress_level'])
    total_assessments = sum(item['count'] for item in stress_level_data)
    for item in stress_level_data:
        item['percentage'] = (item['count'] / total_assessments) * 100

    # Stressor Percentage
    stressor_data = assessment_collection.aggregate([
        {"$match": filter_criteria},
        {"$unwind": "$stressors"},
        {"$group": {"_id": "$stressors", "count": {"$sum": 1}}}
    ])
    stressor_data = list(stressor_data)
    total_students = sum(item['count'] for item in stressor_data)
    for item in stressor_data:
        item['percentage'] = (item['count'] / total_students) * 100



      # Create PDF Output
    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Define Custom Styles
    title_style = styles["Title"]
    title_style.fontSize = 26
    title_style.textColor = colors.HexColor("#0F4D44")
    title_style.alignment = 1  # Center Align

    section_title_style = styles["Heading2"]
    section_title_style.fontSize = 16
    section_title_style.fontName = "Helvetica-Bold"
    section_title_style.textColor = colors.HexColor("#0F4D44")

    normal_style = styles["Normal"]
    normal_style.fontName = "Helvetica"
    normal_style.fontSize = 12
    normal_style.leading = 15

    section_header_style = ParagraphStyle(
    name="SectionHeader",
    parent=styles["Normal"],
    fontSize=16,
    textColor=colors.white,
    alignment=1,
    backColor=colors.HexColor("#a3bfb0"),
    leading=24,
)

    # Cover Page
    elements.append(Paragraph("Stress Check Report", title_style))
    elements.append(Spacer(1, 24))

    # Current date
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", normal_style))
    elements.append(Spacer(1, 12))

  # Add filtered date range if provided
    if start_date and end_date and start_date.lower() != 'none' and end_date.lower() != 'none':
        elements.append(Paragraph(f"Filtered Date Range: {start_date} to {end_date}", normal_style))
    else:
        elements.append(Paragraph("Filtered Date Range: All Records", normal_style))

    elements.append(Spacer(1, 12))


    # Add horizontal line
    line = Drawing(500, 1)  # Width of the line (adjust as needed)
    line.add(Line(0, 0, 500, 0))  # Coordinates of the line (start_x, start_y, end_x, end_y)
    elements.append(line)
    elements.append(Spacer(1, 15))  # Add spacing after the line

    # Section 1: Stress Level Distribution
    elements.append(Paragraph("Stress Level Distribution", section_header_style))
    elements.append(Spacer(1, 12))
    stress_level_table = [["Stress Level", "Student Count", "Percentage"]]
    for item in stress_level_data:
        stress_level_table.append(
            [
                item["stress_level"],
                item["count"],
                f"{round(item['percentage'], 2)}%",
            ]
        )

    table = Table(stress_level_table, colWidths=[150, 150, 150])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4D44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 24))

   # Section 2: Stress Trends Over Time
    elements.append(Paragraph("Stress Trends Over Time", section_header_style))
    elements.append(Spacer(1, 12))
    trends_table = [["Month", "Year", "Average Stress Level"]]

    for entry in avg_stress_result_for_chart:
        # Convert month number to month name
        month_name = calendar.month_name[entry["_id"]["month"]]
        trends_table.append(
            [
                month_name,  # Use the month name instead of the number
                entry["_id"]["year"],
                round(entry["avgStressLevel"], 2),
            ]
        )

    table = Table(trends_table, colWidths=[150, 150, 150])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4D44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Section 3: Year Level Stress Levels
    elements.append(
        Paragraph("Student Stress Levels by Year Level", section_header_style)
    )
    elements.append(Spacer(1, 12))
    year_level_table = [["Year Level", "Average Stress Level"]]
    for entry in year_level_data:
        year_level_table.append(
            [
                f"Year {entry['_id']}",
                round(entry["avgStressLevel"], 2),
            ]
        )

    table = Table(year_level_table, colWidths=[300, 150])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4D44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Section 4: Stressor Percentages
    elements.append(Paragraph("Stressor Percentages", section_header_style))
    elements.append(Spacer(1, 12))
    stressor_table = [["Stressor", "Assessment Count", "Percentage"]]
    for item in stressor_data:
        stressor_table.append(
            [item["_id"], item["count"], f"{round(item['percentage'], 2)}%"]
        )

    table = Table(stressor_table, colWidths=[200, 150, 150])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4D44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Build and Save PDF
    doc.build(elements)
    pdf_output.seek(0)
    
    # Send the PDF as a response
    return send_file(
        pdf_output,
        as_attachment=True,
        download_name="stress_check_report.pdf",
        mimetype="application/pdf"
    )


@app.route('/admin/assessments', methods=['GET', 'POST', 'DELETE'])
@role_required('admin')
def assessments():
    username = session.get('username')

    if not username:
        return redirect(url_for('login'))

    if request.method == 'DELETE':
        try:
            data = request.get_json()  # Parse JSON payload
            assessment_id = data.get('assessment_id')

            if not assessment_id:
                return jsonify({'error': 'Assessment ID not provided.'}), 400

            # Attempt to delete the assessment by ObjectId
            try:
                object_id = ObjectId(assessment_id)
            except Exception as e:
                return jsonify({'error': 'Invalid assessment ID format.'}), 400

            result = assessment_collection.delete_one({'_id': object_id})

            if result.deleted_count == 1:
                print(f"Assessment {assessment_id} deleted successfully.")
                return jsonify({'success': 'Assessment deleted successfully.'}), 200
            else:
                print(f"Assessment {assessment_id} not found.")
                return jsonify({'error': 'Assessment not found.'}), 404

        except Exception as e:
            print(f"Error deleting assessment: {e}")
            return jsonify({'error': 'Error deleting assessment.'}), 500

    # Handle GET requests for displaying assessments
    sort_by = request.args.get('sort_by', 'date')  # Default sort by date
    sort_order = request.args.get('sort_order', 'desc')  # Default to descending

    # Convert sort_order to MongoDB-compatible sort direction
    sort_direction = ASCENDING if sort_order == 'asc' else DESCENDING

    # Define the sort field based on the sort_by parameter
    if sort_by == 'date':
        sort_field = 'date_tested'
    elif sort_by == 'stress_level':
        sort_field = 'stress_level'
    elif sort_by == 'year_level':
        sort_field = 'year_level'
    else:
        sort_field = 'date_tested'

    # Fetch and sort all assessments from the database
    all_assessments = list(assessment_collection.find().sort(sort_field, sort_direction))

    # Pagination setup
    per_page = 10  # Maximum number of assessments per page
    page = request.args.get('page', 1, type=int)  # Get the current page number from the query parameter
    total_assessments = len(all_assessments)  # Total number of assessments
    total_pages = math.ceil(total_assessments / per_page)  # Total number of pages

    # Slice the assessments for the current page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_assessments = all_assessments[start:end]

    # Prepare the paginated data to pass to the template
    assessments_list = []
    for assessment in paginated_assessments:
        user_id = assessment.get('user_id', 'N/A')
        user = users_collection.find_one({'_id': user_id})
        user_name = user.get('username', 'N/A') if user else 'N/A'
        year_level = user.get('year_level', 'N/A') if user else 'N/A'
        age = user.get('age', 'N/A') if user else 'N/A'  # Add age
        assessment_date = assessment.get('date_tested', 'N/A')
        stress_level = assessment.get('stress_level', 'N/A')
        stressors = assessment.get('stressors', [])  # Add stressors

        assessments_list.append({
            'id': str(assessment.get('_id')),
            'username': user_name,
            'age': age,
            'year_level': year_level,
            'date': assessment_date,
            'stress_level': stress_level,
            'stressors': stressors,
        })

    # Pagination controls for the template
    start_page = max(1, page - 2)  # Show the previous 2 pages, if possible
    end_page = min(total_pages, page + 2)  # Show the next 2 pages, if possible

    # Render the assessments page with the sorted and paginated data
    return render_template(
        'admin/assessments.html',
        username=username,
        assessments=assessments_list,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
        sort_order=sort_order,
        sort_by=sort_by,
    )


@app.route('/admin/feedback/', methods=['GET', 'POST'])
@role_required('admin')
def admin_feedback():
  
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of feedback items per page
    query = {}

    # Fetch filtered feedback data from the MongoDB feedback collection
    feedback_data = list(feedback_collection.find(query))

    # Implement pagination logic
    total_feedback = len(feedback_data)
    total_pages = math.ceil(total_feedback / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_feedback = feedback_data[start:end]

    if request.method == 'POST':
        # Handle deletion (AJAX POST request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            feedback_id = request.json.get('feedback_id')
            if feedback_id:
                try:
                    feedback_id = feedback_id.strip()
                    object_id = ObjectId(feedback_id)
                    result = feedback_collection.delete_one({'_id': object_id})
                    
                    if result.deleted_count == 1:
                        return jsonify({'success': f'Feedback deleted successfully.'}), 200
                    else:
                        return jsonify({'error': f'Feedback with ID {feedback_id} not found.'}), 404
                except Exception as e:
                    print(f"Error deleting feedback: {e}")
                    return jsonify({'error': 'Invalid feedback ID format.'}), 400
            return jsonify({'error': 'Feedback ID not provided.'}), 400

        return jsonify({'error': 'Invalid request type.'}), 400

    # Render the page with feedback data for normal GET requests
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    return render_template(
        'admin/feedback.html',
        feedback_data=paginated_feedback,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
    )




@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user_data:
        flash("User not found.", "error")
        return redirect(url_for('management'))

    if request.method == 'POST':
        # Get form values
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        year_level = request.form.get('year_level')

        # Convert and validate numeric fields
        try:
            age = int(age) if age else None
            year_level = int(year_level) if year_level else None
        except ValueError:
            flash("Invalid input for age or year level.", "error")
            return redirect(url_for('edit_user', user_id=user_id))

        # Prepare update data
        update_data = {
            'username': username,
            'email': email,
            'role': role,
            'age': age,
            'gender': gender
        }
        if year_level is not None:
            update_data['year_level'] = year_level

        # Compare fields
        changes_made = False
        if username != user_data['username']:
            changes_made = True
        if email != user_data['email']:
            changes_made = True
        if role != user_data['role']:
            changes_made = True
        if str(age) != str(user_data['age']):
            changes_made = True
        if gender != user_data['gender']:
            changes_made = True
        if user_data.get('year_level'):
            if str(year_level) != str(user_data.get('year_level', '')):
                changes_made = True
        if password:
            if not check_password_hash(user_data['password'], password):
                changes_made = True
                update_data['password'] = generate_password_hash(password)

        # Debug logs
        app.logger.debug(f"Changes made: {changes_made}")
        app.logger.debug(f"Update Data: {update_data}")

        # If no changes were made, display error
        if not changes_made:
            flash("No changes were made. Please update at least one field.", "error")
            return redirect(url_for('edit_user', user_id=user_id))

        # If changes were made, update the user data
        try:
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            flash("User successfully updated.", "success")
        except Exception as e:
            flash(f"Error updating user: {str(e)}", "error")
            app.logger.error(f"Error updating user: {e}")

        return redirect(url_for('management'))

    # GET request to render the edit form with pre-filled data
    return render_template('admin/edit_user.html', username=session.get('username'), user=user_data)





@app.route('/admin/add_user', methods=['GET', 'POST'])
@role_required('admin')
def add_user():
    if request.method == 'POST':
        # Debug form data
        print("Form Data:", request.form)

        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')  # Role determines if it's an admin or a user
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        year_level = request.form.get('year_level')  # Only relevant for users

        # Input validation
        if not username or not email or not role or not password or not age or not gender:
            flash("All fields are required.", "error")
            return redirect(url_for('add_user'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address.", "error")
            return redirect(url_for('add_user'))
        
        # Validate age is a number
        try:
            age = int(age)
        except ValueError:
            flash("Age must be a number.", "error")
            return redirect(url_for('add_user'))

        # Check if user already exists
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash("User already exists!", "error")
            return redirect(url_for('add_user'))

        # Hash the password before saving to database
        if password:
            hashed_password = generate_password_hash(password)  # Use Werkzeug's hash function
        else:
            flash("Password cannot be empty.", "error")
            return redirect(url_for('add_user'))

        # Prepare user data
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,  # Store the hashed password
            'age': age,
            'gender': gender,
            'role': role  # Admin or User
        }

        # Add year_level only if the role is "User"
        if role.lower() == 'user':
            if not year_level:  # Ensure year_level is provided for users
                flash("Year Level is required for users.", "error")
                return redirect(url_for('add_user'))
            new_user['year_level'] = year_level

        # Insert into the users collection
        try:
            users_collection.insert_one(new_user)
            # Flash success message based on the role
            if role.lower() == 'user':
                flash("User has been successfully added.", "success")
            elif role.lower() == 'admin':
                flash("Admin has been successfully added.", "success")
        except Exception as e:
            flash(f"Error inserting into MongoDB: {str(e)}", "error")
            return redirect(url_for('add_user'))

        # Redirect to the add_user route to clear the form
        return redirect(url_for('add_user'))

    # Render the form with empty fields
    return render_template('admin/add_user.html', form_data={})


@app.route('/admin/add_question', methods=['GET'])
def add_question():
    return render_template('/admin/add_questions.html')

# Route to handle form submission and add new question to MongoDB
@app.route('/submit_question', methods=['POST'])
@role_required('admin')
def submit_question():
    if request.method == 'POST':
        question_text = request.form['question']
        question_type = request.form['type']
        question_category = request.form['category']

        # Create a new question document
        new_question = {
            'question': question_text,
            'type': question_type,
            'category': question_category
        }

        # Insert the new question document into MongoDB
        questionnaires.insert_one(new_question)

        # Redirect back to the add question form or to a different page
        return redirect(url_for('stress_questions'))
    

@app.route('/admin/stress_questions', methods=['GET', 'POST'])
def stress_questions():
    try:
        # Retrieve all stress questions from MongoDB
        stress_questions = list(questionnaires.find())
        app.logger.info(f"Retrieved stress questions: {stress_questions}")  # Log retrieved data

        if request.method == 'POST':
            data = request.get_json()  # Get JSON data sent via AJAX
            app.logger.info(f"Received data for deletion: {data}")  # Log received data

            if data and 'delete_question' in data:
                # Get the question ID from the JSON payload
                question_id = data['question_id']

                # Log the question ID to check if it is correct
                app.logger.info(f"Deleting question with ID: {question_id}")

                # Delete the question from the database
                result = questionnaires.delete_one({'_id': ObjectId(question_id)})

                # Log the result of the deletion
                app.logger.info(f"Delete result: {result.deleted_count}")

                if result.deleted_count == 1:
                    return jsonify({'status': 'success', 'message': 'Question successfully deleted.'}), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to delete question. It may not exist.'}), 400

        # If no POST request, just render the page with the list of questions
        return render_template('admin/stress_questions.html', stress_questions=stress_questions)

    except Exception as e:
        app.logger.error(f'Error retrieving stress questions: {str(e)}')
        return 'An error occurred while retrieving data.'
    
# Route for editing recommendations
@app.route('/admin/edit_recommendation', methods=['GET', 'POST'])
@role_required('admin')
def edit_recommendation():
    username = session.get('username')
    if not username:
        return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in

    if request.method == 'GET':
        # Fetch all recommendations and related questions
        recommendations = list(recommendation_collection.find())
        stress_questions = list(db.stress_questions.find())
        
        # Create a mapping of stressor to its related questions
        stressor_questions = {
            question['feature_name']: question['question']
            for question in stress_questions
        }

        return render_template(
            'admin/edit_recommendation.html',
            recommendations=recommendations,
            stressor_questions=stressor_questions
        )
    
    if request.method == 'POST':
        try:
            # Get form data
            stressor = request.form.get('stressor')
            severity = request.form.get('severity')
            new_text = request.form.get('text')
            new_source = request.form.get('source')

            # Validate input
            if not stressor or not severity or not new_text or not new_source:
                flash("All fields are required to update a recommendation.", "error")
                return redirect(url_for('edit_recommendation'))

            # Find the recommendation document for the stressor
            recommendation = recommendation_collection.find_one({'stressor': stressor})

            if not recommendation:
                flash("No matching stressor found.", "error")
                return redirect(url_for('edit_recommendation'))

            # Update the specific severity level's recommendation
            severity_key = str(severity)
            if severity_key in recommendation.get('recommendations', {}):
                recommendation_collection.update_one(
                    {'stressor': stressor},
                    {'$set': {
                        f'recommendations.{severity_key}.0.text': new_text,
                        f'recommendations.{severity_key}.0.source': new_source
                    }}
                )
                flash("Recommendation updated successfully.", "success")
            else:
                flash("Invalid severity level.", "error")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(url_for('edit_recommendation'))
    
@app.route('/admin/get_recommendation', methods=['GET'])
@role_required('admin')
def get_recommendation():
    try:
        # Get stressor and severity from the request arguments
        stressor = request.args.get('stressor')
        severity = request.args.get('severity')

        if not stressor or not severity:
            return jsonify({'error': 'Stressor and severity level are required.'}), 400

        # Fetch the recommendation document for the given stressor
        recommendation_data = recommendation_collection.find_one({'stressor': stressor})
        if not recommendation_data:
            return jsonify({'error': 'No recommendations found for this stressor.'}), 404

        # Extract the recommendation for the specific severity level
        severity_recommendations = recommendation_data.get('recommendations', {}).get(severity, [])
        if not severity_recommendations:
            return jsonify({'error': 'No recommendations found for this severity level.'}), 404

        # Return the first recommendation and source (assuming single recommendation per severity)
        recommendation = severity_recommendations[0]
        return jsonify({
            'text': recommendation.get('text', ''),
            'source': recommendation.get('source', '')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500





# Test Stress ---------------------------------


# Mapping of categorical responses to numeric values
mappings = {
    'Sadness': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Anxious': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Peer Pressure': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Sleep Quality': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'AI Tools': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Family Stress': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Financial Satisfaction': {'Very Satisfied': 1, 'Satisfied': 2, 'Neutral': 3, 'Dissatisfied': 4, 'Very Dissatisfied': 5},
    'Friends Support': {'Strongly Agree': 1, 'Agree': 2, 'Neutral': 3, 'Disagree': 4, 'Strongly Disagree': 5},
    'Resources Access': {'Excellent': 1, 'Good': 2, 'Adequate': 3, 'Poor': 4, 'Very Poor': 5},
    'Home Stress': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5},
    'Commute Stress': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5},
    'Noise Level': {'Very Manageable': 1, 'Manageable': 2, 'Neutral': 3, 'Disturbing': 4, 'Very Disturbing': 5},
    'Weather Conditions': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5},
    'Program Confidence': {'Yes': 1, 'No': 5},
    'Academic Stress': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5},
    'Advisor Support': {'Completely': 1, 'Very Much': 2, 'Moderately': 3, 'Somewhat': 4, 'Not at all': 5}
}


# Retrieve the question-to-feature mapping from MongoDB
def get_question_mapping():
    question_mapping = {}
    try:
        questions = questionnaires.find({})
        for question in questions:
            if '_id' in question and 'feature_name' in question:
                question_mapping[str(question['_id'])] = question['feature_name']
    except Exception as e:
        print(f"Error retrieving question mapping: {e}")
    return question_mapping

# Route to display the questionnaire
@app.route('/test_stress/', methods=['GET'])
@role_required('user')
def test_stress():
    username = session.get('username')

    if username:
        try:
            questions = list(questionnaires.find())  # Query the collection
            print(f"Fetched questions: {questions}")

            if not questions:
                return render_template('test_stress.html', username=username, questions=[])

            return render_template('test_stress.html', username=username, questions=questions)
        
        except Exception as e:
            print(f"Error fetching questions: {e}")
            return render_template('error.html', message="An error occurred while fetching questions.")
    else:
        return redirect(url_for('login'))

# New API endpoint to fetch questions as JSON
@app.route('/api/test_stress/', methods=['GET'])
@role_required('user')
def api_test_stress():
    username = session.get('username')

    if username:
        try:
            questions = list(questionnaires.find())
            print(f"Fetched questions: {questions}")

            # Convert questions to a simpler format, filtering out invalid entries
            questions_data = [
                {
                    "question": q.get('question_text'),
                    "type": q.get('question_type')
                } for q in questions if q.get('question_text') and q.get('question_type')
            ]

            # Optional: Log a warning if there are no valid questions
            if not questions_data:
                print("Warning: No valid questions found.")

            return jsonify({"questions": questions_data})

        except Exception as e:
            print(f"Error fetching questions: {e}")
            return jsonify({"error": "An error occurred while fetching questions."}), 500

    else:
        return jsonify({"error": "User not logged in."}), 401

@app.route('/test_stress/', methods=['POST'])
@role_required('user')
def handle_test_stress():
    responses = request.form.to_dict()
    username = session.get('username')

    if username:
        user = users_collection.find_one({'username': username})
        
        if not user:
            return jsonify({"error": "User not found."}), 404

        user_id = user['_id']

        # Save responses to the database using user_id
        try:
            save_responses_to_database(user_id, responses)  # Ensure this function is implemented correctly
            flash('Your responses have been successfully saved!', 'success')  # Add flash message
        except Exception as e:
            flash(f"Failed to save responses: {str(e)}", 'danger')  # Handle failure case
            return jsonify({"error": f"Failed to save responses: {str(e)}"}), 500

        return redirect(url_for('stress_result'))
    else:
        return redirect(url_for('login'))
    

# Function to save responses to the database
def save_responses_to_database(user_id, responses):
    response_data = {
        'user_id': user_id,
        'responses': responses,
        'timestamp': datetime.utcnow()  # Add current timestamp
    }
    # Insert the response data into the collection
    responses_collection.insert_one(response_data)
    
    
# Stressor mappings
stressor_mapping = {
    'Sadness': {'class': 'sadness', 'icon': 'fa-solid fa-face-sad-tear'},
    'Anxious': {'class': 'anxious', 'icon': 'fa-solid fa-heart-crack'},
    'Peer Pressure': {'class': 'peer-pressure', 'icon': 'fa-solid fa-people-arrows'},
    'Sleep Quality': {'class': 'sleep-quality', 'icon': 'fa-solid fa-bed'},
    'AI Tools': {'class': 'ai-tools', 'icon': 'fa-solid fa-robot'},
    'Family Stress': {'class': 'family-stress', 'icon': 'fa-solid fa-house-user'},
    'Financial Satisfaction': {'class': 'financial-satisfaction', 'icon': 'fa-solid fa-coins'},
    'Friends Support': {'class': 'friends-support', 'icon': 'fa-solid fa-user-friends'},
    'Resources Access': {'class': 'resources-access', 'icon': 'fa-solid fa-book-open'},
    'Home Stress': {'class': 'home-stress', 'icon': 'fa-solid fa-home'},
    'Commute Stress': {'class': 'commute-stress', 'icon': 'fa-solid fa-car'},
    'Noise Level': {'class': 'noise-level', 'icon': 'fa-solid fa-volume-high'},
    'Weather Conditions': {'class': 'weather-conditions', 'icon': 'fa-solid fa-cloud-sun'},
    'Program Confidence': {'class': 'program-confidence', 'icon': 'fa-solid fa-graduation-cap'},
    'Academic Stress': {'class': 'academic-stress', 'icon': 'fa-solid fa-book'},
    'Advisor Support': {'class': 'advisor-support', 'icon': 'fa-solid fa-chalkboard-teacher'}
}
    


# Route to display stress level input form and handle its submission
@app.route('/stress_level', methods=['GET', 'POST'])
@role_required('user')
def stress_level():
    if request.method == 'POST':
        # Capture form data
        stress_level = int(request.form.get('stress_level'))
        stressors = request.form.get('stressors')  # Comma-separated list
        date_tested = datetime.now()

        # Debugging to check form data
        print(f"DEBUG: Stress Level: {stress_level}, Stressors: {stressors}")

        # Fetch the username from session
        username = session.get('username')

        if username:
            # Fetch user ID based on the username
            user = users_collection.find_one({'username': username})
            user_id = user['_id']

            # Prepare assessment data for MongoDB insertion
            assessment_data = {
                'user_id': user_id,
                'stress_level': stress_level,
                'stressors': [s.strip() for s in stressors.split(',')],  # Convert string to list
                'date_tested': date_tested
            }

            # Insert assessment data into MongoDB
            assessment_collection.insert_one(assessment_data)

            # Redirect to the recommendation page
            return redirect(url_for('recommendation_page'))

        # Redirect to login if username not found in session
        return redirect(url_for('login'))

    # Render the stress level input form for GET requests
    return render_template('stress_level.html')


@app.route('/get_recommendations/<stressor_name>/<int:severity>', methods=['GET'])
@role_required('user')
def get_recommendations(stressor_name, severity):
    print(f"DEBUG: Fetching recommendations for Stressor: {stressor_name}, Severity: {severity}")
    
    recommendation_data = recommendation_collection.find_one({'stressor': stressor_name})

    if not recommendation_data:
        return jsonify({"error": "No recommendations found for this stressor."}), 404

    # Access recommendations by severity level
    severity_recommendations = recommendation_data.get('recommendations', {}).get(str(severity), [])

    if not severity_recommendations:
        return jsonify({
            "stressor": stressor_name,
            "severity": severity,
            "recommendations": []  # Return an empty list
        })

    return jsonify({
        'stressor': stressor_name,
        'severity': severity,
        'recommendations': severity_recommendations
    })


# Preprocess and replace categorical values with numeric equivalents
def process_mongo_responses(mongo_response, question_mapping):
    responses = mongo_response.get('responses', {})
    student_data = {}

    # Map question IDs to feature names
    for question_id, answer in responses.items():
        feature_name = question_mapping.get(str(question_id))  # Get the feature name
        if feature_name and feature_name in mappings:
            # Use feature_name as the column in the DataFrame
            student_data[feature_name] = [mappings[feature_name].get(answer, 3)]  # Default to 3 if not found

    # Create DataFrame from student responses
    student_df = pd.DataFrame(student_data)

    # DEBUG: Print the processed DataFrame
    print("DEBUG: Processed DataFrame before prediction:")
    print(student_df)

    return student_df

# Route for Stress Result Page
@app.route('/stress_result/')
@role_required('user')
def stress_result():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = users_collection.find_one({'username': username})
    if not user:
        return redirect(url_for('login'))

    user_id = user['_id']
    response = responses_collection.find_one({'user_id': user_id}, sort=[('timestamp', -1)])

    if not response:
        return handle_no_responses(request)

    question_mapping = get_question_mapping()
    student_df = process_mongo_responses(response, question_mapping)

    if student_df.empty:
        return handle_no_valid_responses(request)

    # Ensure required columns are in the DataFrame
    expected_columns = [
        'Sadness', 'Anxious', 'Peer Pressure', 'Sleep Quality', 'AI Tools',
        'Family Stress', 'Financial Satisfaction', 'Friends Support',
        'Resources Access', 'Home Stress', 'Commute Stress', 'Noise Level',
        'Weather Conditions', 'Program Confidence', 'Academic Stress',
        'Advisor Support'
    ]

    for col in expected_columns:
        if col not in student_df.columns:
            student_df[col] = 3  # Default to neutral if missing

    student_transformed = preprocessor.transform(student_df)
    predicted_stress_level = knn_model.predict(student_transformed)[0]

    common_stressors, detailed_recommendations, primary_recommendation = [], [], None

    # Stressor mapping with icons
    stressor_mapping = {
        'Sadness': {'class': 'sadness', 'icon': 'fa-solid fa-face-sad-tear'},
        'Anxious': {'class': 'anxious', 'icon': 'fa-solid fa-heart-crack'},
        'Peer Pressure': {'class': 'peer-pressure', 'icon': 'fa-solid fa-people-arrows'},
        'Sleep Quality': {'class': 'sleep-quality', 'icon': 'fa-solid fa-bed'},
        'AI Tools': {'class': 'ai-tools', 'icon': 'fa-solid fa-robot'},
        'Family Stress': {'class': 'family-stress', 'icon': 'fa-solid fa-house-user'},
        'Financial Satisfaction': {'class': 'financial-satisfaction', 'icon': 'fa-solid fa-coins'},
        'Friends Support': {'class': 'friends-support', 'icon': 'fa-solid fa-user-friends'},
        'Resources Access': {'class': 'resources-access', 'icon': 'fa-solid fa-book-open'},
        'Home Stress': {'class': 'home-stress', 'icon': 'fa-solid fa-home'},
        'Commute Stress': {'class': 'commute-stress', 'icon': 'fa-solid fa-car'},
        'Noise Level': {'class': 'noise-level', 'icon': 'fa-solid fa-volume-high'},
        'Weather Conditions': {'class': 'weather-conditions', 'icon': 'fa-solid fa-cloud-sun'},
        'Program Confidence': {'class': 'program-confidence', 'icon': 'fa-solid fa-graduation-cap'},
        'Academic Stress': {'class': 'academic-stress', 'icon': 'fa-solid fa-book'},
        'Advisor Support': {'class': 'advisor-support', 'icon': 'fa-solid fa-chalkboard-teacher'}
    }

    for stressor, data in stressor_mapping.items():
        severity = student_df.get(stressor, [3])[0]
        recommendation_data = recommendation_collection.find_one({'stressor': stressor})
        
        # Access recommendations as list of dictionaries with text and source keys
        recs = []
        if recommendation_data:
            recs = [
                {"text": rec.get("text"), "source": rec.get("source")}
                for rec in recommendation_data['recommendations'].get(str(severity), [])
            ]

        if severity in [3, 4, 5]:  # Only show stressors with higher severity
            common_stressors.append({
                "name": stressor,
                "class": data['class'],
                "icon": data['icon'],
                "recommendations": recs
            })

        if recs:
            detailed_recommendations.append({
                "stressor": stressor,
                "severity": severity,
                "recommendation": recs[0]
            })

        if severity in [3, 4, 5] and not primary_recommendation:
            primary_recommendation = recs[0] if recs else None

    if not primary_recommendation:
        primary_recommendation = {
            "text": "Maintain a balanced routine. No significant stressors detected.",
            "source": "General Advice"
        }

    assessment_result = {
        "user_id": user_id,
        "stress_level": int(predicted_stress_level),
        "stressors": [rec['stressor'] for rec in detailed_recommendations],
        "recommendations": primary_recommendation,
        "date_tested": datetime.now(),
        "response_id": response['_id']
    }
    assessment_collection.insert_one(assessment_result)

    if request.args.get('format') == 'json':
        return jsonify({
            'username': username,
            'predicted_stress_level': int(predicted_stress_level),
            'common_stressors': common_stressors
        })

    return render_template(
        'stress_result.html',
        username=username,
        predicted_stress_level=int(predicted_stress_level),
        common_stressors=common_stressors
    )

def handle_no_responses(request):
    if request.args.get('format') == 'json':
        return jsonify({"error": "No responses found for this user beng beng."}), 404
    # Redirect to a 'no data' route if not JSON
    return redirect(url_for('no_data_route'))

def handle_no_valid_responses(request):
    if request.args.get('format') == 'json':
        return jsonify({"error": "No valid responses found for this user beng beng beng."}), 404
    return "No valid responses found for this user."



@app.route('/no-data')
@role_required('user')
def no_data():
    # Fetch username from session
    username = session.get('username')

    if username:
        # Fetch assessment data for the user
        user = users_collection.find_one({'username': username})

        return render_template('no_data.html', username=username)
    else:
        # Redirect to login if the user is not logged in
        return redirect(url_for('login'))


# Route to display detailed assessment and responses
@app.route('/result')
@role_required('user')
def result():
    username = session.get('username')

    if username:
        # Fetch user data from MongoDB
        user = users_collection.find_one({'username': username})
        if not user:
            return "User not found."

        user_id = user['_id']
        response = responses_collection.find_one({'user_id': user_id}, sort=[('timestamp', -1)])

        if not response:
            return "No responses found for this user."

        # Fetch question mappings
        question_mapping = get_question_mapping()

        # Process user's responses
        student_df = process_mongo_responses(response, question_mapping)

        if student_df.empty:
            return "No valid responses found for this user."

        # Check for missing columns and fill with neutral default values (e.g., median)
        expected_columns = [
            'Sadness', 'Anxious', 'Peer Pressure', 'Sleep Quality', 'AI Tools',
            'Family Stress', 'Financial Satisfaction', 'Friends Support',
            'Resources Access', 'Home Stress', 'Commute Stress', 'Noise Level',
            'Weather Conditions', 'Program Confidence', 'Academic Stress',
            'Advisor Support'
        ]

        for col in expected_columns:
            if col not in student_df.columns:
                print(f"DEBUG: Column {col} is missing, defaulting to 3")
                student_df[col] = 3  # Default to neutral value if column is missing

        # Preprocess student data
        student_transformed = preprocessor.transform(student_df)

        # DEBUG: Print transformed data before prediction
        print("DEBUG: Transformed Data for Model Prediction:", student_transformed)

        # Predict stress level
        try:
            predicted_stress_level = knn_model.predict(student_transformed)[0]
        except Exception as e:
            print(f"ERROR: Prediction failed - {str(e)}")
            return "Error during stress level prediction."

        # DEBUG: Check neighbors of the KNN model for this prediction
        try:
            neighbors = knn_model.kneighbors(student_transformed, n_neighbors=5, return_distance=True)
            print(f"DEBUG: Neighbors' Distances: {neighbors[0]}")
            print(f"DEBUG: Neighbors' Labels: {neighbors[1]}")
        except Exception as e:
            print(f"ERROR: Failed to retrieve KNN neighbors - {str(e)}")
            return "Error retrieving KNN neighbors."

        # Update stressor mapping to use FontAwesome 6 icons for a prettier design
        stressor_mapping = {
            'Sadness': {'class': 'sadness', 'icon': 'fa-solid fa-face-sad-tear'},
            'Anxious': {'class': 'anxious', 'icon': 'fa-solid fa-heart-crack'},
            'Peer Pressure': {'class': 'peer-pressure', 'icon': 'fa-solid fa-people-arrows'},
            'Sleep Quality': {'class': 'sleep-quality', 'icon': 'fa-solid fa-bed'},
            'AI Tools': {'class': 'ai-tools', 'icon': 'fa-solid fa-robot'},  
            'Family Stress': {'class': 'family-stress', 'icon': 'fa-solid fa-house-user'},
            'Financial Satisfaction': {'class': 'financial-satisfaction', 'icon': 'fa-solid fa-coins'},
            'Friends Support': {'class': 'friends-support', 'icon': 'fa-solid fa-user-friends'},
            'Resources Access': {'class': 'resources-access', 'icon': 'fa-solid fa-book-open'},
            'Home Stress': {'class': 'home-stress', 'icon': 'fa-solid fa-home'},
            'Commute Stress': {'class': 'commute-stress', 'icon': 'fa-solid fa-car'},
            'Noise Level': {'class': 'noise-level', 'icon': 'fa-solid fa-volume-high'},
            'Weather Conditions': {'class': 'weather-conditions', 'icon': 'fa-solid fa-cloud-sun'},
            'Program Confidence': {'class': 'program-confidence', 'icon': 'fa-solid fa-graduation-cap'},
            'Academic Stress': {'class': 'academic-stress', 'icon': 'fa-solid fa-book'},
            'Advisor Support': {'class': 'advisor-support', 'icon': 'fa-solid fa-chalkboard-teacher'}
        }

        # Create a list of dictionaries with 'icon', 'name', and 'class' for each common stressor
        common_stressors = [
            {"name": key, "class": data['class'], "icon": data['icon']}
            for key, data in stressor_mapping.items()
            if student_df[key][0] in [4, 5]
        ]

        return render_template(
            'result.html',
            username=username,
            responses=response.get('responses', {}),
            assessment=response.get('assessment', {}),
            questions=question_mapping,  # Pass the full question mapping
            stress_feedback=response.get('stress_feedback', {}),
            predicted_stress_level=int(predicted_stress_level) if predicted_stress_level is not None else None,
            common_stressors=common_stressors
        )
    else:
        return redirect(url_for('login'))
    

# Route for Recommendation Page
@app.route('/recommendation/')
@role_required('user')
def recommendation():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = users_collection.find_one({'username': username})
    if not user:
        return redirect(url_for('login'))

    user_id = user['_id']
    response = responses_collection.find_one({'user_id': user_id}, sort=[('timestamp', -1)])
    
    if not response:
        return handle_no_responses(request)

    question_mapping = get_question_mapping()
    student_df = process_mongo_responses(response, question_mapping)
    
    if student_df.empty:
        return handle_no_valid_responses(request)

    # Ensure required columns are in the DataFrame
    expected_columns = [
        'Sadness', 'Anxious', 'Peer Pressure', 'Sleep Quality', 'AI Tools',
        'Family Stress', 'Financial Satisfaction', 'Friends Support',
        'Resources Access', 'Home Stress', 'Commute Stress', 'Noise Level',
        'Weather Conditions', 'Program Confidence', 'Academic Stress',
        'Advisor Support'
    ]
    
    for col in expected_columns:
        if col not in student_df.columns:
            student_df[col] = 3  # Default to neutral if missing

    student_transformed = preprocessor.transform(student_df)
    predicted_stress_level = knn_model.predict(student_transformed)[0]

    common_stressors, detailed_recommendations, primary_recommendation = [], [], None

    # Stressor mapping with icons
    stressor_mapping = {
        'Sadness': {'class': 'sadness', 'icon': 'fa-solid fa-face-sad-tear'},
        'Anxious': {'class': 'anxious', 'icon': 'fa-solid fa-heart-crack'},
        'Peer Pressure': {'class': 'peer-pressure', 'icon': 'fa-solid fa-people-arrows'},
        'Sleep Quality': {'class': 'sleep-quality', 'icon': 'fa-solid fa-bed'},
        'AI Tools': {'class': 'ai-tools', 'icon': 'fa-solid fa-robot'},
        'Family Stress': {'class': 'family-stress', 'icon': 'fa-solid fa-house-user'},
        'Financial Satisfaction': {'class': 'financial-satisfaction', 'icon': 'fa-solid fa-coins'},
        'Friends Support': {'class': 'friends-support', 'icon': 'fa-solid fa-user-friends'},
        'Resources Access': {'class': 'resources-access', 'icon': 'fa-solid fa-book-open'},
        'Home Stress': {'class': 'home-stress', 'icon': 'fa-solid fa-home'},
        'Commute Stress': {'class': 'commute-stress', 'icon': 'fa-solid fa-car'},
        'Noise Level': {'class': 'noise-level', 'icon': 'fa-solid fa-volume-high'},
        'Weather Conditions': {'class': 'weather-conditions', 'icon': 'fa-solid fa-cloud-sun'},
        'Program Confidence': {'class': 'program-confidence', 'icon': 'fa-solid fa-graduation-cap'},
        'Academic Stress': {'class': 'academic-stress', 'icon': 'fa-solid fa-book'},
        'Advisor Support': {'class': 'advisor-support', 'icon': 'fa-solid fa-chalkboard-teacher'}
    }

    for stressor, data in stressor_mapping.items():
        severity = student_df.get(stressor, [3])[0]
        recommendation_data = recommendation_collection.find_one({'stressor': stressor})
        
        # Access recommendations as list of dictionaries with text and source keys
        recs = []
        if recommendation_data:
            recs = [
                {"text": rec.get("text"), "source": rec.get("source")}
                for rec in recommendation_data['recommendations'].get(str(severity), [])
            ]

        if severity in [3, 4, 5]:  # Only show stressors with higher severity
            common_stressors.append({
                "name": stressor,
                "class": data['class'],
                "icon": data['icon'],
                "recommendations": recs
            })

        if recs:
            detailed_recommendations.append({
                "stressor": stressor,
                "severity": severity,
                "recommendation": recs[0]
            })

        if severity in [3, 4, 5] and not primary_recommendation:
            primary_recommendation = recs[0] if recs else None

    if not primary_recommendation:
        primary_recommendation = {
            "text": "Maintain a balanced routine. No significant stressors detected.",
            "source": "General Advice"
        }

    if request.args.get('format') == 'json':
        return jsonify({
            'username': username,
            'predicted_stress_level': int(predicted_stress_level),
            'common_stressors': common_stressors
        })

    return render_template(
        'recommendation.html',
        username=username,
        predicted_stress_level=int(predicted_stress_level),
        common_stressors=common_stressors
    )

def handle_no_responses(request):
    if request.args.get('format') == 'json':
        return jsonify({"error": "No responses found for this user."}), 404
    # Redirect to a 'no data' route if not JSON
    return redirect(url_for('no_data'))

def handle_no_valid_responses(request):
    if request.args.get('format') == 'json':
        return jsonify({"error": "No valid responses found for this user. harsh"}), 404
    return "No valid responses found for this user."


@app.route('/feedback', methods=['GET', 'POST'])
@role_required('user')
def feedback():
    username = session.get('username')
    if not username:
        print("Session username is None")
        return "Unauthorized access", 401

    print(f"Username from session: {username}")

    if request.method == 'POST':
        feedback_text = request.form.get('feedback')
        if not feedback_text:
            flash("Feedback cannot be empty!", "error")
            return redirect(url_for('feedback'))

        print(f"Feedback text received: {feedback_text}")

        user = users_collection.find_one({'username': username})
        if not user:
            print(f"User not found for username: {username}")
            return "User not found", 404

        try:
            feedback_data = {
                'feedback': feedback_text,
                'user_id': user['_id'],
                'username': username,
                'name': user.get('name', 'Unknown'),
                'timestamp': datetime.now()
            }
            feedback_collection.insert_one(feedback_data)
            print(f"Feedback saved: {feedback_data}")
            flash("Thank you for your feedback!", "success")
        except Exception as e:
            print(f"Error saving feedback: {e}")
            flash("Internal Server Error. Please try again later.", "error")
            return redirect(url_for('feedback'))

        # Redirect to avoid form resubmission
        return redirect(url_for('feedback'))

    # Fetch previous feedback for display
    feedback_list = feedback_collection.find({'username': username}).sort('timestamp', -1)
    return render_template('feedback.html', username=username, feedback_list=feedback_list)

@app.route('/analytics/')
@role_required('user')
def analytics():
    username = session.get('username')

    if username:
        user = users_collection.find_one({'username': username})
        if user:
            user_id = user['_id']
            print(f"User ID: {user_id}")  # Debugging print to check user_id

            # Retrieve filter, sort, and pagination parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            sort_order = request.args.get('sort_order', 'des')  # Default to descending
            page = int(request.args.get('page', 1))  # Current page
            per_page = 10  # Items per page

            # Convert sort_order to MongoDB-compatible sort direction
            sort_direction = ASCENDING if sort_order == 'asc' else DESCENDING

            # Build the MongoDB query with optional date filtering
            query = {'user_id': user_id}
            if start_date:
                query['date_tested'] = {'$gte': datetime.strptime(start_date, '%Y-%m-%d')}
            if end_date:
                query.setdefault('date_tested', {}).update({'$lte': datetime.strptime(end_date, '%Y-%m-%d')})

            # Fetch and sort assessments with pagination
            total_assessments = assessment_collection.count_documents(query)  # Total assessments count
            assessments = list(
                assessment_collection.find(query)
                .sort('date_tested', sort_direction)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
            print(assessments)  # Debugging print to check fetched assessments

            # Redirect to no_history.html if there are no assessments
            if not assessments:
                return render_template('no_history.html', username=username)

            # Dictionary to store the frequency of each stressor
            stressor_frequency = defaultdict(int)

            # Process each assessment
            for assessment in assessments:
                stressors = assessment.get('stressors', [])  # Assuming stressors are stored as a list
                for stressor in stressors:
                    stressor_frequency[stressor] += 1

            # Convert stressor data into a list of tuples to pass to the template
            stressor_data = [(stressor, count) for stressor, count in stressor_frequency.items()]

            # Create a dictionary to store the total stress level and count per month
            stress_levels_by_month = defaultdict(lambda: {'total_stress': 0, 'count': 0})

            # Process each assessment
            for assessment in assessments:
                date_tested = assessment['date_tested']
                try:
                    # Convert date_tested to a datetime object if it's a string
                    if isinstance(date_tested, str):
                        date_tested = datetime.strptime(date_tested, '%Y-%m-%d')  # Adjust format as needed

                    stress_level = float(assessment['stress_level'])  # Convert to float
                except (ValueError, TypeError):
                    continue  # Skip this entry if conversion fails

                month = date_tested.strftime('%B')  # Get the full month name

                # Add stress level to the appropriate month
                stress_levels_by_month[month]['total_stress'] += stress_level
                stress_levels_by_month[month]['count'] += 1

            # Calculate the average stress level per month
            avg_stress_by_month = []
            for month in calendar.month_name[1:]:  # Loop through all months
                if stress_levels_by_month[month]['count'] > 0:
                    avg_stress = stress_levels_by_month[month]['total_stress'] / stress_levels_by_month[month]['count']
                    avg_stress_by_month.append((month, avg_stress))
                else:
                    avg_stress_by_month.append((month, 0))  # No data for this month

            # Calculate pagination details
            total_pages = math.ceil(total_assessments / per_page)
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)

            # Pass assessments, average stress, stressor data, and pagination info to the template
            return render_template(
                'analytics.html',
                username=username,
                assessments=assessments,
                avg_stress_by_month=avg_stress_by_month,
                stressor_data=stressor_data,
                page=page,
                total_pages=total_pages,
                start_page=start_page,
                end_page=end_page
            )
        else:
            return redirect(url_for('login'))  # User not found
    else:
        return redirect(url_for('login'))  # Not logged in

    


# View Assessment History
@app.route('/assessment/<assessment_id>')
@role_required('user')
def view_assessment(assessment_id):
    try:
        # Get the username from the session
        username = session.get('username')
        if not username:
            return "User not logged in.", 401

        # Fetch the user from the database using the username
        user = users_collection.find_one({'username': username})
        if not user:
            return "User not found.", 404

        # Fetch the assessment from the assessment_result collection
        assessment = db.assessment_result.find_one({'_id': ObjectId(assessment_id)})
    except Exception as e:
        return f"Error retrieving assessment: {str(e)}", 500

    if not assessment:
        return "Assessment not found", 404

    # Use response_id from assessment to get responses
    response_id = assessment.get('response_id')
    if not response_id:
        return "No response ID found in this assessment.", 404
    
    # Fetch the student's response using the response_id
    response = db.response.find_one({'_id': ObjectId(response_id)})
    if not response:
        return "Response not found for this assessment.", 404

    # Extract question IDs and responses
    question_ids = list(response['responses'].keys())  # Get the list of question IDs
    student_responses = list(response['responses'].values())  # Get the corresponding responses

    # Fetch the questions based on the question IDs
    questions = list(db.stress_questions.find({'_id': {'$in': [ObjectId(q_id) for q_id in question_ids]}}))

    # Prepare the data to be passed to the template
    question_response_pairs = [
        {'question': question['question'], 'response': student_responses[i]} 
        for i, question in enumerate(questions)
    ]

    # Pass the username and user data to the template
    return render_template(
        'view_assessment.html',
        username=username,
        user=user,
        assessment=assessment,
        question_response_pairs=question_response_pairs
    )

@app.route('/profile/', methods=['GET', 'POST'])
@role_required('user')
def profile():
    username = session.get('username')
    if username:
        user = users_collection.find_one({'username': username})
        
        if request.method == 'POST':
            # Collect data safely with .get() to avoid KeyError
            name = request.form.get('name', user.get('name'))
            age = request.form.get('age', user.get('age'))
            gender = request.form.get('gender', user.get('gender'))
            year_level = request.form.get('year-level', user.get('year_level'))

            # Check if no changes were made
            if name == user.get('name') and age == str(user.get('age')) and gender == user.get('gender') and year_level == user.get('year_level'):
                flash("No changes detected. Please modify at least one field before saving.", "error")
                return redirect(url_for('profile'))  # Redirect back to the profile page

            # Update the user's information in the database
            users_collection.update_one(
                {'username': username},
                {'$set': {
                    'name': name,
                    'age': int(age) if age else None,
                    'gender': gender,
                    'year_level': year_level
                }}
            )

            # Refetch updated user data
            user = users_collection.find_one({'username': username})
            flash("Profile successfully updated.", "success")
            return render_template('profile.html', username=username, user=user)

        # Render the profile page with existing user information
        return render_template('profile.html', username=username, user=user)
    else:
        # Redirect to login if the user is not logged in
        return redirect(url_for('login'))

    


@app.route('/change_email', methods=['POST'])
@role_required('user')
def change_email():
    # Get the logged-in username
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    # Fetch user data from the database
    user = users_collection.find_one({'username': username})
    if not user:
        return render_template('profile.html', error_message="User not found.", user=None)

    # Retrieve form data
    new_email = request.form.get('new_email')
    password = request.form.get('password')

    # Check if the password is correct
    stored_password = user['password']
    if not check_password_hash(stored_password, password):
        return render_template('profile.html', error_message="Incorrect password for email change.", user=user)

    # Check if the new email is the same as the current one
    if new_email == user.get('email'):
        flash("No changes detected. The new email is the same as the current one.", "error")
        return redirect(url_for('profile'))  # Redirect back to the profile page

    # If password verification passes and the email is different, update the email
    users_collection.update_one({'username': username}, {'$set': {'email': new_email}})

    # Pass updated user data to the template with success message
    user['email'] = new_email
    flash("Email successfully updated.", "success")
    return render_template('profile.html', success_message="Email successfully updated.", user=user)



@app.route('/check_password', methods=['POST'])
@role_required('user')
def check_password():
    # Get the logged-in username
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    # Fetch user data from the database
    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Retrieve the current password from the request
    current_password = request.json.get('password')

    # Retrieve the stored (hashed) password
    stored_password = user.get('password')

    # Check if the password is correct using hashing
    if not check_password_hash(stored_password, current_password):
        flash("Incorrect current password.", "error")
        return jsonify({'success': False, 'message': 'Incorrect current password'}), 400

    # Return success if the password is correct
    return jsonify({'success': True}), 200



@app.route('/change_password', methods=['POST'])
@role_required('user')
def change_password():
    # Get the logged-in username
    username = session.get('username')
    if not username:
        flash("User not authenticated. Please log in to change your password.", "error")
        return redirect(url_for('login'))

    # Fetch user data from the database
    user = users_collection.find_one({'username': username})
    if not user:
        flash("User not found.", "error")
        return render_template('profile.html', user=None)

    # Retrieve form data
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    # Check if current password is correct
    stored_password = user['password']
    if not check_password_hash(stored_password, current_password):
        flash("Incorrect current password.", "error")
        return render_template('profile.html', user=user)

    # Check if new password and confirm new password match
    if new_password != confirm_new_password:
        flash("New passwords do not match.", "error")
        return render_template('profile.html', user=user)

    # Hash the new password and update it in the database
    hashed_new_password = generate_password_hash(new_password)
    users_collection.update_one({'username': username}, {'$set': {'password': hashed_new_password}})

    # Flash success message and redirect to profile page
    flash("Password successfully updated.", "success")
    return redirect(url_for('profile'))



# Route for dashboard
@app.route('/dashboard/<username>')
@role_required('user')
def dashboard(username):

    # Ensure the user is logged in
    if 'user_id' not in session or session.get('username') != username:
        return redirect(url_for('login'))  # Redirect to login if not logged in or if username doesn't match

    # Fetch user data from the database
    user = users_collection.find_one({'username': username})
    
    if not user:
        return "User not found", 404

    user_id = user['_id']

    # Fetch the latest assessment result for the user
    latest_assessment = assessment_collection.find_one({'user_id': user_id}, sort=[('date_tested', pymongo.DESCENDING)])

    if latest_assessment:
        # Extract the stress level from the latest assessment result
        stress_level = int(latest_assessment['stress_level'])
    else:
        stress_level = None

    # MongoDB aggregation pipeline to get the top 4 stressors for the logged-in user
    pipeline = [
        {"$match": {"user_id": user_id}},  # Filter by user_id
        {"$unwind": "$stressors"},  # Unwind the stressors array
        {"$group": {"_id": "$stressors", "count": {"$sum": 1}}}, 
        {"$sort": {"count": -1}},
        {"$limit": 4}
    ]

    # Execute the pipeline and get the top stressors
    top_stressors = list(assessment_collection.aggregate(pipeline))

    # Pass the top stressors, user, and other data to the template
    return render_template('dashboard.html', username=username, user=user, stress_level=stress_level, latest_assessment=latest_assessment, top_stressors=top_stressors)


#Sign in


@app.route('/signin', methods=['POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        gender = request.form['gender']
        year_level = request.form['year_level']
        age = int(request.form['age'])  # Convert age to integer
        
        # Set the role to 'user'
        role = 'user'
    
        # Check if user exists in MongoDB
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            # Return error response if the user already exists
            return jsonify({'error': 'User already exists!'})
        else:
            # Hash the password before saving it to the database
            hashed_password = generate_password_hash(password)
            
            # Insert new user into the database with the provided role and hashed password
            new_user = {
                'username': username,
                'password': hashed_password,
                'role': role,
                'email': email,
                'gender': gender,
                'year_level': year_level,
                'age': age
            }
            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)  # Get the newly created user's ID
            
            # Store user ID and username in session
            session['user_id'] = user_id
            session['username'] = username
            
            # Return success response and the URL to redirect to the login page
            return jsonify({'success': 'Sign up successful!', 'redirect_url': url_for('login')})

@app.route('/signin', methods=['GET'])
def signup():
    return render_template('signin.html')

# faqs

@app.route('/faqs/')
@role_required('user')
def faqs():
    # Fetch username from session
    username = session.get('username')

    if username:
        # Fetch assessment data for the user
        user = users_collection.find_one({'username': username})

        return render_template('faqs.html', username=username)
    else:
        # Redirect to login if the user is not logged in
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/logout')
def admin_logout():
    # Clear all session data
    session.clear()
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

