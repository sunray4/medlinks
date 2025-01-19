from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import yagmail
import uuid
import string
import secrets
import chatgpt
from flask_socketio import SocketIO, emit

# import db.factory
import os
import configparser
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

yag = yagmail.SMTP('medlinks.app@gmail.com', 'uqqz awlm wrqo vbyy')

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))
app.config['MONGO_URI'] = config['PROD']['DB_URI']
app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']
mongo = PyMongo(app)

client = MongoClient(app.config['MONGO_URI'], server_api=ServerApi('1'))
users = client.get_database('medlinks').get_collection('users')
medlogs = client.get_database('medlinks').get_collection('medlogs')
events = client.get_database('medlinks').get_collection('events')

bot = None

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
        session['type'] = type
        
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
            session['type'] = user['type']
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
        user = users.find_one({'email': session['email']})
        session['type'] = user['type']
        if request.method == 'GET':
            if session['type'] == 'doctor':
                return render_template("d_patient_list.html")
            elif session['type'] == 'patient':
                return render_template("p_med_log.html")
        elif request.method == 'POST':
            patient_name = request.form['patient_fullname']
            patient_dob = request.form['patient_dob']
            patient_sex = request.form['patient_sex']
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
            
            doctor = users.find_one({'user_id': session['doctor_id']})
            doctor['patient_list'].append(patient_id)
            doctor_name = doctor['fullname']
            users.update_one({'user_id': session['doctor_id']}, {'$set': {'patient_list': doctor['patient_list']}})
            
            medlog_id = str(uuid.uuid4())
            users.insert_one({'user_id': patient_id, 'medlog_id': medlog_id, 'fullname': patient_name, 'email': patient_email, 'patient_sex': patient_sex, 'password': generate_password_hash(patient_password), 'type': type, 'doctor_id': session['doctor_id'], 'dob': patient_dob, 'bc_service_card_id': patient_service_id, 'address': patient_address, 'phone_number': patient_phone_num, 'height': patient_height, 'weight': patient_weight, 'allergies': patient_allergies})
            medlogs.insert_one({'medlog_id': medlog_id, 'patient_id': patient_id, 'entries': [], 'doctor_id': session['doctor_id']})
            
            
            # send patient email w/ login info (email + password)
            email_content = f'''
            Hi {patient_name}!
            
            Welcome to Medlinks! Your doctor, {doctor_name} has created an account for you. You can access Medlinks with these credentials:
            Email: {patient_email}
            Password: {patient_password}
            
            Best wishes,
            Your friends at Medlinks
            '''
            
            yag.send(patient_email, 'Medlinks', email_content)
            
            return render_template("d_patient_list.html")
    else:
        return redirect(url_for('login'))
    
