import spacy
import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. LOAD THE CUSTOM DOMAIN BRAIN ---
def load_ai_and_database():
    print("Loading AI and Custom Tech Skills Database into memory...")
    nlp = spacy.load("en_core_web_sm")
    
    # Pointing to the custom Data Engineering/Tech database you created
    db_path = "data/tech_skills_db.json"
    skills_list = []
    
    # We use a safe fallback in case the database folder hasn't been moved over yet
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            skills_list = json.load(f)
            
    # We now return the raw list of skills instead of the fragile PhraseMatcher
    return nlp, skills_list

# Initialize the AI (In FastAPI, this runs safely once when the server boots)
nlp, skills_list = load_ai_and_database()

# --- 2. THE SCORING ALGORITHM ---
def calculate_match_score(cleaned_resume, cleaned_jd):
    """Calculates the mathematical overlap score (0-100%)."""
    if not cleaned_resume or not cleaned_jd: 
        return 0.0
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    return round(similarity * 100, 2)

# --- 3. THE SKILL EXTRACTOR (BULLETPROOF EDITION) ---
def extract_skills(text):
    """Scans raw text using Regex to bypass Spacy tokenization bugs."""
    text_lower = text.lower()
    found_skills = set()
    
    for skill in skills_list:
        # \b ensures we only match whole words (so "C" doesn't match inside "Mac")
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        
        if re.search(pattern, text_lower):
            # We add the ORIGINAL capitalized skill from the database, not the lowercase version
            found_skills.add(skill)
            
    return found_skills

# --- 4. THE GAP ANALYZER ---
def get_missing_keywords(raw_resume, raw_jd):
    """Finds required skills in the JD that are missing from the Resume."""
    jd_skills = extract_skills(raw_jd)
    resume_skills = extract_skills(raw_resume)
    
    # Pure mathematical subtraction (JD skills minus Resume skills)
    missing = jd_skills.difference(resume_skills)
    
    # We removed .title() so it outputs exact matches like "PostgreSQL" and "AWS"
    return list(missing)[:10]