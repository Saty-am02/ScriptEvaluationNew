from fastapi import APIRouter,File,UploadFile
import random
from PIL import Image
import base64
from io import BytesIO
import pandas as pd
import fitz
import google.generativeai as genai
import tempfile
import os
import shutil
from pathlib import Path
import json
import pyrebase
import requests
import pandas as pd
import firebase_admin
from firebase_admin import credentials, storage
#from typing import Annotated,List,Union


es_upload_router = APIRouter()


GEMINI_API = "AIzaSyD-HzbQwUFUN9libpS9NtXvYWVq8ibXCTA"

generation_config = {  
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 400,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


genai.configure(api_key=GEMINI_API)
model_vision = genai.GenerativeModel(
            "gemini-pro-vision", safety_settings=safety_settings
        )





try:

    cred =  {
        "apiKey": "AIzaSyAcNkl3QXy0L_OWmMlxGNSEHar0YZddP_Q",
        "authDomain": "scriptevaluation.firebaseapp.com",
        "projectId": "scriptevaluation",
        "storageBucket": "scriptevaluation.appspot.com",
        "messagingSenderId": "955685431488",
        "appId": "1:955685431488:web:41c163453fa74cfad1a525",
        "measurementId": "G-1M4P9LFB0V",
        "databaseURL":"https://scriptevaluation.firebaseio.com",
        "serviceAccount":"KEYS/firebase_cred.json"
        }
    
    
    


    firebase = pyrebase.initialize_app(cred)
    storage = firebase.storage()


except Exception as e:
        print(f"[-]Error during importing of pyrebase at es_upload.py : {str(e)}")
        



def is_file_present(file_path_cloud,file_path_local):
    try:
        file  = storage.child(file_path_cloud).download(file_path_local)
        print(f"[+]File Present at :  {file} ")
        print(file_path_cloud)
        print(file_path_local)
        return True
    except Exception as e:
        print(f"[-]csv file not present: {e}")
        return False




def save_upload_file(upload_file: UploadFile, destination: Path) -> str:
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            file_name = buffer.name
            print(type(file_name))
    finally:
        upload_file.file.close()
    return file_name


def delete_file(filename):
    try:
        os.remove(filename)
    except:
        print("[-]File cannot be deleted as it is not present")




def pdf2img(pdf_path):
        pdf_document = fitz.open(pdf_path)
        image_list = []

        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            image_list.append(page.get_pixmap())

        pdf_document.close()

        images = [
            Image.frombytes("RGB", (image.width, image.height), image.samples)
            for image in image_list
        ]

        # Combine all images vertically
        combined_image = Image.new(
            "RGB", (images[0].width, sum(image.height for image in images))
        )
        offset = 0

        for image in images:
            combined_image.paste(image, (0, offset))
            offset += image.height
        filename  = pdf_path.replace('.pdf','')
        # Save the combined image
        combined_image.save(f"{filename}.jpeg", "JPEG")
        return filename

@es_upload_router.post("/questions")
def num_question(exam_id:str,subject:str):
    try:
        storage_client = firebase_admin.storage.bucket()

        # Construct the path
        path = f"main_ES/{exam_id}/{subject}/"

        # Get all blobs in the specified path
        blobs = storage_client.list_blobs(prefix=path)
        quest = []
        for blob in blobs:
            if len(blob.name.split('/')[-2]) < 3:
                quest.append(blob.name.split('/')[-2])
        return max(quest)
    except:
        return 0






def uploadfile_main(exam_id,subject_id,es_PDFpath, qid, question, max_marks):
    extracted_text = ""
    additional_points = ""
    image_string = ""
    try:
        print('[+]uploading...')

        filename = pdf2img(es_PDFpath)
        es_JPEGpath = Image.open(f"expectedanswer.jpeg")
        
        
        
        
        path_on_cloud_PDF = f"main_ES/{exam_id}/{subject_id}/{qid}/expectedanswer.pdf"
        path_local_PDF = "expectedanswer.pdf"

        path_on_cloud_JPEG = f"main_ES/{exam_id}/{subject_id}/{qid}/expectedanswer.jpeg"
        path_local_JPEG = "expectedanswer.jpeg"
        
        path_on_cloud_CSV = f"main_ES/{exam_id}/{subject_id}/{exam_id}-{subject_id}_data.csv"
        path_local_CSV = f"test101-101_data.csv"
        #storing in the cloud
        storage.child(path_on_cloud_PDF).put(path_local_PDF)
        storage.child(path_on_cloud_JPEG).put(path_local_JPEG)
        
    
        flag = is_file_present(path_on_cloud_CSV,path_local_CSV)
         

        if flag == False:
            dicts = {"exam_id":exam_id,"subject_id":subject_id,"question_id":qid,"max_marks":max_marks,"question":question}


            df = pd.DataFrame(dicts,index=[0])
            df.to_csv(f"{exam_id}-{subject_id}_data.csv",index =False)
            print(df)
            json_data = df.to_json()
            storage.child(path_on_cloud_CSV).put(path_local_CSV)
    
        elif flag == True:
            storage.child(path_on_cloud_CSV).download(path_local_CSV)
            dicts = {"exam_id":exam_id,"subject_id":subject_id,"question_id":qid,"max_marks":max_marks,"question":question}

            
            df = pd.read_csv(path_local_CSV)
            

            index = df[df['question_id'] == int(qid)].index      
            print(index)
            #index_list= df(df['question_id'] == qid).index
            df.drop(index,axis=0,inplace=True)

            df = df._append(dicts,ignore_index=True)
            print(df)
            json_data = df.to_json()
            df.to_csv(path_local_CSV,index=False)

            storage.child(path_on_cloud_CSV).put(path_local_CSV)
           



        print("[+]Files finished uploading") 
        
        
        return json_data
    except Exception as e:
        print(f"[-]Error during uploading : {str(e)}")
        return -1



        

def extract_text(file_path):
    try:
        file_img_path = pdf2img(file_path)
        image = Image.open("question.jpeg")

        response = model_vision.generate_content(["Extract text from the give image , just give me the extracted text no need for any explanation or sorry message ",image])
    
        extract_text = response.text
        print(f"[+]Extracter Question is: {extract_text}")

    except Exception as e:
        print(f"[-] An error at extract_text : {e}")
        return (" ")

    return extract_text
    

        


        
            


@es_upload_router.post("/questions")
def num_question(exam_id:str,subject:str):
    try:
        storage_client = firebase_admin.storage.bucket()

        # Construct the path
        path = f"main_ES/{exam_id}/{subject}/"

        # Get all blobs in the specified path
        blobs = storage_client.list_blobs(prefix=path)
        quest = []
        for blob in blobs:
            if len(blob.name.split('/')[-2]) < 3:
                quest.append(blob.name.split('/')[-2])
        return max(quest)
    except:
        return 0





@es_upload_router.post('/evaluate/esupload')
async def ES_upload(exam_id:str,subject_id:str, mark: int,question_id:str,question_str:str | None=None ,ES: UploadFile = File(),question_file: UploadFile =  File(None)):
    

    if question_str:

        max_marks = str(mark)
    
        file_one_path = save_upload_file(ES, Path(f"expectedanswer.pdf"))
    

        json_data = uploadfile_main(exam_id,subject_id,file_one_path,question_id,question_str,max_marks)
    
    
    #print(f"{file_one_path},,{file_two_path}")
        
        delete_file(file_one_path)
        delete_file("expectedanswer.jpeg")
        delete_file(f"{exam_id}-{subject_id}_data.csv")
        

    elif question_file:
        max_marks = str(mark)

        file_one_path = save_upload_file(ES,Path(f"expectedanswer.pdf"))
        #print("file size : "+str(len(question_file)))

        question_file_path = save_upload_file(question_file,Path(f"question.pdf"))

        extracted_question = extract_text(question_file_path)

        json_data = uploadfile_main(exam_id,subject_id,file_one_path,question_id,extracted_question,max_marks)
        
        
        delete_file(file_one_path)
        delete_file("expectedanswer.jpeg")
        delete_file(question_file_path)
        delete_file("question.jpeg")
        
    else:
        json_data = {"Error":"[-]No Question is Uploaded"}
    
    #return result
    

    #json_data=json.dumps(result)

    
    return json_data








