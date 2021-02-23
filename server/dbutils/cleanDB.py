import pymongo as pym
import json
import sys

my_client = pym.MongoClient()
db = my_client['playMyMood']

p = db.songDataPoint.drop()
q = db.bodyDataPoint.drop()

if p:
    print("listening data deleted")

if q:
    print("fitness data deleted")
