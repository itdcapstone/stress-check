import re

from bson import ObjectId
from bson.objectid import ObjectId
# pip install pymongo

from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask import jsonify
from dotenv import load_dotenv
# pip install flask

from pymongo import MongoClient
from pymongo import DESCENDING
from pymongo import ASCENDING
import pymongo
# pip install pymongo

from werkzeug.security import generate_password_hash, check_password_hash
# pip install werkzeug

from datetime import datetime
from collections import defaultdict
import calendar
import pickle
import os

import pandas as pd
# pip install pandas

from bcrypt import hashpw, gensalt
import bcrypt
# pip install bcrypt

# Load environment variables from the .env file
load_dotenv()

# Get MongoDB URI and Flask Secret Key from environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize Flask app
app = Flask(__name__, static_folder='../client', template_folder='../client')

# Set Flask secret key for session management
app.secret_key = SECRET_KEY  # Get secret key from environment variable

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)  # Connect to MongoDB using the URI from environment variable
db = client.get_database('dbAdmin')

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




# Landing page
@app.route('/')
def index():
    return render_template('landing/landing.html')


#log in

# Route for student login in the root folder
@app.route('/student_login', methods=['GET'])
def student_login():
    # Add your login logic here for students
    return render_template('login.html')  # Render the student login page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']  # This can be either username or email
        password = request.form['password']
        
        # Check if the input is a username or email
        if '@' in username_or_email:  # If the input contains '@', treat it as an email
            existing_user = users_collection.find_one({'email': username_or_email})
        else:
            existing_user = users_collection.find_one({'username': username_or_email})
        
        if existing_user:
            # Check if the user has the role of "user"
            if existing_user.get('role') != 'user':
                flash('Your role is not allowed to log in.', 'error')
                return redirect(url_for('login'))

            # Check if the hashed password matches the input password
            if check_password_hash(existing_user['password'], password):
                session['user_id'] = str(existing_user['_id'])
                session['username'] = existing_user['username']  # Use the username from the DB
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard', username=existing_user['username']))
            else:
                # Flash message for incorrect password
                flash('Incorrect password. Please try again.', 'error')
                return redirect(url_for('login'))
        else:
            # Flash message for user not found
            flash('No account found with the provided username or email.', 'error')
            return redirect(url_for('login'))

    # Render the login page for GET requests
    return render_template('login.html')




# Route for admin login in the admin folder
@app.route('/admin_login')
def admin_login():
   
    return render_template('admin/login.html')  # Render the admin login page


@app.route('/admin_login', methods=['POST'])
def admin_login_dashboard():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        # Query the database for username or email match
        existing_user = users_collection.find_one({
            '$or': [{'username': identifier}, {'email': identifier}]
        })

        if not existing_user:
            return jsonify({'error': 'Invalid username or email!'})

        if not check_password_hash(existing_user.get('password'), password):
            return jsonify({'error': 'Invalid password!'})

        if existing_user.get('role') != 'admin':
            return jsonify({'error': 'Insufficient permissions!'})

        # Store user data in session
        session['username'] = existing_user.get('username')

        # Respond with success message and redirect URL
        return jsonify({
            'success': 'Login successful!',
            'redirect_url': url_for('admin_dashboard')
        })





# admin dashboard =====================
    
# Admin route for admin dashboard
@app.route('/admin_dashboard')
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
def management():
    username = session.get('username')

    if username:
        # Pagination logic
        page = request.args.get('page', 1, type=int)  # Get the page number from the query params (default: 1)
        per_page = 20  # Number of users to display per page

        # Get total number of users
        total_users = users_collection.count_documents({})

        # Fetch users for the current page
        users = users_collection.find().skip((page - 1) * per_page).limit(per_page)
        users = list(users)  # Convert cursor to list for rendering

        # Calculate total pages
        total_pages = (total_users + per_page - 1) // per_page  # Ceiling division

        # Calculate start and end page for pagination buttons
        start_page = max(1, page - 1)
        end_page = min(total_pages, page + 2)

        if request.method == 'POST':
            if 'edit_user' in request.form:
                user_id = request.form.get('user_id')  # Get the user ID from the form
                app.logger.info(f"Edit request for user_id: {user_id}")
                if user_id:
                    try:
                        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
                        if user_data:
                            app.logger.info(f"User data found: {user_data}")
                            return render_template('admin/edit_user.html', username=username, user=user_data)
                        else:
                            flash("No user found with the provided ID.", "error")
                    except Exception as e:
                        flash("Error retrieving user data.", "error")

            elif 'delete_user' in request.form:
                # Handle delete request
                user_id = request.form.get('user_id')
                if user_id:
                    app.logger.info(f"Attempting to delete user with ID: {user_id}")
                    try:
                        users_collection.delete_one({'_id': ObjectId(user_id)})
                        flash("User successfully deleted.", "success")  # Success message
                    except Exception as e:
                        flash("Error deleting user.", "error")
                return redirect(url_for('management'))

        # Render the user management page with pagination data
        return render_template(
            'admin/management.html',
            username=username,
            users=users,
            page=page,
            total_pages=total_pages,
            start_page=start_page,
            end_page=end_page
        )
    else:
        return redirect(url_for('login'))


