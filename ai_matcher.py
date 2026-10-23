import re

SYNONYMS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "reactjs": "react",
    "vuejs": "vue",
    "spring": "spring boot",
    "springboot": "spring boot",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "bi": "business intelligence",
    "powerbi": "power bi",
    "cv": "computer vision",
    "rest": "rest api",
    "restful": "rest api"
}


def normalize_skill(skill: str) -> str:
    cleaned = re.sub(r"[^\w\s\+\#]", " ", skill).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return SYNONYMS.get(cleaned, cleaned)


def parse_skills(skills_input) -> set:
    if isinstance(skills_input, list):
        items = skills_input
    elif isinstance(skills_input, str):
        # Split by comma or semicolon or newline
        items = re.split(r"[,;\n|]", skills_input)
    else:
        items = []

    result = set()
    for item in items:
        norm = normalize_skill(item)
        if norm:
            result.add(norm)
    return result


def compute_ai_match(candidate_skills_raw: str, job_skills_raw: str, candidate_location: str = "", job_location: str = "") -> dict:
    cand_skills = parse_skills(candidate_skills_raw)
    job_skills = parse_skills(job_skills_raw)

    if not job_skills:
        return {
            "match_score": 100,
            "matching_skills": list(cand_skills),
            "missing_skills": [],
            "match_level": "Exceptional Match",
            "is_local_match": True
        }

    # Intersect skills
    matched_skills_set = cand_skills.intersection(job_skills)
    missing_skills_set = job_skills - cand_skills

    # Skill overlap ratio (0.0 to 1.0)
    skill_ratio = len(matched_skills_set) / len(job_skills)
    skill_score = skill_ratio * 80.0

    # Local talent boost (up to 20%)
    c_loc = candidate_location.strip().lower()
    j_loc = job_location.strip().lower()

    is_local = False
    if c_loc and j_loc and (c_loc in j_loc or j_loc in c_loc):
        loc_score = 20.0
        is_local = True
    elif c_loc and j_loc:
        loc_score = 8.0  # general region
    else:
        loc_score = 10.0

    final_score = int(min(100, round(skill_score + loc_score)))

    # Determine match level
    if final_score >= 90:
        level = "Exceptional Match"
    elif final_score >= 75:
        level = "Strong Match"
    elif final_score >= 55:
        level = "Good Match"
    else:
        level = "Moderate Match"

    # Human-readable skill titles
    matching_list = [s.title() for s in matched_skills_set]
    missing_list = [s.title() for s in missing_skills_set]

    return {
        "match_score": final_score,
        "matching_skills": matching_list,
        "missing_skills": missing_list,
        "match_level": level,
        "is_local_match": is_local
    }
