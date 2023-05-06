from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

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


@app.route("/Login", methods=['POST', 'GET'])
def Login():
    reg_id = (request.form['reg_id']).lower()
    reg_pass = request. form['reg_pass']

    check_id = "SELECT COUNT (reg_id) FROM user WHERE reg_id=(%s)"
    check_pass = "SELECT COUNT(reg_pass) FROM user WHERE reg_pass-(%s) "
    correct_id = False
    correct_pass = False
    cursor = db_conn.cursor()

    if (cursor.execute(check_id, (reg_id)))>0:
        correct_id = True
        
    if (cursor.execute(check_pass, (reg_pass))) >0:
        correct_pass = True

    if correct_id and correct_pass:
        print("Login successful")
        return render_template('Home.html')
    else:
        print("Invalid user id or/and password!")
        correct_id = False
        correct_pass = False
        return render_template('Login.html')


@app.route("/Register", methods=['GET', 'POST'])
def registerEmp():
    reg_id = (request.form['reg_id'])
    reg_pass = request.form['reg_pass']
    reg_conf_pass = request.form['reg_conf_pass']
    
    insert_sql = "INSERT INTO register VALUES (%s, %s)"
    select_sql = "SELECT * FROM register WHERE reg_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, (reg_id))
    regid_no=cursor.fetchall()
    
    if reg_conf_pass!=reg_pass:
        print("Confirm password is wrong.")
        return render_template('Register.html')
    elif str(regid_no) != "()":
        print("This ID already existed. Please enter another one.")
        return render_template('Register.html')
    else:
        try:
            cursor.execute(insert_sql, (reg_id, reg_pass))
            db.conn.commit()
            
        finally:
            cursor.close()
            
        print("Successfully registered")
        return render_template("Login.html")


@app.route("/addemp", methods=['POST'])
def AddEmp():
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
        # Uplaod image file in S3 #
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

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    emp_id = (request.form['emp_id']).lower()
    check_sql = "SELECT emp_id FROM employee WHERE emp_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(check_sql, (emp_id))
    emp_id = re.sub('\W+','',str(cursor.fetchall()))
    check_sql = "SELECT first_name FROM employee WHERE emp_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(check_sql, (emp_id))
    emp_first = re.sub('\W+','',str(cursor.fetchall()))
    check_sql = "SELECT last_name FROM employee WHERE emp_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(check_sql, (emp_id))
    emp_last = re.sub('\W+','',str(cursor.fetchall()))
    check_sql = "SELECT pri_skill FROM employee WHERE emp_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(check_sql, (emp_id))
    emp_interest = re.sub('\W+','',str(cursor.fetchall()))
    check_sql = "SELECT location FROM employee WHERE emp_id=(%s)"
    cursor = db_conn.cursor()
    cursor.execute(check_sql, (emp_id))
    emp_location = re.sub('\W+','',str(cursor.fetchall()))
    emp_image_url = re.sub('\W+','',str(cursor.fetchall()))
    if str(emp_first) != "":
        return render_template('GetEmpOutput.html', id=emp_id, fname=emp_first, lname=emp_last, interest=emp_interest, location=emp_location, image_url=emp_image_url)
    else:
        print("Invalid ID")
        return renderrender_template('GetEmp.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
