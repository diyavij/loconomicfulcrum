from datetime import datetime
from pymongo import MongoClient
import time
x="hello world!"
client = MongoClient('mongodb://heroku_1n5jt39m:l3aqlpaavn7r99q9k8cata1ibe@ds155278.mlab.com:55278/heroku_1n5jt39m?retryWrites=false')
mydatabase = client["heroku_1n5jt39m"]
while True:
    now=datetime.now()
    current_time=now.strftime("%H:%M")
    if current_time>"23:58":
        mydatabase.jobs.drop()
        mydatabase.fs.files.drop()
        mydatabase.fs.chunks.drop()
        mydatabase.times.drop()
    time.sleep(60)
