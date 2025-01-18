from flask import Flask, render_template, request, jsonify, session
from flask_pymongo import PyMongo
from pymongo import MongoClient

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
users = mongo.db.users


@app.route('/register')
def render_register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    mongo.db.users.insert_one({'username': username, 'password': hashed_password})

    return jsonify({'message': 'User registered successfully', 'redirect': '/'}), 201


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = mongo.db.users.find_one({'username': username})
    
    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return jsonify({'message': 'Logged in successfully', 'redirect': '/'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# User Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Protected Route Example
@app.route('/profile', methods=['GET'])
def profile():
    if 'username' in session:
        return jsonify({'message': f"Welcome {session['username']}"}), 200
    else:
        return jsonify({'error': 'Unauthorized'}), 401

@app.route("/", methods=['GET', 'POST'])
def home():
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
        
        return render_template("d_patient_list.html")

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

