import time
import requests
import os
from twilio.rest import Client
import google.generativeai as genai
from .audio_screening import process_audio_interview
import json

# ----------------------------
# CONFIG
# ----------------------------
account_sid = 'ACcff9024a5adf75dce972b4c3e7a64b28'
auth_token = '3b35d56d53423a7fc0e0037731e7e020'
genai.configure(api_key='AIzaSyBertql-JOr6tXPMJXfsyzrYA8ZffDIbuE')

to_number = '+918754786877'
from_number = '+16605277223'
twiml_url = 'https://voicebotscreening-1486.twil.io/voicebot?questionIndex=0'

# Create data directory for recordings if it doesn't exist
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print("SCRIPT_DIR", {SCRIPT_DIR})

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
print("PROJECT_ROOT", {PROJECT_ROOT})

RECORDINGS_DIR = os.path.join(PROJECT_ROOT, "data", "recordings")
print("RECORDINGS_DIR", {RECORDINGS_DIR})


os.makedirs(RECORDINGS_DIR, exist_ok=True)

def initiate_call():
    """
    Initiates a Twilio call, waits for recording, downloads it, and processes it
    through the existing audio screening pipeline.
    """
    client = Client(account_sid, auth_token)

    print("📞 Initiating call...")
    call = client.calls.create(
        url=twiml_url,
        to=to_number,
        from_=from_number,
        record=True
    )

    print(f"✅ Call started. SID: {call.sid}")
    print("⏳ Waiting 180 seconds for recording to be ready...")
    time.sleep(180)  # Wait for recording to be processed

    # ----------------------------
    # STEP 2: DOWNLOAD RECORDING
    # ----------------------------
    recordings = client.recordings.list(call_sid=call.sid, limit=1)

    if not recordings:
        print("❌ No recording found.")
        return None

    recording = recordings[0]
    recording_url = f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
    # mp3_file = os.path.join(RECORDINGS_DIR, f"recording-{recording.sid}.mp3")
    mp3_file = os.path.join(RECORDINGS_DIR, f"recording.mp3")

    print(f"🎧 Recording URL: {recording_url}")

    response = requests.get(recording_url, auth=(account_sid, auth_token), stream=True)
    if response.status_code == 200:
        with open(mp3_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(f"✅ Recording saved as {mp3_file}")
    else:
        print(f"❌ Failed to download: {response.status_code}")
        return None

def process_call():
    # ----------------------------
    # STEP 3: PROCESS RECORDING
    # ----------------------------
    print("🔍 Processing audio through screening pipeline...")
    try:
        mp3_file = os.path.join(RECORDINGS_DIR, f"recording.mp3")
        print("mp3_file: ", {mp3_file})
        
        result = process_audio_interview(mp3_file)
        print("✅ Audio processing completed successfully!")
        return result
    except Exception as e:
        print(f"❌ Error processing audio: {str(e)}")
        return None