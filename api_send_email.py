# api_send_email.py
# for internal use only

from mailjet_rest import Client
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("MJ_API_PUBLIC")
api_secret = os.getenv("MJ_API_SECRET")
if not api_key or not api_secret:
    raise RuntimeError("Check if API keys are copied to .env")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_email(to_email, to_name, subject, htmlpart, textpart=""): 
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "hamchiu.zhang14488-biph@basischina.com",
                    "Name": "BIPH NHS Treasury"
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_name
                    }
                ],
                "Subject": subject,
                "TextPart": textpart,
                "HTMLPart": htmlpart
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result.json()["Messages"][1]["Status"], result.status_code