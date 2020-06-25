#!/usr/bin/env python
# coding: utf-8

import pickle
import os
from pymongo import MongoClient
client = MongoClient()
db = client.jeepforum
db.create_collection('posts')
files = os.listdir('postdata')
for file in files:
    with open('postdata/'+file,'rb') as cellar:
        post_dicts = pickle.load(cellar)
    db.posts.insert_many(post_dicts)
print(db.posts.count_documents({}))
