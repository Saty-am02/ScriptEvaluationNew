from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import secrets
from firebase_admin import credentials, firestore, initialize_app, storage
from fastapi.security import APIKeyCookie

FIREBASE_CREDENTIALS_PATH = r"KEYS\firebase_cred.json"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
secret_key = secrets.token_hex(16)

api_key_cookie = APIKeyCookie(name = "session_cookie", auto_error= False)
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)

firebase_app = initialize_app(cred, {
    'databaseURL': 'https://scriptevaluation.firebaseio.com/',
    'storageBucket': 'scriptevaluation.appspot.com', 
})

# initialize_app(cred, {'databaseURL': 'https://scriptevaluation.firebaseio.com/'})

db = firestore.client()
storage_client = storage

from app import routers
