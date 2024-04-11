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


as_upload_router = APIRouter()

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
        print(f"[-]Error during importing of pyrebase at as_upload.py : {str(e)}")
        



def is_file_present(file_path_cloud,file_path_local):
    try:
        file  = storage.child(file_path_cloud).download(file_path_local)
        print(f"[+]File Present at :  {file} ")
        return True
    except Exception as e:
        print(f"[-]csv file not present: {e}")
        print(file_path_cloud)
        print(file_path_local)
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








def uploadfile_main(exam_id,subject_id,as_PDFpath, qid,student_id):
    extracted_text = ""
    additional_points = ""
    image_string = ""
    try:
        print('[+]uploading...')

        filename = pdf2img(as_PDFpath)
        
        
        
        
        path_on_cloud_PDF = f"main_AS/{exam_id}/{subject_id}/{student_id}/{qid}/studentanswer.pdf"
        path_local_PDF = "studentanswer.pdf"

        path_on_cloud_JPEG = f"main_AS/{exam_id}/{subject_id}/{student_id}/{qid}/studentanswer.jpeg"
        path_local_JPEG = "studentanswer.jpeg"
        
        path_on_cloud_CSV = f"main_ES/{exam_id}/{subject_id}/{exam_id}-{subject_id}_data.csv"
        path_local_CSV = f"{exam_id}-{subject_id}_data.csv"
        #storing in the cloud
       
    
        flag = is_file_present(path_on_cloud_CSV,path_local_CSV)
         

        if flag == False:
            print("[-]Evaluation scheme is not present")
            dicts = {"AS_upload_status":False}
            return dicts
    
        elif flag == True:
            storage.child(path_on_cloud_CSV).download(path_local_CSV)
            
            df = pd.read_csv(path_local_CSV)
            
            qid_list = df['question_id'].to_list()


            #index = df[df['question_id'] == int(qid)].index

            

            print(qid_list)
            if qid[0] == 0:
                qid = qid[1:]
                
            if qid not in str(qid_list):
                print("[-]Question ID is not pesent")
                return dicts

            storage.child(path_on_cloud_PDF).put(path_local_PDF)
            storage.child(path_on_cloud_JPEG).put(path_local_JPEG)

            
            #index_list= df(df['question_id'] == qid).index
            #df.drop(index,axis=0,inplace=True)

            #df = df._append(dicts,ignore_index=True)
            #print(df)
            #json_data = df.to_json()
            #df.to_csv(path_local_CSV,index=False)

            #storage.child(path_on_cloud_CSV).put(path_local_CSV)
           
 

            print("[+]Files finished uploading") 
        
        
        return {"AS_upload_status": True}
    except Exception as e:
        print(f"[-]Error during uploading : {str(e)}")
        return {"AS_upload_status": False}



        

    

        
        
            








@as_upload_router.post('/evaluate/asupload')
async def AS_upload(exam_id:str,subject_id:str,student_id:str,q_id:str,ES: UploadFile = File()):
    
    
    file_one_path = save_upload_file(ES, Path(f"studentanswer.pdf"))
    

    json_data = uploadfile_main(exam_id,subject_id,file_one_path,q_id,student_id)
    
    
    #print(f"{file_one_path},,{file_two_path}")
    delete_file(file_one_path)
    delete_file("studentanswer.jpeg")

    #delete_file(f"{exam_id}-{subject_id}_data.csv")

    # delete_file(f"{exam_id}-{subject_id}_data.csv")
    
    
    
    #return result
    

    #json_data=json.dumps(result)

    
    return json_data





















