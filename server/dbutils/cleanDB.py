import json
import sys

import pymongo as pym

my_client = pym.MongoClient()
db = my_client["playMyMood"]

p = db.songs.drop()
r = db.datapoints.drop()

if p:
    print("music data deleted")

if r:
    print("merged data deleted")
