# firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from settings import firebase_credentials

cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
firebase_db = firestore.client()
