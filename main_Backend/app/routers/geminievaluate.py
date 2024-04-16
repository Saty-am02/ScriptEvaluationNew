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


geminiEvaluate_api_router = APIRouter()


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
        "databaseURL":"https://scriptevaluation-default-rtdb.firebaseio.com",
        "serviceAccount":"KEYS/firebase_cred.json"
        }
    
    
    


    firebase = pyrebase.initialize_app(cred)
    storage = firebase.storage()
    database = firebase.database()


except Exception as e:
        print(f"[-]Error during importing of pyrebase at geminiEvaluate.py : {str(e)}")
        



def is_file_present(file_path_cloud,file_path_local):
    try:
        file  = storage.child(file_path_cloud).download(file_path_local)
        #delete_file(file_path_local)

        print(f"[+]File Present at :  {file_path_cloud} ")
        return True
    except Exception as e:
        print(f"[-]Evaluation scheme is not present at {file_path_cloud} file not present: {e}")
        return False




def delete_file(filename):
    try:
        os.remove(filename)
    except:
        print("[-]File cannot be deleted as it is not present")



def evaluatemarks(ES_path,AS_path,question,max_marks):

    expectedAnswer = Image.open(ES_path)
    studentAnswer = Image.open(AS_path)

    response = model_vision.generate_content(
            [
                f"The images below are the Expected answer and the student given answer for the question : {str(question)} and the expected answer is {expectedAnswer}, please Evaluate them and give me the marks ,the maxomum mark is {str(max_marks)},just give me the mark as a single value,no explanation or sorry message required",
                studentAnswer,
            ]
        )
    print("[#]this is max marks in gemini : "+str(max_marks))
    
    text = response.text
    print(f"[#]marks awarded in gemini:{text}")


    return text









def geminiEvaluate_main(exam_id,subject_id):
    extracted_text = ""
    additional_points = ""
    image_string = ""
    try:
        print('[+]Evaluating...')
        

        path_on_cloud_CSV = f"main_ES/{exam_id}/{subject_id}/{exam_id}-{subject_id}_data.csv"
        path_local_CSV = f"{exam_id}-{subject_id}_data.csv"
        flag = is_file_present(path_on_cloud_CSV,path_local_CSV)
        
        if flag == False:
            print("[-]Evaluation scheme is not present")
            dicts = {"geminiEvaluate_status":False}
            return dicts


        elif flag == True:

            #es_JPEGpath = Image.open(f"studentanswer.jpeg")
 
 # Extract qid names from the csv
       
            storage.child(path_on_cloud_CSV).download(path_local_CSV)
            df = pd.read_csv(path_local_CSV)
            df.sort_values(by=['question_id'])
            qid_list = df['question_id'].to_list()

# Extract document names from the response
            

            path_on_cloud_SD = f"student_data/{exam_id}/{subject_id}/{exam_id}-{subject_id}_studentdata.csv"
            path_local_SD = f"{exam_id}-{subject_id}_studentdata.csv"


            storage.child(path_on_cloud_SD).download(path_local_SD)

            studentID_df = pd.read_csv(path_local_SD)

            all_student_id = studentID_df["student_id"].to_list()
            
#checking is all student files are uploaded
            
            print("[#]this is all student ids : " +' '.join(str(e) for e in all_student_id))
            print("[#]This is all qids        : "+ ' '.join(str(e) for e in qid_list))
            for stu_id in all_student_id:
                for q_id in qid_list:
            
                    path_on_cloud_AS = f"main_AS/{exam_id}/{subject_id}/{stu_id}/{q_id}/studentanswer.jpeg"
                    path_local_AS = "studentanswer.jpeg"

                    flag_AS = is_file_present(path_on_cloud_AS,path_local_AS)

                    if flag_AS == False:
                        print("[-]Not All Files are uploaded")
                        dicts = {"geminiEvaluate_status":False}
                        return dicts

                

            main_dicts = {"exam_id":exam_id,"subject_id":subject_id}
            
            
            for stu_id in all_student_id:
                temp_dicts = {}
                for q_id in qid_list:
                    path_on_cloud_AS = f"main_AS/{exam_id}/{subject_id}/{stu_id}/{q_id}/studentanswer.jpeg"
                    path_local_AS = "studentanswer.jpeg"

 
                    path_on_cloud_ES = f"main_ES/{exam_id}/{subject_id}/{q_id}/expectedanswer.jpeg"
                    path_local_ES = "expectedanswer.jpeg"

                    
                    storage.child(path_on_cloud_ES).download(path_local_ES)
                    storage.child(path_on_cloud_AS).download(path_local_AS)
                    


                    question = df[df["question_id"]==q_id]["question"].to_numpy()[0] 
                    max_marks = df[df["question_id"]==q_id]["max_marks"].to_numpy()[0]
                   
                    #print("[#]i am question type: "+str(type(question)))
                    #print("[#]i am max marks type: "+str(type(max_marks)))

                    

                    print("[#]i am question : "+str(question))
                    print("[#]i am max marks: "+str(max_marks))
                    
                    marks_awarded = evaluatemarks(path_local_ES,path_local_AS,str(question),str(max_marks))
                    marks_awarded = marks_awarded.replace(" ","") 
                    print(f"{marks_awarded}")
                     
                    temp_dicts[q_id] = marks_awarded
           
                
                main_dicts.update({stu_id:temp_dicts})                         
                 

         

                    
        
                       
            

            #index = df[df['question_id'] == int(qid)].index

            

            
            #index_list= df(df['question_id'] == qid).index
            #df.drop(index,axis=0,inplace=True)

            #df = df._append(dicts,ignore_index=True)
            #print(df)
            #json_data = df.to_json()
            #df.to_csv(path_local_CSV,index=False)

            #storage.child(path_on_cloud_CSV).put(path_local_CSV)
           
 
            path_on_cloud_JSON = f"main_result/{exam_id}/{subject_id}/{exam_id}-{subject_id}_results.json"
            path_local_JSON = f"{exam_id}-{subject_id}_results.json"
            print("[+]Files Evaluating Finished")
            with open(path_local_JSON, 'w') as fp:
                json.dump(main_dicts, fp)
                fp.close()
            print(f"[+]Uploading the results and data at : {path_on_cloud_JSON}")
            storage.child(path_on_cloud_JSON).put(path_local_JSON)


        
        print(main_dicts)
        return main_dicts
    except Exception as e:
        print(f"[-]Error during Evaluating : {str(e)}")
        return {"geminiEvaluate_status": False,"Error": str(e)}



        

    

        
        
            







def cleanup(exam_id,subject_id):

    print("[@.]CLEANING UP")
    #delete_file("expectedanswer.jpeg")
    #delete_file("studentanswer.jpeg")
    #delete_file(f"{exam_id}-{subject_id}_data.csv")
    #delete_file(f"{exam_id}-{subject_id}_studentdata.csv")
    #delete_file(f"{exam_id}-{subject_id}_results.json")
    print("[@+]CLEANING UP DONE!")



@geminiEvaluate_api_router.post('/evaluate/geminiEvaluate')
async def geminiEvaluate(exam_id:str,subject_id:str):
    
    
    

    json_data = geminiEvaluate_main(exam_id,subject_id)
    
    cleanup(exam_id,subject_id)
        
    
    
    #return result
    

    #json_data=json.dumps(result)

    
    return json_data






















