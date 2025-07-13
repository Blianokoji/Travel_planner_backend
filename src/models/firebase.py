# firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from settings import firebase_credentials
import logging

try:
    if firebase_credentials:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred)
        firebase_db = firestore.client()
        logging.info("Firebase initialized successfully")
    else:
        # Initialize with default credentials (for local development)
        firebase_admin.initialize_app()
        firebase_db = firestore.client()
        logging.info("Firebase initialized with default credentials")
except Exception as e:
    logging.error(f"Failed to initialize Firebase: {e}")
    firebase_db = None
