from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_skill_match(resume_skills, jd_skills):
    if not jd_skills:
        return 0.0  # or some other value or behavior you want
    return len(set(resume_skills) & set(jd_skills)) / len(set(jd_skills)) * 100

def compute_semantic_score(resume_text, jd_text):
    embeddings = model.encode([resume_text, jd_text], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
    return round(score * 100, 2)

def overall_fit_score(skill_score, experience_score, semantic_score):
    return round((0.5 * skill_score + 0.3 * experience_score + 0.2 * semantic_score), 2)