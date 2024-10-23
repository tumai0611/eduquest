from flask import Flask, request, jsonify, redirect
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from flask_cors import CORS
import os

app = Flask(__name__)

# Set up CORS to allow requests from your Netlify site
CORS(app, resources={r"/api/*": {"origins": "*"}})
try:
    mongodb_uri = os.getenv('mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/')
    client = MongoClient("mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/")
    db = client['userDB']  # Replace with your database name
    users = db.users
except Exception as e:
    print("Could not connect to MongoDB:", e)
""" mongo_uri = os.getenv("mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/")  # This should be set to your Atlas URI
client = MongoClient(os.getenv('mongodb+srv://elysia:swe@ct2004-swe.3a2gl.mongodb.net/'))
db = client.userDB
users = db.users """

@app.route('/')
def home():
    # Redirect to your Netlify site
    return redirect("https://astonishing-travesseiro-d6393a.netlify.app/", code=302)


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    phone = data['phone']
    email = data['email']
    password = data['password']

    if not all([username, phone, email, password]):
        return jsonify({"message": "All fields are required"}), 400

    # Check if the username already exists
    if users.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    # Check if the email already exists
    if users.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    # Check if the phone number already exists
    if users.find_one({"phone": phone}):
        return jsonify({"message": "Phone number already exists"}), 400

    hashed_password = hashpw(password.encode('utf-8'), gensalt())
    
    new_user = {
        "username": username,
        "phone": phone,
        "email": email,
        "passwordHash": hashed_password,
    }
    print("Received data:", data)  # Log the received data
    users.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    print("Login attempt:", data)  # Log the incoming data
    username = data['username']
    password = data['password']

    user = users.find_one({"username": username})
    if not user:
        print("User not found:", username)  # Log if user doesn't exist
        return jsonify({"message": "User does not exist"}), 404

    if user and checkpw(password.encode('utf-8'), user['passwordHash']):
        print("Login successful for:", username)  # Log successful login
        return jsonify({"message": "Login successful!"}), 200
    else:
        print("Invalid credentials for:", username)  # Log invalid login attempt
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/login', methods=['OPTIONS'])
def login_options():
    return jsonify({'status': 'ok'}), 200



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

