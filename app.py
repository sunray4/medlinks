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
        session['user_id'] = doctor_id
        
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
            session['user_id'] = user['user_id']
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
        try:
            if not user['type']: session['type'] = 'doctor'
            else: session['type'] = user['type']
        except:
            session['type'] = 'doctor'
        if request.method == 'GET':
            if session['type'] == 'doctor':
                patients = get_patients()
                return render_template("d_patient_list.html", patients=patients)
            elif session['type'] == 'patient':
                patient = users.find_one({'email': session['email']})
                return render_template("p_med_log.html", patient=patient, medlogs=medlogs.find_one({'medlog_id': patient['medlog_id']})['entries'])
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
            patients = get_patients()
            return render_template("d_patient_list.html", patients=patients)
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

@socketio.on('final_data')
def handle_final_data(data):
    print(data)
    user = users.find_one({'email': session['email']})
    today_date = datetime.today().strftime('%Y-%m-%d')

    patient_notes = data.replace('\n', '<br>')
    personal_notes = ''
    doctor_diagnosis = ''
    medicine = []
    mode = 'Text'

    med_name = ''
    med_dosage = ''
    med_instructions = ''
    medicine.append({'med_name': med_name, 'med_dosage': med_dosage, 'med_instructions': med_instructions})
    
    patient = users.find_one({'email': session['email']})
    medlog_id = patient['medlog_id']

    medlog = medlogs.find_one({'medlog_id': medlog_id})
    medlog['entries'].append({'date': today_date, 'mode': mode, 'patient_notes': patient_notes, 'personal_notes': personal_notes, 'doctor_diagnosis': doctor_diagnosis, 'medicines': medicine, 'inperson_meeting': '', 'is_viewed': False})
    medlogs.update_one({'medlog_id': medlog_id}, {'$set': {'entries': medlog['entries']}})

    emit('final_data', 'return_medlog')

@app.route('/list-new-logs', methods=['GET'])
def get_new_logs():
    user = users.find_one({'email': session['email']})
    medlog = medlogs.find({'doctor_id': user['user_id']})
    name_list = []
    email_list = []
    date_sent = []

    for log in medlog:
        for entry in log['entries']:
            print(entry)
            if entry['is_viewed'] == False:
                patient_id = log['patient_id']
                patient = users.find_one({'user_id': patient_id})

                name_list.append(patient['fullname'])
                email_list.append(patient['email'])
                date_sent.append(entry['date'])

        
    return jsonify({'emails': email_list, 'names': name_list, 'dates': date_sent}), 200

@app.route('/d-new-logs/')
def new_logs():
    if session['type'] == 'doctor':
        user = users.find_one({'email': session['email']})

        medlog = medlogs.find({'doctor_id': user['user_id']})

        return render_template("d_new_logs.html", doctor_id=user['user_id'], medlogs=medlog)
    elif session['type'] == 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

# @app.route('/d-patient-med-log/')
# def patient_med_log():
#     # print("running patient med log")
#     return render_template("d_patient_med_log.html")

@app.route('/d-patient-list/')
def patient_list():
    patients = get_patients()
    return render_template("d_patient_list.html", patients=patients)

@app.route('/p_med_log/')
def patient_med_logs():
    if session['type'] == 'patient':
        patient = users.find_one({'email': session['email']})
        return render_template("p_med_log.html", patient=patient, medlogs=medlogs.find_one({'medlog_id': patient['medlog_id']})['entries'])
    else:
        return redirect(url_for('home'))

# @app.route('/redirect-doctor-to-patient-log/<doctor_id>', methods=['POST'])
# def redirect_doctor_to_patient_log(doctor_id, patient_id, entry_id):
#     return render_template("d_patient_med_log.html", patient_id=patient_id, entry_id=entry_id)

@app.route('/list_patients', methods=['GET'])
def get_patients():
    patient_list = users.find_one({'user_id': session['doctor_id']})['patient_list']
    users_list = users.find({'user_id': {'$in': patient_list}})
    email_list = []
    name_list = []
    dob_list = []
    
    for user in users_list:
        if user['type'] == 'patient':
            email_list.append(user['email'])
            name_list.append(user['fullname'])
            dob_list.append(user['dob'])

    return jsonify({'emails': email_list, 'names': name_list, 'dob': dob_list }), 200

@socketio.on('d_patient_med_log_mark_read')
def medlog_mark_red(data):
    medlog = medlogs.find_one({'doctor_id': data['user_id']})
    for entry in medlog['entries']:
        if entry['date'] == data['date']:
            entry['is_viewed'] = True
            index = medlog['entries'].index(entry)
            medlog['entries'][index] = entry
            medlogs.update_one({'doctor_id': data['user_id']}, {'$set': {'entries': medlog['entries']}})
            pass

