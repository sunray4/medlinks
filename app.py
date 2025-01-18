from flask import Flask, render_template, request, jsonify

import db.factory
import os
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

@app.route("/", methods=["POST"])
def home():
    return render_template("index.html")


@app.route('/new-logs/<doctor_id>')
def new_logs(doctor_id):
    return render_template("d_new_logs.html")


@app.route('/redirect-doctor-to-patient-log/<doctor_id>', methods=['POST'])
def redirect_doctor_to_patient_log(doctor_id, patient_id, entry_id):
    return render_template("d_patient_med_log.html", patient_id=patient_id, entry_id=entry_id)

if __name__ == "__main__":
    app = db.factory.create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = config['PROD']['DB_URI']

    app.run(debug=True)
