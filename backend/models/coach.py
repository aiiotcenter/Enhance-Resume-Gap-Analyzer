import spacy
import os
import random
import json
import time
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- BULLETPROOF .ENV LOADER ---
# This forces Python to look in the EXACT directory, overriding any stuck memory keys
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# Initialize the Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load the grammar engine
nlp = spacy.load("en_core_web_sm")

WEAK_VERBS = {
    "help", "work", "responsible", "task", "assist", "handle", 
    "participate", "contribute", "support", "do", "make"
}

METRIC_WARNINGS = [
    "⚠️ **Missing Metric:** Quantify your impact! Add numbers (e.g., 'saved 10 hours', 'increased revenue by 15%').",
    "⚠️ **Where is the data?** Hiring managers love numbers. Estimate the scale of your work or the percentage of improvement.",
    "⚠️ **Lacks Quantifiable Results:** Did this save time? Did it make money? Add a specific metric to prove your success."
]

def extract_experience_bullets(raw_text):
    """API CALL 1: Extracts the bullets deterministically."""
    prompt = f"""
    You are an expert resume parser. Read the following resume text.
    Extract ONLY the bullet points that describe accomplishments in the "Work Experience" or "Projects" sections.
    Completely IGNORE the Professional Summary, Skills list, Education, and Contact Info.
    
    CRITICAL INSTRUCTIONS:
    1. Return a JSON array of strings ONLY. Do not wrap it in a dictionary.
    2. You MUST copy the text exactly word-for-word from the resume. Do not alter a single character, punctuation mark, or letter case.
    
    Resume Text:
    {raw_text}
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0, 
                )
            )
            if not response.text:
                return ["API_ERROR: Google Gemini returned an empty response."]
            
            extracted = json.loads(response.text)
            
            if isinstance(extracted, dict):
                for val in extracted.values():
                    if isinstance(val, list):
                        return val
                return ["API_ERROR: Unexpected JSON structure."]
                
            return extracted
        except Exception as e:
            error_str = str(e)

            print("\n" + "!"*50)
            print(f"🔑 KEY CHECK: {str(os.getenv('GEMINI_API_KEY'))[:10]}...")
            print(f"🚨 REAL ERROR: {error_str}")
            print("!"*50 + "\n")

            if ("503" in error_str or "429" in error_str) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return [f"API_ERROR: {error_str}"]

def batch_rewrite_bullets(bad_bullets_list, jd_text):
    """API CALL 2: The Batcher! Rewrites ALL bad bullets in ONE single request!"""
    if not bad_bullets_list:
        return []
        
    bullets_text = "\n".join([f"{i+1}. {b}" for i, b in enumerate(bad_bullets_list)])
        
    prompt = f"""
    You are an expert executive resume writer. 
    Here is a Job Description: "{jd_text[:1000]}"
    
    Here are {len(bad_bullets_list)} poorly written resume bullet points.
    Rewrite EACH bullet point to be highly impactful, using industry-standard "key expressions" from the job description.
    
    CRITICAL INSTRUCTION 1: You MUST return a JSON array of strings containing exactly {len(bad_bullets_list)} rewritten bullet points, corresponding to the input order. Do NOT wrap it in a dictionary.
    
    CRITICAL INSTRUCTION 2: If the original bullet point does NOT contain a measurable metric (like a percentage, dollar amount, or time saved), you MUST generate and insert a realistic, conservative metric into your rewrite (e.g., "by 15%", "by 20%", or "saving 10 hours per week"). Make the number sound highly plausible for the described task. Do not use placeholders.
    
    Original Bullets:
    {bullets_text}
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7, 
                )
            )
            
            rewrites = json.loads(response.text)
            
            if isinstance(rewrites, dict):
                for val in rewrites.values():
                    if isinstance(val, list):
                        rewrites = val
                        break
            
            if not isinstance(rewrites, list) or len(rewrites) != len(bad_bullets_list):
                return ["API Formatting Error: Could not generate perfect rewrite."] * len(bad_bullets_list)
                
            return rewrites
        except Exception as e:
            error_str = str(e)
            if ("503" in error_str or "429" in error_str) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return [f"API Rewrite Error: {error_str}"] * len(bad_bullets_list)

def get_resume_feedback(raw_text, jd_text):
    """The Main Engine Pipeline."""
    extracted_lines = extract_experience_bullets(raw_text)
    
    if extracted_lines and isinstance(extracted_lines[0], str) and "API_ERROR" in extracted_lines[0]:
        return {f"⚠️ Parse Error": [extracted_lines[0]]}
        
    bad_bullets = []
    bullet_issues = {}
    
    for line in extracted_lines:
        clean_line = line.strip().lstrip('•-* ')
        if len(clean_line) < 20:
            continue
            
        doc = nlp(clean_line)
        issues = []
        
        has_metric = any(token.like_num or token.text in ["%", "$"] for token in doc)
        if not has_metric:
            issues.append(random.choice(METRIC_WARNINGS))
            
        first_verb = None
        for token in doc:
            if token.pos_ == "VERB":
                first_verb = token
                break
                
        if first_verb and first_verb.lemma_.lower() in WEAK_VERBS:
            issues.append(f"❌ **Weak Verb ('{first_verb.text}'):** This sounds passive. Upgrade to a stronger action verb.")
            
        if issues:
            bad_bullets.append(clean_line)
            bullet_issues[clean_line] = issues

    if bad_bullets:
        rewrites = batch_rewrite_bullets(bad_bullets, jd_text)
        
        for i, bullet in enumerate(bad_bullets):
            rewrite_text = rewrites[i] if i < len(rewrites) else "Rewrite failed."
            bullet_issues[bullet].append(f"💡 **Suggested Rewrite:** {rewrite_text}")
            
    return bullet_issues

def generate_micro_objective(raw_resume, jd_text):
    """Generates a highly tailored 1-2 sentence Micro-Objective."""
    prompt = f"""
    You are an expert executive recruiter. 
    Read the following Job Description and the Candidate's Resume.
    
    Job Description:
    {jd_text[:2000]}
    
    Resume:
    {raw_resume[:2000]}
    
    TASK:
    Generate a single, highly tailored "Micro-Objective" sentence that the candidate can put at the very top of their resume. 
    It MUST start with "🎯 Why This Role: " (try to guess the company name if possible, e.g., "🎯 Why This Role at Tesla: ").
    Connect the candidate's strongest technical skill directly to the company's core mission or a specific requirement in the job description.
    Keep it under 40 words. Do NOT wrap it in quotes.
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7 
                )
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if ("503" in error_str or "429" in error_str) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return ""
    return ""