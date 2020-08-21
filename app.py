from flask import Flask, redirect, url_for, render_template, request, session, g, app
from werkzeug.utils import secure_filename
import gridfs
import sys
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from base64 import b64encode
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gridfs
client = MongoClient('mongodb://heroku_1n5jt39m:l3aqlpaavn7r99q9k8cata1ibe@ds155278.mlab.com:55278/heroku_1n5jt39m?retryWrites=false')
mydatabase = client["heroku_1n5jt39m"]
fs=gridfs.GridFS(mydatabase, collection="fs")
gs=gridfs.GridFS(mydatabase, collection="gs")
app=Flask(__name__)
app.secret_key = "lgmpisgood"

# for email verification
app.config.from_pyfile('config.cfg')
mail = Mail(app)
s = URLSafeTimedSerializer('Thisisasecret!')
a = URLSafeTimedSerializer('secret!')

def is_time_between(begin_time, end_time, check_time):
    pass
def is_time_right(begin_time, end_time):
    return begin_time<=end_time
@app.route("/add", methods=["POST", "GET"])
def add():
    if "user" in session:
        users = getUser()
        if request.method=="POST":
            radio=request.form.get("V/J")
            email=request.form.get("phone")
            start_time=request.form.get("stime")
            end_time=request.form.get("etime")
            back_check=request.files["bcheck"]
            img=request.files["yourImage"]
            img_id=fs.put(img,encoding='utf-8')
            back_check_id=fs.put(back_check,encoding='utf-8')
            message="Please add a background check certificate to continue"
            message2="Your end time is before your start time!"
            message3="you can't post 2 job availabilities! wait until tommorow to post your availability"
            istime=is_time_right(start_time, end_time)
            data={"job_type":radio, "email":email, "start_time":start_time, "end_time":end_time, "back_check_id":back_check_id, "face_img_id":img_id}
            mydatabase.jobs.insert_one(data)
            compare1=mydatabase.fs.files.find({"_id":ObjectId(back_check_id)},{"length":1,"_id":0})
            compare2=mydatabase.jobs.find({"back_check_id":ObjectId(back_check_id)},{"job_type":1, "_id":0})
            
            dc={"email": email}
            comp=[]
            for y in compare1:
                comp.append(list(y.values()))
            for x in compare2:
                comp.append(list(x.values()))
            print(img_id,back_check_id, file=sys.stderr)
            if istime==False:
                mydatabase.jobs.delete_one({"back_check_id":ObjectId(back_check_id)})
                mydatabase.fs.files.delete_one({"_id":ObjectId(back_check_id)})
                mydatabase.fs.chunks.delete_one({"files_id":ObjectId(back_check_id)})
                mydatabase.fs.chunks.delete_one({"files_id":ObjectId(img_id)})
                mydatabase.fs.files.delete_one({"_id":ObjectId(img_id)})
                return render_template("signup_hire.html", message=message2, users=users)
            if comp[0][0]==0 and comp[1][0]=="Job":
                mydatabase.jobs.delete_one({"back_check_id":ObjectId(back_check_id)})
                mydatabase.fs.files.delete_one({"_id":ObjectId(back_check_id)})
                mydatabase.fs.chunks.delete_one({"files_id":ObjectId(back_check_id)})
                mydatabase.fs.chunks.delete_one({"files_id":ObjectId(img_id)})
                mydatabase.fs.files.delete_one({"_id":ObjectId(img_id)})
                return render_template("signup_hire.html", message=message, users=users)
            time={"email":email,"start_time":start_time, "end_time":end_time}
            mydatabase.times.insert_one(time)
            return render_template("signup_hire.html", users=users)
        else:
            return render_template("signup_hire.html", users=users)
    return render_template("login.html", message="Make sure you are logged in!")
        
@app.route("/jobs", methods=["POST", "GET"])
def jobs():
    if "user" in session:
        documents = mydatabase.jobs.find({})
        allListings = []
        overflowOne = []
        overflowTwo = []
        of1 = False
        of2 = False
        users = getUser()
        for document in documents:
            allListings.append(list(document.values()))

        for item in allListings:
            b = fs.get(item[6]).read()
            image = b64encode(b).decode("utf-8")
            item.append(image)

##        if len(allListings) % 3 == 1:
##            i = allListings.index(allListings[-1])
##            overflowOne.append(allListings.pop(i))
##            of1 = True
##        elif len(allListings) % 3 == 2:
##            i = allListings.index(allListings[-1])
##            n = allListings.index(allListings[-2])
##            overflowTwo.append(allListings.pop(i))
##            overflowTwo.append(allListings.pop(n))
##            of2 = True
##        chunkedList = [allListings[x:x + 3] for x in range(0, len(allListings), 3)]
        print(len(allListings))
        return render_template('jobs.html', response=allListings, of1=of1, of2=of2, overflowOne=overflowOne, overflowTwo=overflowTwo, users=users)
    return render_template("login.html", message="Make sure you are logged in!")

