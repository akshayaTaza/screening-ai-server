from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import sys
from PyPDF2 import PdfReader
import logging

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.calculate_score import calculate_score
from utils.twillio_call import initiate_call
from utils.twillio_call import process_call

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = '../data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/calculate_score', methods=['POST'])
def calculate():
    logger.info("Received POST request to /calculate_score")
    logger.info(f"Request files: {list(request.files.keys())}")
    
    # Check if files are present
    if 'resume' not in request.files or 'jd' not in request.files:
        logger.error(f"Missing files. Available files: {list(request.files.keys())}")
        return jsonify({"error": "Missing files"}), 400

    resume_file = request.files['resume']
    jd_file = request.files['jd']
    
    logger.info(f"Resume file: {resume_file.filename}, size: {resume_file.content_length if hasattr(resume_file, 'content_length') else 'unknown'}")
    logger.info(f"JD file: {jd_file.filename}, size: {jd_file.content_length if hasattr(jd_file, 'content_length') else 'unknown'}")

    if resume_file.filename == '' or jd_file.filename == '':
        logger.error(f"Empty filename. Resume: '{resume_file.filename}', JD: '{jd_file.filename}'")
        return jsonify({"error": "Empty file uploaded"}), 400

    # Secure filenames
    resume_filename = secure_filename(resume_file.filename)
    jd_filename = secure_filename(jd_file.filename)
    
    logger.info(f"Secure filenames - Resume: {resume_filename}, JD: {jd_filename}")

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
    jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_filename)

    # Save files temporarily
    resume_file.save(resume_path)
    jd_file.save(jd_path)
    
    logger.info(f"Files saved - Resume: {resume_path}, JD: {jd_path}")

    try:
        # Read resume file
        if resume_filename.lower().endswith('.pdf'):
            logger.info("Reading resume as PDF")
            with open(resume_path, 'rb') as r:
                reader = PdfReader(r)
                resume_text = " ".join(page.extract_text() or '' for page in reader.pages)
        else:
            logger.info("Reading resume as text")
            with open(resume_path, 'r', encoding='utf-8') as r:
                resume_text = r.read()
        # Read JD file
        if jd_filename.lower().endswith('.pdf'):
            logger.info("Reading JD as PDF")
            with open(jd_path, 'rb') as j:
                reader = PdfReader(j)
                jd_text = " ".join(page.extract_text() or '' for page in reader.pages)
        else:
            logger.info("Reading JD as text")
            with open(jd_path, 'r', encoding='utf-8') as j:
                jd_text = j.read()
    except Exception as e:
        logger.error(f"Error reading files: {str(e)}")
        # Optionally delete uploaded files if error occurs
        if os.path.exists(resume_path):
            os.remove(resume_path)
        if os.path.exists(jd_path):
            os.remove(jd_path)
        return jsonify({"error": f"Failed to parse uploaded files: {str(e)}"}), 400

    # Call your scoring function
    result = calculate_score(resume_text, jd_text)
    
    logger.info("Score calculation completed successfully")

    # Optionally delete uploaded files
    os.remove(resume_path)
    os.remove(jd_path)
    
    logger.info("Temporary files cleaned up")

    return jsonify(result), 200

@app.route('/start_call', methods=['POST'])
def start_call():
    try:
        # Call your Twilio logic
        call_response = initiate_call()

        return jsonify({"status": "success", "twilio_response": call_response}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/process_call', methods=['POST'])
def process_file():
    try:
        result = process_call()

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
