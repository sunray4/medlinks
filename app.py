from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from pymongo import MongoClient
import uuid
import string
import secrets

# import db.factory
import os
import configparser
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))
app.config['MONGO_URI'] = config['PROD']['DB_URI']
app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']
mongo = PyMongo(app)

client = MongoClient(app.config['MONGO_URI'])
users = client.get_database('medlinks').get_collection('users')

def generate_patient_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(12))
    
    return password

@app.route('/register')
def render_register():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if users.find_one({'email': username}):
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    users.insert_one({'email': username, 'password': hashed_password})

    return jsonify({'message': 'User registered successfully', 'redirect': '/'}), 201


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
    if not email or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = users.find_one({'email': email})
    
    if user and check_password_hash(user['password'], password):
        session['email'] = email
        return jsonify({'message': 'Logged in successfully', 'redirect': '/'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# User Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Protected Route Example
@app.route('/profile', methods=['GET'])
def profile():
    if 'email' in session:
        return jsonify({'message': f"Welcome {session['email']}"}), 200
    else:
        return jsonify({'error': 'Unauthorized'}), 401

@app.route("/", methods=['GET', 'POST'])
def home():
    if "email" in session:
        if request.method == 'GET':
            return render_template("d_patient_list.html")
        elif request.method == 'POST':
            patient_name = request.form['patient_fullname']
            patient_dob = request.form['patient_dob']
            patient_service_id = request.form['patient_service_id']
            patient_address = request.form['patient_address']
            patient_email = request.form['patient_email']
            patient_phone_num = request.form['patient_phone_num']
            patient_height = request.form['patient_height']
            patient_weight = request.form['patient_weight']
            patient_allergies = request.form['patient_allergies']
            
            patient_id = str(uuid.uuid4())
            type = 'patient'
            
            users.insert_ones({'user_id': patient_id, 'fullname': patient_name, 'email': patient_email, 'password': generate_password_hash(generate_patient_password()), 'type': 'patient', })
            
            return render_template("d_patient_list.html")
    else:
        return redirect(url_for('login'))

@app.route('/new-logs/<doctor_id>')
def new_logs(doctor_id):
    return render_template("d_new_logs.html")


@app.route('/redirect-doctor-to-patient-log/<doctor_id>', methods=['POST'])
def redirect_doctor_to_patient_log(doctor_id, patient_id, entry_id):
    return render_template("d_patient_med_log.html", patient_id=patient_id, entry_id=entry_id)

if __name__ == "__main__":
    # app = db.factory.create_app()
    # app.config['DEBUG'] = True
    # app.config['MONGO_URI'] = config['PROD']['DB_URI']

    app.run(debug=True)

