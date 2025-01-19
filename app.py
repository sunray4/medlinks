from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import yagmail
import uuid
import string
import secrets

# import db.factory
import os
import configparser
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

yag = yagmail.SMTP('medlinks.app@gmail.com', 'uqqz awlm wrqo vbyy')

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))
app.config['MONGO_URI'] = config['PROD']['DB_URI']
app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']
mongo = PyMongo(app)

client = MongoClient(app.config['MONGO_URI'], server_api=ServerApi('1'))
users = client.get_database('medlinks').get_collection('users')
medlogs = client.get_database('medlinks').get_collection('medlogs')

def generate_patient_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(12))
    
    return password

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['first-name']
        lastname = request.form['last-name']
        fullname = firstname + ' ' + lastname
        email = request.form['email']
        password = request.form['password']
        doctor_id = str(uuid.uuid4())
        type = 'doctor'
        
        if not email or not password:
            flash('Email and password are required.', 'error')

        if users.find_one({'email': email}):
            flash('Email already exists.', 'error')
        
        hashed_password = generate_password_hash(password)
        users.insert_one({'user_id': doctor_id, 'email': email, 'password': hashed_password, 'fullname': fullname, 'unread_message_list': [], 'patient_list': [], 'events': [], 'type': type})
        session['doctor_id'] = doctor_id
        
        flash('Successfully created account, please log in.', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
        if not email or not password:
            return jsonify({'error': 'email and password are required'}), 400
        
        user = users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['doctor_id'] = user['user_id']
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please try again', 'error')
            
    return render_template('login.html')

# User Logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('email', None)
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login'))

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
            patient_password = generate_patient_password()
            
            users.insert_one({'user_id': patient_id, 'fullname': patient_name, 'email': patient_email, 'password': generate_password_hash(patient_password), 'type': type, 'doctor_id': session['doctor_id'], 'dob': patient_dob, 'bc_service_card_id': patient_service_id, 'address': patient_address, 'phone_number': patient_phone_num, 'height': patient_height, 'weight': patient_weight, 'allergies': patient_allergies})
            medlogs.insert_one({'medlog_id': str(uuid.uuid4()), 'patient_id': patient_id, 'entries': [], 'doctor_id': session['doctor_id']})
            
            # send patient email w/ login info (email + password)

            email_content = '''
            Hi {patient_name}!
            
            Welcome to Medlinks! Your doctor has created an account for you. Here are your login credentials:
            Email: {patient_email}
            Password: {patient_password}
            
            Best wishes,
            Your friends at Medlinks
            '''
            
            yag.send(patient_email, 'Medlinks', email_content)
            
            return render_template("d_patient_list.html")
    else:
        return redirect(url_for('login'))

@app.route('/d-new-logs/<doctor_id>')
def new_logs(doctor_id):
    return render_template("d_new_logs.html")

@app.route('/d-patient-med-log/')
def patient_med_log():
    return render_template("d_patient_med_log.html")

@app.route('/d-patient-list/')
def patient_list():
    return render_template("d_patient_list.html")

@app.route('/redirect-doctor-to-patient-log/<doctor_id>', methods=['POST'])
def redirect_doctor_to_patient_log(doctor_id, patient_id, entry_id):
    return render_template("d_patient_med_log.html", patient_id=patient_id, entry_id=entry_id)

@app.route('/list_patients', methods=['GET'])
def get_patients():
    users_list = users.find()
    email_list = []
    name_list = []
    
    for user in users_list:
        email_list.append(user['email'])
        name_list.append(user['fullname'])

    return jsonify({'emails': email_list, 'names': name_list}), 200
    

if __name__ == "__main__":
    # app = db.factory.create_app()
    # app.config['DEBUG'] = True
    # app.config['MONGO_URI'] = config['PROD']['DB_URI']

    app.run(debug=True, port=5500)