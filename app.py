# app.py
import uuid
from flask import Flask, request, jsonify, redirect, render_template
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from flask_cors import CORS
import os
import requests
from bson.objectid import ObjectId
from bson import ObjectId, errors

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

try:
    mongodb_uri = os.getenv('mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/')
    client = MongoClient("mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/")
    db = client['userDB']  # Replace with your database name
    users = db.users
    quizzes_collection = db.quizzes
    score_collection = db.score 
    
except Exception as e:
    print("Could not connect to MongoDB:", e)


#-------- controller for Goabal------------#
@app.route('/')
def main():
    return redirect('/login')  

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/eduSettings')
def settings_edu_page():
    return render_template('/eduSettings.html')

@app.route('/eduViewResult')
def Result_edu_page():
    return render_template('/eduViewResult.html')

@app.route('/studentViewResult')
def Result_student_page():
    return render_template('/studentViewResult.html')

@app.route('/studentSettings')
def settings_studen_page():
    return render_template('/studentSettings.html')
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data['username']
        phone = data['phone']
        email = data['email']
        password = data['password']
        role = data['role']  # New role field

        if not all([username, phone, email, password, role]):
            return jsonify({"message": "All fields are required"}), 400

        # remove this. it's okay to have duplicate usernames
        # if users.find_one({"username": username}):
        #     return jsonify({"message": "Username already exists"}), 400

        #this should be unique
        if users.find_one({"email": email}):
            return jsonify({"message": "Email already exists"}), 400

        # Generate a unique user ID
        user_id = str(uuid.uuid4())

        hashed_password = hashpw(password.encode('utf-8'), gensalt())

        new_user = {
            "user_id": user_id,
            "username": username,
            "phone": phone,
            "email": email,
            "passwordHash": hashed_password,
            "role": role
        }
        users.insert_one(new_user)
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        print(f"Registration failed: {str(e)}")  # Add this line to print the error
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500
    

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        user = users.find_one({"email": email})
        
        if not user or not checkpw(password.encode('utf-8'), user['passwordHash']):
            return jsonify({"message": "Invalid email or password"}), 401

        return jsonify({
            "message": "Login successful!",
            "role": user["role"],
            "user_id": user["user_id"],
            "username": user["username"],
            "phone": user["phone"]
        }), 200
    except Exception as e:
        print(f"Login failed: {str(e)}")  # Print the error for debugging
        return jsonify({"message": f"Login failed: {str(e)}"}), 500

@app.route('/api/updateProfile', methods=['POST'])
def update_profile():
    try:
        # Extract the data from the request
        data = request.get_json()
        user_id = data.get('user_id')  # Ensure you have user_id in the request to identify the user
        username = data.get('username')
        phone = data.get('phone')
        password = data.get('password')

        # Find the user by user_id
        user = users.find_one({"user_id": user_id})
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Prepare fields to update
        update_fields = {"username": username, "phone": phone}

        # Hash the password if provided and add to update fields
        if password:
            hashed_password = hashpw(password.encode('utf-8'), gensalt())
            update_fields["passwordHash"] = hashed_password

        # Update the user's information in the database
        users.update_one({"user_id": user_id}, {"$set": update_fields})

        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        print(f"Profile update failed: {str(e)}")  # Debugging info
        return jsonify({"message": f"Profile update failed: {str(e)}"}), 500
    

