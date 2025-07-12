import whisper
import openai
import json
import os
import re

# Set your OpenAI API key here or via environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up OpenAI client (uses OPENAI_API_KEY from env)
client = openai.OpenAI()

# Company criteria (for prompt reference)
NOTICE_PERIOD_RANGE = (0, 60)  # days
HIKE_RANGE = (10, 20)  # percent
PREFERRED_WORK_MODE = "hybrid"


def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]


def extract_answers_with_llm(transcript):
    prompt = f"""
You are an assistant that extracts structured information from interview transcripts.
Given the following transcript, extract the following fields as JSON:
- willing_to_relocate (yes/no/unclear)
- notice_period_days (number or 'unclear')
- preferred_work_mode (hybrid/remote/onsite/unclear)
- current_ctc_lpa (number or 'unclear')
- expected_ctc_lpa (number or 'unclear')
- technical_knowledge: Analyze the candidate's answers to any technical questions (e.g., about databases, programming, system design, etc.) and provide a score from 0 to 100, along with a brief explanation. If no technical questions are present, set score to 0 and explanation to "No technical questions found."

Example:
Transcript:
AI: What are your current salary and your expectations for the new role?
Candidate: My current CTC is 14 LPA, and I’m expecting around 18–20 LPA, depending on the role and responsibilities.
AI: How will you analyse DB performance issue?
Candidate: I would start by checking slow queries, indexing, and monitoring resource usage. Tools like EXPLAIN in SQL help identify bottlenecks.

JSON:
{{
  "willing_to_relocate": "unclear",
  "notice_period_days": "unclear",
  "preferred_work_mode": "unclear",
  "current_ctc_lpa": 14,
  "expected_ctc_lpa": 18,
  "technical_knowledge": {{"score": 85, "explanation": "Candidate gave a good overview of DB performance analysis, mentioning slow queries, indexing, and monitoring."}}
}}

Now, for this transcript:
{transcript}

Return only the JSON.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    # Remove markdown code block if present
    if content.startswith("```json"):
        content = re.sub(r"^```json", "", content).strip()
    if content.startswith("```"):
        content = re.sub(r"^```", "", content).strip()
    if content.endswith("```"):
        content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except Exception as e:
        print("[ERROR] Could not decode LLM response as JSON. Raw response:")
        # print(content)
        raise e


def score_candidate_with_llm(extracted_answers):
    prompt = f"""
You are an HR assistant. Given the candidate's answers and the company criteria, score the candidate from 0 to 100 and recommend whether to move to the next round.

Company criteria:
- Notice period: 0-60 days
- Hike on current CTC: 10%-20%
- Preferred work mode: hybrid
- Technical knowledge is important for this role and should be reflected in the overall score.

Candidate answers:
{extracted_answers}

Return a JSON with:
- score (0-100)
- recommendation ("move to next round" or "reject")
- brief_reason
- technical_knowledge (repeat the technical_knowledge score and explanation from above)

Return only the JSON.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    # Remove markdown code block if present
    if content.startswith("```json"):
        content = re.sub(r"^```json", "", content).strip()
    if content.startswith("```"):
        content = re.sub(r"^```", "", content).strip()
    if content.endswith("```"):
        content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except Exception as e:
        print("[ERROR] Could not decode LLM response as JSON. Raw response:")
        # print(content)
        raise e


def process_audio_interview(audio_path):
    transcript = transcribe_audio(audio_path)
    extracted = extract_answers_with_llm(transcript)
    result = score_candidate_with_llm(extracted)
    return {
        "transcript": transcript,
        "extracted_answers": extracted,
        "scoring_result": result
    }

# Example usage (uncomment to use):
# result = process_audio_interview("sample_interview.mp3")
# print(json.dumps(result, indent=2)) 