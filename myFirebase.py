#!/usr/bin/python3

#
# access to firebase firestore
#

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use the application default credentials
# (this setting is only for GCP environment, not for local PC environemnt, etc.)
cred = credentials.ApplicationDefault()
#firebase_admin.initialize_app()
firebase_admin.initialize_app(cred, {
        'projectId': "fresh-catwalk-335010",
})


# query to BigQuery and return DataFrame
def queryFirestore(collectionName, limit):
    db = firestore.client()
    coll_ref = db.collection(collectionName)
    docs = coll_ref.stream()
    #for doc in docs:
        #print(f'{doc.id} => {doc.to_dict()}')
    return docs


def addFirestore(collectionName, data):
    db = firestore.client()
    coll_ref = db.collection(collectionName)
    for d in data:
        coll_ref.add(d)
    


if __name__ == "__main__":
    queryFirestore("sampleKey", 5)
    #addFirestore("sampleKey", [{"city":"Okayama", "country":"JAPAN"}])
    #print("added to sampleKey")
    print("done")