@app.route('/api/deleteUser/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Find the user by user_id to check the role
        user = users.find_one({"user_id": user_id})
        
        # Check if the user exists
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Delete the user account
        user_result = users.delete_one({"user_id": user_id})
        print("User deletion result:", user_result.deleted_count)

        # Handle additional deletions if the user is an educator
        if user["role"] == "educator":
            # Find all quizzes created by this educator
            quizzes = quizzes_collection.find({"user_id": user_id})
            quiz_ids = [str(quiz["_id"]) for quiz in quizzes]  # Convert quiz_ids to strings
            print("Quiz IDs as strings for deletion:", quiz_ids)

            # Delete all quizzes created by this educator
            quizzes_collection.delete_many({"user_id": user_id})

            # Delete all scores associated with the deleted quizzes
            score_result = score_collection.delete_many({"quiz_id": {"$in": quiz_ids}})
            print("Deleted scores count:", score_result.deleted_count)

            return jsonify({
                "message": "Educator account, associated quizzes, and scores deleted successfully",
                "deleted_quizzes_count": len(quiz_ids),
                "deleted_scores_count": score_result.deleted_count
            }), 200
        else:
            # For a student, only the user account is deleted
            return jsonify({"message": "Student account deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting user, quizzes, and scores: {str(e)}")
        return jsonify({"message": f"Error deleting account: {str(e)}"}), 500



#-------- Controller for Student------------#
@app.route('/studentDash')
def student_home_page(): 
    return render_template('studentDash.html')


@app.route('/studentViewQuiz')
def student_Play_Quiz():  
    return render_template('studentViewQuiz.html')

@app.route('/studentPlayQuiz', methods=['GET'])
def play_quiz():
    return render_template('studentPlayQuiz.html')


@app.route('/api/student_assigned_quizzes/<student_id>', methods=['GET'])
def get_student_assigned_quizzes(student_id):
    try:
        # Find quizzes where the student is assigned
        quizzes = db.quizzes.find(
            {"assigned": student_id},
            {"title": 1, "user_id": 1, "questions": 1, "assigned": 1} 
        )
        
       
        quiz_list = []
        for quiz in quizzes:
            quiz["_id"] = str(quiz["_id"])
            quiz_list.append(quiz)

        return jsonify(quiz_list), 200
    except Exception as e:
        print(f"Error fetching assigned quizzes: {e}")
        return jsonify({"error": "Failed to fetch assigned quizzes"}), 500


@app.route('/api/get_quiz/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    try:
        quiz = db.quizzes.find_one({"_id": ObjectId(quiz_id)}, {"title": 1, "questions": 1})
        if not quiz:
            return jsonify({"error": "Quiz not found"}), 404

        # Convert ObjectId to string for JSON serialization
        quiz["_id"] = str(quiz["_id"])
        for question in quiz["questions"]:
            question["id"] = str(question["id"])

        return jsonify(quiz)
    except Exception as e:
        print(f"Error retrieving quiz: {e}")
        return jsonify({"error": "Could not retrieve quiz data"}), 500
    

@app.route('/api/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        user_id = data.get("user_id")
        quiz_id = data.get("quiz_id")
        questions = data.get("questions")
        answers = data.get("answers")

        if not user_id or not quiz_id or not questions or not answers:
            return jsonify({"error": "Missing data for submission"}), 400

        # Retrieve the student's username
        user = db.users.find_one({"user_id": user_id}, {"username": 1})
        if not user:
            return jsonify({"error": "User not found"}), 404
        student_name = user.get("username")

        # Calculate score based on correct answers
        score = 0
        for question in questions:
            question_id = question["id"]
            correct_answer = question["correct_answer"]
            if answers.get(question_id) == correct_answer:
                score += 1

        # Prepare document to insert into the score collection
        submission = {
            "user_id": user_id,
            "username": student_name,   # Store the student's name
            "quiz_id": quiz_id,
            "questions": questions,
            "answers": answers,
            "score": score
        }

        # Insert the submission data into the score collection
        db.score.insert_one(submission)

        return jsonify({"message": "Quiz submitted successfully", "score": score}), 200
    except Exception as e:
        print(f"Error submitting quiz: {e}")
        return jsonify({"error": "Failed to submit quiz"}), 500

    
@app.route('/api/check_quiz_completion/<user_id>/<quiz_id>', methods=['GET'])
def check_quiz_completion(user_id, quiz_id):
    try:
        completed = db.score.find_one({"user_id": user_id, "quiz_id": quiz_id})
        return jsonify({"completed": bool(completed)}), 200
    except Exception as e:
        print(f"Error checking quiz completion: {e}")
        return jsonify({"error": "Failed to check quiz completion"}), 500

@app.route('/api/get_educator_name/<educator_id>', methods=['GET'])
def get_educator_name(educator_id):
    try:
        #print(f"Looking up educator with user_id: {educator_id}")  # for Debugging 
        educator = db.users.find_one({"user_id": educator_id}, {"username": 1})

        if educator:
            return jsonify({"name": educator["username"]}), 200
        else:
            #print("Educator not found in users collection")  # for Debugging
            return jsonify({"name": "Unknown"}), 404
    except Exception as e:
        print(f"Error fetching educator name: {e}")
        return jsonify({"error": "Failed to fetch educator name"}), 500





#-------- Controller for Edu------------#
@app.route('/eduDash')
def educator_home_page():  
    return render_template('eduDash.html')

@app.route('/eduCreateQuiz')
def educator_create_quiz():  
    return render_template('eduCreateQuiz.html')

@app.route('/eduManageQuiz')
def educator_manage_quiz():  
    return render_template('eduManageQuiz.html')

@app.route('/eduViewQuiz', methods=['GET', 'POST'])
def educator_view_quiz():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        quizzes = list(quizzes_collection.find({"user_id": user_id}))
        return render_template('partials/quiz_cards.html', quizzes=quizzes)
    return render_template('eduViewQuiz.html', quizzes=[])

@app.route('/deleteQuiz/<user_id>/<quiz_id>', methods=['DELETE'])
def delete_quiz(user_id, quiz_id):
    try:
        # Delete the quiz from quizzes collection
        quiz_result = db.quizzes.delete_one({"_id": ObjectId(quiz_id), "user_id": user_id})
        
        # Delete associated scores from score collection
        score_result = db.score.delete_many({"quiz_id": quiz_id})

        if quiz_result.deleted_count > 0:
            return jsonify({"success": True, "message": "Quiz and associated scores deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Quiz not found or could not be deleted"})
    except Exception as e:
        print(f"Error deleting quiz: {e}")
        return jsonify({"success": False, "message": "Failed to delete quiz and scores"}), 500

    
@app.route('/renameQuiz/<user_id>/<quiz_id>', methods=['PUT'])
def rename_quiz(user_id, quiz_id):
    data = request.get_json()
    new_title = data.get("new_title")

    if not new_title:
        return jsonify({"success": False, "message": "New title is required"}), 400

    try:
        result = quizzes_collection.update_one(
            {"_id": ObjectId(quiz_id), "user_id": user_id},
            {"$set": {"title": new_title}}
        )
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "Quiz renamed successfully."}), 200
        else:
            return jsonify({"success": False, "message": "Quiz not found or access denied."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/eduAssignQuiz')
def edu_assign_quiz():
    return render_template('eduAssignQuiz.html')

@app.route('/eduViewScore')
def edu_View_Score():
    return render_template('eduViewScore.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    students = users.find({"role": "student"})
    student_list = [{"user_id": student["user_id"], "username": student["username"], "email": student["email"]} for student in students]
    return jsonify(student_list)

@app.route('/api/assign_quiz', methods=['POST'])
def assign_quiz():
    try:
        data = request.json
        quiz_id = data.get("quiz_id")
        assigned = data.get("assigned")

        # Validate the input data
        if not quiz_id or not assigned:
            return jsonify({"error": "Quiz ID and assigned students are required"}), 400

        # Convert quiz_id to ObjectId 
        quiz_id = ObjectId(quiz_id)

        # Update the quiz document in MongoDB
        result = quizzes_collection.update_one(
            {"_id": quiz_id},
            {"$set": {"assigned": assigned}}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Quiz assigned successfully!"}), 200
        else:
            return jsonify({"error": "Quiz not found"}), 404

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500

@app.route('/api/assigned_students/<quiz_id>', methods=['GET'])
def get_assigned_students(quiz_id):
    try:
        # Convert quiz_id to ObjectId for MongoDB lookup
        try:
            quiz_id = ObjectId(quiz_id)
        except errors.InvalidId as e:
            print(f"Invalid ObjectId format for quiz_id: {quiz_id}, error: {e}")
            return jsonify({"error": "Invalid quiz ID format"}), 400

        # Query the quizzes_collection (make sure this matches your collection name)
        quiz = quizzes_collection.find_one({"_id": quiz_id}, {"assigned": 1})
        
        if not quiz:
            print(f"No quiz found with ID: {quiz_id}")
            return jsonify({"error": "Quiz not found"}), 404

        assigned_student_ids = quiz.get("assigned", [])
        #print("Assigned Student IDs:", assigned_student_ids)  # for Debugging 

        # Retrieve details for each assigned student by their user_id
        assigned_students = list(users.find(
            {"user_id": {"$in": assigned_student_ids}},
            {"user_id": 1, "username": 1, "email": 1}  # Only fetching necessary fields
        ))

        # Convert ObjectIds in results to strings
        for student in assigned_students:
            student["_id"] = str(student["_id"])
            student["user_id"] = str(student["user_id"])

        print("Assigned Students Data:", assigned_students)  # Debugging line

        return jsonify(assigned_students)
    
    except Exception as e:
        print(f"Server error while retrieving assigned students: {e}")
        return jsonify({"error": f"Could not retrieve assigned students: {str(e)}"}), 500

@app.route('/api/remove_assigned_students', methods=['POST'])
def remove_assigned_students():
    try:
        data = request.json
        quiz_id = data.get("quiz_id")
        students_to_remove = data.get("assigned")

        # Validate inputs
        if not quiz_id or not students_to_remove:
            return jsonify({"error": "Quiz ID and students to remove are required"}), 400

        quiz_id = ObjectId(quiz_id)

        # Update the assigned list in the quiz document by pulling specified students
        result = quizzes_collection.update_one(
            {"_id": quiz_id},
            {"$pull": {"assigned": {"$in": students_to_remove}}}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Selected students removed successfully!"}), 200
        else:
            return jsonify({"error": "Failed to update assigned students"}), 500

    except Exception as e:
        print(f"Error while removing assigned students: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api/get_quiz_scores/<quiz_id>', methods=['GET'])
def get_quiz_scores(quiz_id):
    try:
        # Fetch scores associated with the given quiz_id
        scores = db.score.find({"quiz_id": quiz_id})
        
        # Prepare the response data
        score_list = []
        for score in scores:
            score_data = {
                "_id": str(score["_id"]),
                "user_id": score["user_id"],
                "username": score["username"],  # Include username
                "score": score["score"],
                "questions": score["questions"],
                "answers": score["answers"]
            }
            score_list.append(score_data)

        return jsonify(score_list), 200
    except Exception as e:
        print(f"Error fetching scores: {e}")
        return jsonify({"error": "Failed to fetch scores"}), 500



@app.route('/api/delete_score/<score_id>', methods=['DELETE'])
def delete_score(score_id):
    try:
        result = db.score.delete_one({"_id": ObjectId(score_id)})
        if result.deleted_count == 1:
            return jsonify({"message": "Score deleted successfully"}), 200
        else:
            return jsonify({"error": "Score not found"}), 404
    except Exception as e:
        print(f"Error deleting score: {e}")
        return jsonify({"error": "Failed to delete score"}), 500





# API endpoint to fetch quizzes
@app.route('/api/quizzes', methods=['GET', 'POST'])
def quizzes():
    if request.method == 'GET':
        try:
            category = request.args.get('category')
            difficulty = request.args.get('difficulty')
            q_type = request.args.get('type')
            amount = request.args.get('amount', default=10, type=int)

            params = {
                'amount': amount
            }
            
            # Include 'category' if it's not 'any' or empty
            if category and category.lower() != 'any':
                params['category'] = category

            # Include 'difficulty' if it's not 'any' or empty
            if difficulty and difficulty.lower() != 'any':
                params['difficulty'] = difficulty.lower()

            # Include 'type' if it's not 'any' or empty
            if q_type and q_type.lower() != 'any':
                params['type'] = q_type.lower()

            # Make request to Open Trivia API
            response = requests.get('https://opentdb.com/api.php', params=params)
            response.raise_for_status()
            quizzes = response.json().get('results', [])

            return jsonify({"quizzes": quizzes}), 200
        except Exception as e:
            return jsonify({"message": f"Failed to fetch quizzes: {str(e)}"}), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()
            quiz_title = data.get('title')
            questions = data.get('questions')
            user_id = data.get('user_id')  # Assume user_id is sent in the request

            if not quiz_title or not questions or not user_id:
                return jsonify({"message": "Title, questions, and user ID are required"}), 400

            # Assign unique IDs to each question if not present
            for question in questions:
                if 'id' not in question:
                    question['id'] = str(ObjectId())

            new_quiz = {
                "user_id": user_id,  # Use the user's unique ID as the quiz ID
                "title": quiz_title,
                "questions": questions
            }
            quizzes_collection.insert_one(new_quiz)
            return jsonify({"message": "Quiz created successfully", "user_id": user_id}), 201
        except Exception as e:
            return jsonify({"message": f"Failed to create quiz: {str(e)}"}), 500

# Get available quizzes
@app.route('/api/quizzes/available', methods=['GET'])
def get_available_quizzes():
    try:
        quizzes = quizzes_collection.find({}, {'_id': 1, 'title': 1})
        quiz_list = [{'id': str(q['_id']), 'title': q['title']} for q in quizzes]
        return jsonify({'quizzes': quiz_list}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to fetch available quizzes: {str(e)}"}), 500

# Categories endpoint
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        # Default categories for the quiz application
        categories = [
            {'id': 9, 'name': 'General Knowledge'},
            {'id': 18, 'name': 'Computer'},
            {'id': 19, 'name': 'Mathematics'},
            {'id': 23, 'name': 'History'},
            {'id': 17, 'name': 'Science & Nature'},
            {'id': 27, 'name': 'Animals'}
        ]
        return jsonify({"categories": categories}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to fetch categories: {str(e)}"}), 500

@app.route('/api/get_student_answers/<user_id>', defaults={'quiz_id': None}, methods=['GET'])
@app.route('/api/get_student_answers/<user_id>/<quiz_id>', methods=['GET'])
def get_student_answers(user_id, quiz_id):
    try:
        if quiz_id:
            score = db.score.find_one({"user_id": user_id, "quiz_id": quiz_id})
            if not score:
                return jsonify({"error": "Score not found for this student and quiz"}), 404

            # Fetch the quiz title from the quizzes collection
            quiz = db.quizzes.find_one({"_id": ObjectId(quiz_id)}, {"title": 1})
            if not quiz:
                return jsonify({"error": "Quiz not found"}), 404

            # Convert ObjectId to string for JSON serialization
            score["_id"] = str(score["_id"])
            score["quiz_title"] = quiz.get("title", "Unknown Quiz Title")  # Add quiz title to the response

            return jsonify(score), 200
        else:
            scores = list(db.score.find({"user_id": user_id}))
            if not scores:
                return jsonify({"error": "No scores found for this student"}), 404

            # Fetch quiz titles for each score
            for score in scores:
                score["_id"] = str(score["_id"])
                quiz_id = score.get("quiz_id")
                if quiz_id:
                    quiz = db.quizzes.find_one({"_id": ObjectId(quiz_id)}, {"title": 1})
                    score["quiz_title"] = quiz.get("title", "Unknown Quiz Title") if quiz else "Unknown Quiz Title"

            return jsonify(scores), 200

    except Exception as e:
        print(f"Error fetching student answers: {e}")
        return jsonify({"error": "Failed to fetch student answers"}), 500
@app.context_processor
def inject_search_edu_pages():
    # Filter pages to only include those with links starting with '/edu'
    edu_pages = [
        {"title": "Educator Settings", "link": "/eduSettings"},
        {"title": "Educator View Result", "link": "/eduViewResult"},
        {"title": "Educator Dashboard", "link": "/eduDash"},
        {"title": "Create Quiz", "link": "/eduCreateQuiz"},
        {"title": "Manage Quiz", "link": "/eduManageQuiz"},
        {"title": "View Quiz", "link": "/eduViewQuiz"},
        {"title": "Assign Quiz", "link": "/eduAssignQuiz"},    ]
    return dict(edupages=edu_pages)
@app.context_processor
def inject_search_student_pages():
    # Filter pages to only include those with links starting with '/edu'
    student_pages = [
        {"title": "Student Settings", "link": "/studentSettings"},
        {"title": "Student View Result", "link": "/studentViewResult"},
        {"title": "Student Dashboard", "link": "/studentDash"},
        {"title": "Play Quiz", "link": "/studentPlayQuiz"},
        {"title": "View Quiz", "link": "/studentViewQuiz"},]
    return dict(studentPages=student_pages)



if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5001)))