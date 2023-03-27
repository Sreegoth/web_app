#General Flask Imports
from flask import Flask, render_template, request, session

#For MySQL Database connection
import mysql.connector as mysql

#For OTP validation though mail
from flask_mail import Mail, Message
from random import randint

#For Art Generation
import io
import os
import warnings
from PIL import Image
import PIL
import base64
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

#Importing external files

#Intialization
app = Flask(__name__)
app.secret_key = "richard"



#Connection to the mail server to send OTP
mail = Mail(app)
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'richarda0538@gmail.com'
app.config['MAIL_PASSWORD'] = 'zydmmtbspdsoknat'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


#Connection to the Database
db = mysql.connect(
    host='localhost',
    user='root',
    password='mysql123@',
    database='imagepicto'
)
cur = db.cursor()



#Index Page
@app.route('/')
def index():
    return render_template("index.html")

#Home Page
@app.route('/home')
def homePage():
    return render_template("home_page.html")



#MODULE1 - Registration, Login, Forgot Password, Logout

#Calling Login_Register File
@app.route('/loginRegister')
def loginRegister():
    return render_template('login_register.html')

#Validating Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    le = request.form['emailid']
    lp = request.form['loginpassword']

    session['emailid'] = le
    session['loginpassword'] = lp
    sql = "SELECT email, passward FROM user_data WHERE email=%s"
    email = [(session['emailid'])]
    cur.execute(sql, email)
    user = cur.fetchone()
    if user:
        if session['emailid'] == user[0] and session['loginpassword'] == user[1]:
            return render_template('home_page.html')
        else:
            return render_template('login_register.html', abc='Invalid Login!')
    else:
        return render_template('login_register.html', abc='No Rocords Found! Please Register!!')

#Validating Register
@app.route('/register', methods=['POST'])
def register():
    fn = request.form['firstname']
    ln = request.form['lastname']
    re = request.form['emailid']
    rp = request.form['registerpassword']
    cp = request.form['confirmpassword']
    rflag = 0
    session['emailid'] = re
    sql = "SELECT email FROM user_data WHERE email=%s"
    ue = [(session['emailid'])]
    cur.execute(sql, ue)
    regdata = cur.fetchone()
    if regdata:
        if session['emailid'] == regdata[0]:
            rflag = 1
            return render_template('login_register.html', abc="Account already Exists!", rflag=rflag)
    else:
        if fn.isalpha() and ln.isalpha():
            if rp == cp:
                sql = "INSERT INTO user_data(firstname, lastname, email, passward) VALUES(%s, %s, %s, %s)"
                val = (fn, ln, re, rp)
                cur.execute(sql, val)
                db.commit()
                return render_template('home_page.html')
            else:
                rflag = 1
                return render_template('login_register.html', abc='Passwords did not match!', rflag=rflag)
        else:
            rflag = 1
            return render_template('login_register.html', abc='First and Last Names should be characters', rflag=rflag)

#Calling Forgot Password Page
@app.route('/forgot')
def forgotPassword():
    return render_template('forgot_password.html')

#Generate OTP and send to the mail
@app.route('/getOtp', methods=['POST'])
def getOtp():
    email = request.form['emailid']
    sql = "SELECT email FROM user_data WHERE email=%s"
    cur.execute(sql, [email])
    user = cur.fetchone()
    if user:
        if email == user[0]:
            msg = Message(subject='OTP', sender='richardson00538@gmail.com', recipients=[email])
            session['otp'] = randint(000000, 999999)
            msg.body = str(session['otp'])
            mail.send(msg)
            return render_template('forgot_password.html', res='OTP sent!', email=str(email)[2:-2])
        else:
            return render_template('login_register.html', abc='No Rocords Found! Please Register!!')
    else:
        return render_template('login_register.html', abc='No Rocords Found! Please Register!!')
    

#Validating the OTP obtained
@app.route('/validate', methods=["POST"])
def validate():
    user_otp = request.form['otp']
    if session['otp'] == int(user_otp):
        return render_template('reset_password.html')
    return render_template('forgot_password.html', abc="Incorrect OTP!")

