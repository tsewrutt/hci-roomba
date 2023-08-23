import numpy as np
import random
import requests
import sys
import os
import time
import threading

# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore
#     # Use a service account.
# cred = credentials.Certificate('hri-roomba-data-83bcb0b681a0.json')

# app = firebase_admin.initialize_app(cred)

# db = firestore.client()

#controlsDoc_ref_stream = db.collection('movements').stream()
# controlsDirection_Ref = db.collection('movements').document('direction')
# users_ref = db.collection('tasks')
# docs = users_ref.stream()
# tasksCounter = 0

# for doc in docs:

#     if(doc.to_dict()["status"] == "incomplete"):
# 		    tasksCounter = tasksCounter + 1
# print("Incomplete Tasks: " + str(tasksCounter))



    #print(f'{doc.id} => {doc.to_dict()}')
    # if(doc.to_dict()["status"] == "incomplete"):
    #     doc.reference.update({'status': "pending"})
# def listen_doc():
#        callback_done = threading.Event()

def on_snapshot(doc_snapshot, changes, read_time):
#    for doc in doc_snapshot:
#        print(f'Received doc snapshot: {doc.id}')
    return
    


if __name__ == "__main__":

        try:
            #doc_ref = db.collection('movements').document('direction')      
            # controlsDirection_Ref.on_snapshot(on_snapshot)
            # while True:
            #        #print(docGet.to_dict())
            #        #print(db.collection('movements').stream().get().to_dict())
            #        print(controlsDirection_Ref.get().to_dict())
            #        time.sleep(0.01)
            numofCollisiona = 0
            for x in range(3):
                  print('x:', x,'times')

        except Exception:
                print("Error")
        
        sys.exit()