@app.route("/BackgroundCheck/<bcheck>")
def bcheckimg(bcheck):
    back_checkb=fs.get(ObjectId(bcheck)).read()
    back_checkf=b64encode(back_checkb).decode("utf-8")
    return f"<img src='data:;base64,{back_checkf}'>"
def datesoverlap(s1, e1, s2, e2):
  if max(s1,s2)<min(e1,e2):
    return True
  else:
    return False

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['user']
        password = request.form['pass']
        document = {"username": username, "password": password}
        userDocument = {"username": username}
        verifiedDocument = {"username": username, "password": password, "verified": True}
        # Make sure that account does exist
        if mydatabase.listingUsers.find(userDocument).count() > 0:
            # and credentials are correct
            if mydatabase.listingUsers.find(document).count() > 0:
                # and is email verified
                if mydatabase.listingUsers.find(verifiedDocument).count() > 0:
                    session['user'] = username
                    rests = getAllDocs()
                    users = getUser()
                    return render_template("index.html", response=rests, users=users)
                else:
                    emailVerification(username)
                    return render_template("login.html", message="Make sure your account has been verified. We resent the email!")
            else:
                return render_template("login.html", message="Incorrect password.")
        else:
            return render_template("login.html", message="An account with that email address does not exist.")
    return render_template("login.html")


@app.route('/signupTxt')
def signupTxt():
    return render_template("signup.html")


@app.route('/signup', methods=["POST"])
def signup():
    global usernameUp
    fName = request.form['fname']
    lName = request.form['lname']
    usernameUp = request.form['userSignup']
    passwordUp = request.form['passSignup']
    query = {"username": usernameUp}
    # Checking if the chosen username exists
    if mydatabase.listingUsers.find(query).count() > 0:
        return render_template("signup.html", message="That email address already has an account.")
    else:
        document = {"firstname": fName, "lastname": lName, "username": usernameUp, "password": passwordUp, "verified": False}
        rec1 = mydatabase.listingUsers.insert_one(document)
        session['user'] = usernameUp
        emailVerification(usernameUp)

        return render_template("signup.html", message=f"Your account has been created! Check your email to verify your account and get started! The link expires in an hour!")

@app.route('/confirmEmail/<token>', methods=["GET"])
def confirmEmail(token):
    username = request.args.get('username')
    email = s.loads(token, salt='email-confirm', max_age=3600)
    myquery = {"username": username}
    newvalues = {"$set": {"verified": True}}

    mydatabase.listingUsers.update_one(myquery, newvalues)

    return render_template("login.html", message="Email confirmed. You can log in now!")

@app.route('/insertTxt')
def insertTxt():
    if "user" in session:
        rests = getAllDocs()
        users = getUser()
        return render_template("index.html", response=rests, users=users)
    return render_template("login.html", message="Make sure you are logged in!")

@app.route('/insert', methods=["POST"])
def insertToDatabase():
    if "user" in session:
        nameOfItem = request.form["noi"]
        description = request.form["desc"]
        price = request.form["price"]
        quantity = request.form["quan"]
        img = request.files["imgFile"]
        a = gs.put(img, encoding='utf-8')
        now = datetime.today()
        now = now.strftime('%m-%d-%Y')

        rec = {"name": nameOfItem,
               "description": description,
               "price": price,
               "currentdate": now,
               "user": g.user,
               "quantity": quantity,
               "image": a}
        print(g.user)
        rec1 = mydatabase.listings.insert_one(rec)
        rests = getAllDocs()
        users = getUser()

        return render_template("index.html", response=rests, users=users)
    return render_template("login.html", message="Make sure you are logged in!")


@app.route('/delete', methods=["POST"])
def deleteFromDatabase():
    if "user" in session:
        idToDelete = request.form["idfieldDelete"]
        idToDeleteImg = request.form["idfieldDeleteImg"]
        print(idToDelete)
        print(idToDeleteImg)
        mydatabase.listings.delete_one({'_id': ObjectId(idToDelete)})
        mydatabase.listings.chunks.delete_many({'files_id': ObjectId(idToDeleteImg)})
        mydatabase.listings.files.delete_one({'_id': ObjectId(idToDeleteImg)})
        rests = getAllDocs()
        users = getUser()
        return render_template("index.html", response=rests, users=users)
    return render_template("login.html", message="Make sure you are logged in!")

@app.route('/update', methods=["POST"])
def updateDatabase():
    if "user" in session:
        idToUpdate = request.form["upid"]
        nameToUpdate = request.form["upnoi"]
        descToUpdate = request.form["updesc"]
        priceToUpdate = request.form["upprice"]
        quantityToUpdate = request.form["upquan"]

        updateList = []
        myquery = {'_id': ObjectId(idToUpdate)}
        newvalues = {"$set": {"name": nameToUpdate, "description": descToUpdate, "price": priceToUpdate, "quantity": quantityToUpdate}}

        mydatabase.listings.update_one(myquery, newvalues)
        rests = getAllDocs()
        users = getUser()

        return render_template("index.html", response=rests, users=users)
    return render_template("login.html", message="Make sure you are logged in!")

