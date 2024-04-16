import spacy
from google.cloud import vision
from google.cloud.vision_v1 import types
from google.oauth2 import service_account
import google.generativeai as genai
import docx2txt
import PIL.Image


GEMINI_API = "AIzaSyAPpvH6HwOg5DnW-FqaqcmJWRV8lbWnKUk"

generation_config = {
        "temperature":0,
        "top_p":1,
        "top_k":1,
        "max_output_tokens":1,
    }

safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        },
    ]



def gemini_grading(student_ans,right_ans,max_marks):
    genai.configure(api_key=GEMINI_API)
    model = genai.GenerativeModel(model_name = 'gemini-pro',safety_settings=safety_settings)

    template = f"""The student answer is '{student_ans}' ; and the expected answer by the teacher is '{right_ans}'; now evaluate the answer of the student by using the expected answer of the teacher as the template and give back  the mark out of {max_marks} , Give me only the mark, no other explanation or suggestion or sorry message or any alternatives"""

    marks = model.generate_content(template).text
    return marks
    




def evaluate_the_AnswerScript_gemini(image_paths):
    extracted_text = ""
    try:
        for i in image_paths:
            img = PIL.Image.open(i)
            genai.configure(api_key=GEMINI_API)
            model_vision = genai.GenerativeModel('gemini-pro-vision')

            response =  model_vision.generate_content(["Extract the text in this image, do not include stricked out lines", img])
        
            extracted_text += response.text

        print(extracted_text)
        
     
   
        answer_scheme = docx2txt.process("C:/Ganglia/ScriptEvaluationNew/basic_prototype/app/uploads/testEval.docx")
        # print(answer_scheme)

        max_marks='10'

        awaded_marks = gemini_grading(extracted_text,answer_scheme,max_marks)
        print("")
        print("The marks awarded to the student is : "+awaded_marks) 

    
    except Exception as e:
            print(f"Error during batch document text detection: {str(e)}")

# Replace 'your_image_paths' with a list of paths to your image files
image_paths = [
    r'C:/Ganglia/ScriptEvaluationNew/basic_prototype/app/uploads/Answer1.png',
# Add more paths as needed
]

# Replace 'path/to/your/keyfile.json' with the actual path to your Google Cloud service account key JSON file
#credentials_path = '/home/tamil/keys/unused/script-evaluation-a41aac110e2b.json'

#main call for detecting the handwriting via the Google.vesion
#batch_detect_handwriting(image_paths, credentials_path)
evaluate_the_AnswerScript_gemini(image_paths)