@app.route('/admin/dashboard/')
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
def data():

    # Default filter values
    filter_criteria = {}

    # Get filters from request (e.g., date range)
    start_date = request.args.get('start_date')  # Format: YYYY-MM-DD
    end_date = request.args.get('end_date')      # Format: YYYY-MM-DD

    # Build date range filter
    if start_date and end_date:
        try:
            filter_criteria["date_tested"] = {
                "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
                "$lte": datetime.strptime(end_date, "%Y-%m-%d")
            }
            print("Filter criteria:", filter_criteria)  # Debugging line to check the filter
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD'.", 400
    else:
        # Optional: Set a default date range
        filter_criteria["date_tested"] = {
            "$gte": datetime(2000, 1, 1),
            "$lte": datetime.now()
        }

    print("Final filter criteria:", filter_criteria)  # Debugging line to ensure the filter is correct

    # Use assessment collection for count
    assessment_count = assessment_collection.count_documents(filter_criteria)

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
                           chart_data=chart_data,
                           column_chart_data=column_chart_data,
                           year_level_student_counts=year_level_student_counts,
                           stressor_data=stressor_data,
                           stress_level_data=stress_level_data,
                           assessment_count=assessment_count,  # Now using assessment_count
                           start_date=start_date,
                           end_date=end_date)
    
    
@app.route('/admin/feedback/', methods=['GET', 'POST'])
def admin_feedback():
    # Handle date filtering (GET request)
    date_filter = request.args.get('dateFilter')
    query = {}

    if date_filter:
        try:
            # Parse the user input in 'YYYY-MM-DD' format
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
            
            # Set the start and end of the day
            start_date = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = filter_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Construct the query to filter feedback by the provided date
            query = {'timestamp': {'$gte': start_date, '$lte': end_date}}

        except ValueError:
            print(f"Invalid date format for filter: {date_filter}. Expected format is 'YYYY-MM-DD'.")
            pass  # Ignore invalid date formats

    # Fetch filtered feedback data from the MongoDB feedback collection
    feedback_data = list(feedback_collection.find(query))

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
    return render_template('admin/feedback.html', feedback_data=feedback_data)



@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
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
def analytics():
    username = session.get('username')

    if username:
        user = users_collection.find_one({'username': username})
        if user:
            user_id = user['_id']
            print(f"User ID: {user_id}")  # Debugging print to check user_id

            # Retrieve filter and sort parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            sort_order = request.args.get('sort_order', 'des')  # Default to descending

            # Convert sort_order to MongoDB-compatible sort direction
            sort_direction = ASCENDING if sort_order == 'asc' else DESCENDING

            # Build the MongoDB query with optional date filtering
            query = {'user_id': user_id}
            if start_date:
                query['date_tested'] = {'$gte': datetime.strptime(start_date, '%Y-%m-%d')}
            if end_date:
                query.setdefault('date_tested', {}).update({'$lte': datetime.strptime(end_date, '%Y-%m-%d')})

            # Fetch and sort assessments
            assessments = list(assessment_collection.find(query).sort('date_tested', sort_direction))
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

            # Pass assessments, average stress, and stressor data to the template
            return render_template('analytics.html', username=username, assessments=assessments,
                                   avg_stress_by_month=avg_stress_by_month, stressor_data=stressor_data)
        else:
            return redirect(url_for('login'))  # User not found
    else:
        return redirect(url_for('login'))  # Not logged in
    


# View Assessment History
@app.route('/assessment/<assessment_id>')
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
            return jsonify({'success': 'Sign-in successful!', 'redirect_url': url_for('login')})

@app.route('/signin', methods=['GET'])
def signup():
    return render_template('signin.html')

# faqs

@app.route('/faqs/')
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
    # Clear session variables
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/admin/logout')
def admin_logout():
    # Clear session variables
    session.pop('username', None)
    return redirect(url_for('admin_login'))

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