@app.route("/signout")
def signout():
    if "user" in session:
        session.clear()
        return render_template("login.html", message="Successfully logged out!")
    return render_template("login.html", message="Make sure you are logged in!")

def getAllDocs():
    documents = mydatabase.listings.find({"user": g.user})
    rests = []
    for document in documents:
        rests.append(list(document.values()))
    for item in rests:
        b = gs.get(item[7]).read()
        image = b64encode(b).decode("utf-8")
        item.append(image)
    print(rests)
    return rests

def getUser():
    print(g.user)
    userDocuments = mydatabase.listingUsers.find({"username": g.user})
    users = []
    for userDocument in userDocuments:
        users.append(list(userDocument.values()))
    print(users)
    return users

def emailVerification(emailTo):
    token = s.dumps(emailTo, salt='email-confirm')
    URL = f"http://loconomic-fulcrum.herokuapp.com/confirmEmail/{token}?username={emailTo}"

    # me == my email address
    # you == recipient's email address
    me = "LoconomicFulcrum@gmail.com"
    you = emailTo

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "LGMP Verification"
    msg['From'] = me
    msg['To'] = you

    # Create the body of the message (a plain-text and an HTML version).
    text = f"Hi!\nClick on the following link to verify your account:\n{URL}"
    html = f"""\
    <html>
      <head></head>
      <body>
        <p>Hi!<br>
           Click on <a href="{URL}">this</a> link to verify your LGMP account.
        </p>
      </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login('LoconomicFulcrum', 'SajeevRohan')
    mail.sendmail(me, you, msg.as_string())
    mail.quit()

@app.route('/updateQuantity', methods=["POST"])
def updateQuantity():
    if "user" in session:
            idToQuat = request.form['idQuant']
            quant=request.form["quant"]
            myquery = {'_id': ObjectId(idToQuat)}
            getQuant = mydatabase.listings.find(myquery)
            for document in getQuant:
                result = list(document.values())
            result = result[6]
            result = int(result)
            quant=int(quant)
            newResult = result = result - quant
            newvalues = {"$set": {"quantity": newResult}}
            
            mydatabase.listings.update_one(myquery, newvalues)
            rests = getAllDocs()
            users = getUser()
            return render_template('redirectListings.html')

    return render_template("login.html", message="Make sure you are logged in!")

@app.route("/search", methods=["GET"])
def search():
    if "user" in session:
        query = request.args.get('query')
        allListings = []
        rests = []
        documents = mydatabase.listings.find({})
        for document in documents:
            rests.append(list(document.values()))

        for item in rests:
            name = str(item[1])
            if query.lower() in name.lower():
                allListings.append(item)

        overflowOne = []
        overflowTwo = []
        of1 = False
        of2 = False

        for item in allListings:
            b = gs.get(item[7]).read()
            image = b64encode(b).decode("utf-8")
            item.append(image)
        users = getUser()

        if len(allListings) % 3 == 1:
            i = allListings.index(allListings[-1])
            print(i)
            overflowOne.append(allListings.pop(i))
            of1 = True
        elif len(allListings) % 3 == 2:
            i = allListings.index(allListings[-1])
            n = allListings.index(allListings[-2])
            overflowTwo.append(allListings.pop(i))
            overflowTwo.append(allListings.pop(n))
            of2 = True


        chunkedList = [allListings[x:x + 3] for x in range(0, len(allListings), 3)]

        return render_template('listings.html', response=chunkedList, users=users, of1=of1, of2=of2,
                               overflowOne=overflowOne, overflowTwo=overflowTwo)
    return render_template('login.html', message="Make sure you are logged in!")


@app.route('/listings', methods=['GET', 'POST'])
def listings():
    if "user" in session:
        documents = mydatabase.listings.find({})
        allListings = []
        overflowOne = []
        overflowTwo = []
        of1 = False
        of2 = False
        for document in documents:
            allListings.append(list(document.values()))

        for item in allListings:
            b = gs.get(item[7]).read()
            image = b64encode(b).decode("utf-8")
            item.append(image)
        users = getUser()

        if len(allListings) % 3 == 1:
            i = allListings.index(allListings[-1])
            print(i)
            overflowOne.append(allListings.pop(i))
            of1 = True
        elif len(allListings) % 3 == 2:
            i = allListings.index(allListings[-1])
            n = allListings.index(allListings[-2])
            overflowTwo.append(allListings.pop(i))
            overflowTwo.append(allListings.pop(n))
            of2 = True
        print(overflowOne)
        print(overflowTwo)
        print(of1)
        print(of2)

        chunkedList = [allListings[x:x + 3] for x in range(0, len(allListings), 3)]



        return render_template('listings.html', response=chunkedList, users=users, of1=of1, of2=of2, overflowOne=overflowOne, overflowTwo=overflowTwo)
    return render_template('login.html', message="Make sure you are logged in!")

@app.before_request
def before_request():
    g.user = None
    if "user" in session:
        g.user = session['user']

    
if __name__=="__main__":
    app.run()
    