@app.route('/p-post/', methods=['GET', 'POST'])
def post():
    global bot
    bot = chatgpt.SymptomAnalyzer()
    user = users.find_one({'email': session['email']})
    sex = user['patient_sex']
    dob = user['dob']
    dob_date = datetime.strptime(dob, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    bot.get_user_inputs(age, sex)
    return render_template('p_post.html')

@socketio.on('user_message')
def handle_user_message(message):
    global bot
    try:
        response = bot.add_user_response(message)
        
        if isinstance(response, (dict, list)):
            emit('bot_response', response, broadcast=True)
        else:
            emit('bot_response', str(response), broadcast=True)
    except Exception as e:
        emit('bot_response', f"An error occurred: {str(e)}", broadcast=True)

@app.route('/d-new-logs/')
def new_logs():
    if session['type'] == 'doctor':
        return render_template("d_new_logs.html")
    elif session['type'] == 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

# @app.route('/d-patient-med-log/')
# def patient_med_log():
#     # print("running patient med log")
#     return render_template("d_patient_med_log.html")

@app.route('/d-patient-list/')
def patient_list():
    patients = {}
    return render_template("d_patient_list.html", patients=patients)

@app.route('/redirect-doctor-to-patient-log/<doctor_id>', methods=['POST'])
def redirect_doctor_to_patient_log(doctor_id, patient_id, entry_id):
    return render_template(" .html", patient_id=patient_id, entry_id=entry_id)

@app.route('/list_patients', methods=['GET'])
def get_patients():
    users_list = users.find()
    email_list = []
    name_list = []
    dob_list = []
    
    for user in users_list:
        if user['type'] == 'patient':
            email_list.append(user['email'])
            name_list.append(user['fullname'])
            dob_list.append(user['dob'])

    return jsonify({'emails': email_list, 'names': name_list, 'dob': dob_list }), 200

@app.route('/d_patient_med_log/<email>', methods=['GET', 'POST'])
def patient_med_log(email):
    if request.method == 'GET':
        patient = users.find_one({'email': email})
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
    elif request.method == 'POST':
        rows = request.args.get('rows')
        date = request.form.get('entry_date', None)
        mode = request.form.get('entry_mode', None)
        personal_notes = request.form.get('entry_personal_notes', None)
        doctor_diagnosis = request.form.get('entry_doctor_diagnosis', None)
        med_name = request.form.get('med_name', None)
        med_dosage = request.form.get('med_dosage', None)
        med_instructions = request.form.get('med_instructions', None)
        inperson_meeting = request.form.get('inperson_meeting', None)
        
        if not mode:
            return jsonify({'error': 'Entry mode is required'}), 400
        
        print(rows)
        
        patient = users.find_one({'email': email})
        medlog_id = patient['medlog_id']

        medlog = medlogs.find_one({'medlog_id': medlog_id})
        medlog['entries'].append({'date': date, 'mode': mode, 'personal_notes': personal_notes, 'doctor_diagnosis': doctor_diagnosis, 'med_name': med_name, 'med_dosage': med_dosage, 'med_instructions': med_instructions, 'inperson_meeting': inperson_meeting})
        medlogs.update_one({'medlog_id': medlog_id}, {'$set': {'entries': medlog['entries']}})

    
    return render_template("d_patient_med_log.html", patient=patient)

events = [
    {
        'todo': 'Appt. with Josh',
        'date': '2025-01-14',
        'time': '12:00',
        'type': 'Online', 
    },  
    {
        'todo': 'Appt. with Sarah',
        'date': '2025-01-14',
        'time': '13:00',
        'type': 'In person' 
    },
    
]

@app.route('/create_event', methods=['POST'])
def create_event():
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        if "email" in session:
            if session['type'] == 'patient':
                user = users.find_one({'email': session['email']})
                session_key = user['user_id']
                doctor_id = user['doctor_id']
                events.insert_one({'doctor_id': doctor_id, 'patient_id': session_key, 'date': date, 'time': time})
                return render_template("p_calendar.html")
        else: 
            return redirect(url_for('login'))
                

@app.route('/display_events', methods=['GET'])
def get_events():
    if "email" in session:
        if session['type'] == 'doctor':
            user = users.find_one({'email': session['email']})
            session_key = user['user_id']
            events_session = events.find({ "doctor_id": session_key})
            return jsonify({'events': events_session}), 200
        elif session['type'] == 'patient':
            user = users.find_one({'email': session['email']})
            session_key = user['user_id']
            events_session = events.find({ "patient_id": session_key})
            return jsonify({'events': events_session}), 200
    else:
        return redirect(url_for('login'))
        


@app.route('/d_calendar')
def d_calendar():
    return render_template('d_calendar.html', events = events)

@app.route('/p_calendar')
def p_calendar():
    return render_template('p_calendar.html', events = events)

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    emit('message', data, broadcast=True)

if __name__ == "__main__":
    # app = db.factory.create_app()
    # app.config['DEBUG'] = True
    # app.config['MONGO_URI'] = config['PROD']['DB_URI']

    socketio.run(app, debug=True, port=5500)