from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
from werkzeug.exceptions import BadRequestKeyError
import re

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Login.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        reg_pass = request.form['reg_pass']
        cursor = db_conn.cursor()

        query = "INSERT INTO Login (reg_id, reg_pass) VALUES (%s, %s)"
        cursor.execute(query, (reg_id, reg_pass))
        db_conn.commit()

        print("Registration successful")
        return render_template('Login.html', success="Registration successful! Please login to continue.")
    else:
        return render_template('Register.html')


@app.route("/Login", methods=['POST', 'GET'])
def Login():
    if request.method == 'POST':
        reg_id = request.form['reg_id'].lower()
        reg_pass = request.form['reg_pass']
        cursor = db_conn.cursor()

        # Check if the combination of reg_id and reg_pass exists in the database
        check_login = "SELECT COUNT(*) FROM Login WHERE reg_id = %s AND reg_pass = %s"
        cursor.execute(check_login, (reg_id, reg_pass))
        result = cursor.fetchone()[0]

        if result > 0:
            print("Login successful")
            return render_template('Home.html')
        else:
            print("Invalid user id or/and password!")
            error = "Invalid user id or/and password!"
            return render_template('Login.html', error=error)
    
    return render_template('Login.html')

@app.route("/addemp", methods=['GET', 'POST'])
def AddEmp():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pri_skill = request.form['pri_skill']
        location = request.form['location']
        emp_image_file = request.files['emp_image_file']

        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if emp_image_file.filename == "":
            return "Please select a file"

        try:
            cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
            db_conn.commit()
            emp_name = "" + first_name + " " + last_name
            
            # Upload image file in S3
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

            except Exception as e:
                return str(e)

        finally:
            cursor.close()

        print("All modifications done...")
        return render_template('AddEmpOutput.html', name=emp_name)
    else:
        return render_template('AddEmp.html')



@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    if 'emp_id' in request.form:
        emp_id = (request.form['emp_id']).lower()
        check_sql = "SELECT emp_id FROM employee WHERE emp_id=(%s)"
        cursor = db_conn.cursor()
        cursor.execute(check_sql, (emp_id,))
        emp_id = re.sub('\W+','',str(cursor.fetchall()))
        check_sql = "SELECT first_name FROM employee WHERE emp_id=(%s)"
        cursor = db_conn.cursor()
        cursor.execute(check_sql, (emp_id,))
        emp_first = re.sub('\W+','',str(cursor.fetchall()))
        check_sql = "SELECT last_name FROM employee WHERE emp_id=(%s)"
        cursor = db_conn.cursor()
        cursor.execute(check_sql, (emp_id,))
        emp_last = re.sub('\W+','',str(cursor.fetchall()))
        check_sql = "SELECT pri_skill FROM employee WHERE emp_id=(%s)"
        cursor = db_conn.cursor()
        cursor.execute(check_sql, (emp_id,))
        emp_interest = re.sub('\W+','',str(cursor.fetchall()))
        check_sql = "SELECT location FROM employee WHERE emp_id=(%s)"
        cursor = db_conn.cursor()
        cursor.execute(check_sql, (emp_id,))
        emp_location = re.sub('\W+','',str(cursor.fetchall()))
        emp_image_url = re.sub('\W+','',str(cursor.fetchall()))
        if str(emp_first) != "":
            return render_template('GetEmpOutput.html', id=emp_id, fname=emp_first, lname=emp_last, interest=emp_interest, location=emp_location, image_url=emp_image_url)
        else:
            print("Invalid ID")
            return render_template('GetEmp.html')
    else:
        print("emp_id key not found in request.form")
        return render_template('GetEmp.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