#Resetting the Password
@app.route('/reset', methods=['POST'])
def reset():
    newpass = request.form['newpass']
    confirmpass = request.form['confirmpass']
    if newpass==confirmpass:
        sql = "UPDATE user_data SET password=%s WHERE email=%s"
        val = [newpass, (session['emailid'])]
        cur.execute(sql, val)
        db.commit()
        return render_template('login_register.html', abc="Password Upadted! Please Re-Login")
    else:
        return render_template('reset_password.html', abc="Invaid!")


#MODULE2 - Art Generation, Meme Generation, Criminal Face GEneration, Poster PResentation

#Connection to the server
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
os.environ['STABILITY_KEY'] = 'sk-bS0wfTvkEiOYYayTvtInZRuGvYnsuftbJ5O9JidiJxSpTbfK'
stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'],
    verbose=True,
    engine="stable-diffusion-v1-5"
)

#Function to generate art image
def generateimage(text):
    for resp in text:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                data = io.BytesIO()
                img.save(data, "JPEG")
                encoded_img_data = base64.b64encode(data.getvalue())
                #img.show()
    return encoded_img_data.decode('utf-8')

#ART GENERATION

#Calling Art Generation Page(art)
@app.route('/art')
def art():
    return render_template('art_generation.html')

#Generating the art image based on given input
@app.route('/generateArt', methods=["POST"])
def generateArt():
    text = request.form['t1']
    prompt= "8k resolution image of " + text
    answers = stability_api.generate(
    prompt=prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("art_generation.html", img_data=img_data, prompt=text)


#Criminal Face Generation

#Calling Criminal Face Generation Page
@app.route('/criminal_face_generation')
def criminal_face():
    return render_template('criminal_face_generation.html')

#Generating face based on the given text
@app.route('/generateFace', methods=["POST"])
def generateFace():
    gender = request.form['gender']
    age = request.form['age']
    hair = request.form['hair']
    face = request.form['face']
    eyes = request.form['eyes']
    nose = request.form['nose']
    lips = request.form['lips']
    skin = request.form['skin']
    t2 = request.form['t2']
    prompt = "a neat clear coloured front image "+gender+" of "+age+" years old, "+hair+" hair, "+face+" face, "+eyes+" eyes, "+nose+" nose, "+lips+" lips, "+skin+" skin, "+t2
    answers = stability_api.generate(
    prompt=prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("criminal_face_generation.html", img_data=img_data, gender=gender, age=age, hair=hair, face=face, eyes=eyes, nose=nose, lips=lips, skin=skin, t2=t2)

#Meme Generation

#Calling Criminal Face Generation Page
@app.route('/memes_generation')
def memes():
    return render_template('memes_generation.html')

#Generating the art image based on given input
@app.route('/generateMeme', methods=["POST"])
def generateMeme():
    prompt=request.form['meme']
    answers = stability_api.generate(
    prompt="a meme on "+prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("memes_generation.html", img_data=img_data, prompt=prompt)

#Poster Generation

#Calling Poster Generation Page
@app.route('/poster_generation')
def poster():
    return render_template('poster_generation.html')

#Generating the poster based on given input
@app.route('/generatePoster', methods=["POST"])
def generatePoster():
    prompt=request.form['poster']
    answers = stability_api.generate(
    prompt="a poster on "+prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("poster_generation.html", img_data=img_data, prompt=prompt)


#MODULE2 - Art Generation, Meme Generation, Criminal Face GEneration, Poster PResentation

#Calling Profile Page
@app.route('/profile')
def profilePage():
    sql = "SELECT firstname, lastname FROM user_data WHERE email=%s"
    email = [(session['emailid'])]
    cur.execute(sql, email)
    user = cur.fetchone()
    print(str(email)[2:-2])
    return render_template('profile_page.html', name=str(user[0]+" "+user[1]), email=str(email)[2:-2])

#Running the code
if __name__ == "__main__":
    app.run(debug=True)