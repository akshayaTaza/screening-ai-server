import os
import sys
# from parser import extract_text_from_pdf
from .llm_mapper import extract_structured_data
from .scorer import compute_skill_match, compute_semantic_score, overall_fit_score
from dotenv import load_dotenv
import json
# Add import for audio screening
from .audio_screening import process_audio_interview
# Add import for Twilio call functionality
from .twillio_call import initiate_call_and_process
load_dotenv()

RESUME_PATH = "/Users/tazapay/Hackathon/Parser/v2/ai-screener-backend//data/resumes/ResumeQA.pdf"
JD_PATH = "/Users/tazapay/Hackathon/Parser/v2/ai-screener-backend/data/job_descriptions/JD_QA.pdf"

RESUME_PROMPT = """
Extract the following fields from this resume:
- Full Name
- Email
- Phone Number
- LinkedIn URL
- Skills
- Languages
- Certifications
- Education (degree, institution, year)
- Experience (role, company, duration in years, description)
- Projects (name, description, technologies)
- Achievements
- Publications
- Summary
Return only JSON.
"""

JD_PROMPT = """
Extract the following fields from this job description:
- Title
- Department
- Company Name
- Company Description
- Required Skills
- Minimum Experience Years
- Location
- Reporting To
- Salary Range
- Employment Type
- Benefits
- Application Deadline
Return only JSON.
"""

def calculate_score(resume_text, jd_text):
    # LLM extraction
    resume_struct = extract_structured_data(RESUME_PROMPT, resume_text)
    jd_struct = extract_structured_data(JD_PROMPT, jd_text)

    print("Extracted Resume JSON:")
    print(json.dumps(resume_struct, indent=2))
    print("Extracted JD JSON:")
    print(json.dumps(jd_struct, indent=2))

    # LLM-based scoring and analysis
    scoring_prompt = f'''
You are an expert HR analyst. Given the following two JSON objects, one representing a candidate's resume and the other a job description, analyze and score the candidate's fit for the job.

Instructions:
- Carefully compare the candidate's skills, experience, location, and other relevant fields to the job requirements.
- For each of the following categories, provide a score from 0 to 100, and a brief explanation:
  - skills_match: How well do the candidate's skills match the required skills?
  - experience_match: How well does the candidate's experience (years, roles, industries) match the job requirements?
  - location_match: How suitable is the candidate's location (or willingness to relocate/remote) for the job's location. Check if the candidate is of closer proximity, and give some score there too?
  - overall_fit: Your overall assessment of the candidate's fit for the job, considering all factors.
- Also, list the matched_skills and missing_skills.
- If possible, mention any other relevant observations (e.g., certifications, projects, language proficiency, etc.).
- Return your analysis as a JSON object in the following format:

{{
  "skills_match": {{
    "score": <number>,
    "explanation": "<string>"
  }},
  "experience_match": {{
    "score": <number>,
    "explanation": "<string>"
  }},
  "location_match": {{
    "score": <number>,
    "explanation": "<string>"
  }},
  "overall_fit": {{
    "score": <number>,
    "explanation": "<string>"
  }},
  "matched_skills": [<list of strings>],
  "missing_skills": [<list of strings>],
  "other_observations": "<string>"
}}

Resume JSON:
{json.dumps(resume_struct, ensure_ascii=False)}

Job Description JSON:
{json.dumps(jd_struct, ensure_ascii=False)}
'''

    analysis = extract_structured_data(scoring_prompt, "")
    print("\nLLM Analysis and Scoring:")
    print(json.dumps(analysis, indent=2))