@app.route('/d_patient_med_log/<email>', methods=['GET', 'POST'])
def patient_med_log(email):
    if request.method == 'GET':
        patient = users.find_one({'email': email})
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
    elif request.method == 'POST':
        date = request.form.get('entry_date', None)
        mode = request.form.get('entry_mode', None)
        patient_notes = request.form.get('entry_patient_notes', None)
        personal_notes = request.form.get('entry_personal_notes', None)
        doctor_diagnosis = request.form.get('entry_doctor_diagnosis', None)
        medicine = []
        inperson_meeting = request.form.get('inperson_meeting', None)
        isViewed = True

        med_name = request.form.get('med_name_1', None)
        med_dosage = request.form.get('med_dosage_1', None)
        med_instructions = request.form.get('med_instructions_1', None)
        medicine.append({'med_name': med_name, 'med_dosage': med_dosage, 'med_instructions': med_instructions})
        
        if not mode:
            return jsonify({'error': 'Entry mode is required'}), 400
        
        patient = users.find_one({'email': email})
        medlog_id = patient['medlog_id']

        medlog = medlogs.find_one({'medlog_id': medlog_id})
        medlog['entries'].append({'date': date, 'mode': mode, 'patient_notes': patient_notes, 'personal_notes': personal_notes, 'doctor_diagnosis': doctor_diagnosis, 'medicines': medicine, 'inperson_meeting': inperson_meeting, 'is_viewed': isViewed})
        medlogs.update_one({'medlog_id': medlog_id}, {'$set': {'entries': medlog['entries']}})

    return render_template("d_patient_med_log.html", patient=patient, medlogs=medlogs.find_one({'medlog_id': patient['medlog_id']})['entries'])

events_dict = [
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

@app.route('/getdocname', methods=['GET'])
def return_docname():
    if 'email' in session:
        if session['type'] == 'patient':
            user = users.find_one({'email': session['email']})
            doctor_id = user['doctor_id']
            doctor_name = users.find_one({'user_id': doctor_id})['fullname']

            return jsonify({'name': doctor_name}), 200

@app.route('/create_event', methods=['POST'])
def create_event():
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        appt_type = request.form['type']
        if "email" in session:
            if session['type'] == 'patient':
                user = users.find_one({'email': session['email']})
                session_key = user['user_id']
                doctor_id = user['doctor_id']
                event_id = str(uuid.uuid4())
                patient_name = user['fullname']
                todo = 'Appt. w/ ' + patient_name
                events.insert_one({'event_id': event_id, 'todo':todo, 'type':appt_type, 'doctor_id': doctor_id, 'patient_id': session_key, 'date': date, 'time': time})
                user = users.find_one({'email': session['email']})
                session_key = user['user_id']
                print(session_key)
                events_session = events.find({ "patient_id": session_key})
                patient_email = user['email']
                doctor_name = users.find_one({'user_id': doctor_id})['fullname']
                doctor_email = users.find_one({'user_id': doctor_id})['email']
                
                patient_event_email_content = f'''
                Hi {patient_name}!

                Your appointment has been booked for {date} at {time}.

                Best wishes,
                Your friends at Medlinks
                '''

                yag.send(patient_email, 'Medlinks Appointment', patient_event_email_content)

                doctor_event_email_content = f'''
                Hi {doctor_name},

                An appointment with {patient_name} has been booked for {date} at {time}.

                Best regards,
                Medlinks
                '''

                yag.send(doctor_email, 'Medlinks Appointment', doctor_event_email_content)

                return render_template("p_calendar.html", events = events_session)
        else: 
            return redirect(url_for('login'))
                

@app.route('/d_calendar')
def d_calendar():
    if "email" in session:
        if session['type'] == 'patient':
            return jsonify({'error': 'Unauthorized'}), 401
        elif session['type'] == 'doctor':
            user = users.find_one({'email': session['email']})
            session_key = user['user_id']
            events_session = events.find({ "doctor_id": session_key})
            
            return render_template('d_calendar.html', events = events_session)
    else:
        return redirect(url_for('login'))
    
@app.route('/d_delete_from_doctor/<email>', methods=['GET', 'POST'])
def d_delete_from_doctor(email):
    user = users.find_one({'email': email})
    doctor = users.find_one({'user_id': session['doctor_id']})
    doctor['patient_list'].remove(user['user_id'])
    users.update_one({'user_id': session['doctor_id']}, {'$set': {'patient_list': doctor['patient_list']}})
    
    return redirect(url_for('home'))

@app.route('/p_calendar')
def p_calendar():
    if "email" in session:
        if session['type'] == 'doctor':
            return jsonify({'error': 'Unauthorized'}), 401
        elif session['type'] == 'patient':
            user = users.find_one({'email': session['email']})
            session_key = user['user_id']
            events_session = events.find({ "patient_id": session_key})
            
            return render_template('p_calendar.html', events = events_session)
    else:
        return redirect(url_for('login'))

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    emit('message', data) #, broadcast=True)

if __name__ == "__main__":
    # app = db.factory.create_app()
    # app.config['DEBUG'] = True
    # app.config['MONGO_URI'] = config['PROD']['DB_URI']

    socketio.run(app, debug=True, port=5500)