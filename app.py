from flask import Flask, request, jsonify
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from flask_cors import CORS

import os
from pymongo import MongoClient




app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins, adjust as needed

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.userDB
users = db.users

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the User Registration API!"}), 200


@app.route('/register', methods=['POST'])
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

    users.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = users.find_one({"username": username})
    if not user:
        return jsonify({"message": "User does not exist"}), 404

    if user and checkpw(password.encode('utf-8'), user['passwordHash']):
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

if __name__ == '__main__':
    app.run(debug=True)
