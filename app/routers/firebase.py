from fastapi import FastAPI, APIRouter, Form
from fastapi.staticfiles import StaticFiles
import secrets
from firebase_admin import credentials, firestore, initialize_app, storage
from fastapi.security import APIKeyCookie

FIREBASE_CREDENTIALS_PATH = r"KEYS/firebase_cred.json"

app = FastAPI()
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


firebase_API = APIRouter()


@firebase_API.get("/get_students")
def get_students():
    print("Getting students")
    student_dict = {}
    student_ref = db.collection('SID')
    all_students = student_ref.stream()
    for SID in all_students:
        update_sequence = [(SID.id, SID.to_dict()['Uploaded'])]
        student_dict.update(update_sequence)
        print(student_dict)
    
    return student_dict

@firebase_API.post("/add_status")
def add_status(StudentID: str = Form(...), uploaded: bool = Form(...)):
    student_db = db.collection("SID")
    student_ref = student_db.document(StudentID)
    student_ref.set({
        "Uploaded" : uploaded
    })

    return {"Message" : "Uploaded status successfully!"}

@firebase_API.get("/get_subjects")
def get_subjects():
    subjects = {}
    subject_db = db.collection("SubjectID").document("Subjects")
    sub_snapshot = subject_db.get().to_dict()

    return sub_snapshot

@firebase_API.post('/add_subject')
def add_subject(Subject: str = Form(...), Evaluation_Uploaded: bool = Form(...)):
    sub_ref = db.collection("SubjectID").document('Subjects')
    sub_ref.update({
        Subject : Evaluation_Uploaded
    })
    return {"Message" : "Added subject successfully!"}


@firebase_API.get("/examIDs")
def get_examIDs():
    all_exams = []
    exams_db = db.collection("ExamID")
    exam_ref = exams_db.stream()
    for exam in exam_ref:
        all_exams.append(exam.id)
    
    return ({"Exams" : all_exams})
