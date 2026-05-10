from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DOMAIN_KEYWORDS = {
    "Tech": [
        "developer", "software", "engineer", "python", "java", "web", "frontend",
        "backend", "full stack", "data analyst", "machine learning", "it", "tester"
    ],
    "Commerce": [
        "accountant", "bank", "finance", "gst", "tax", "auditor", "clerk",
        "accounts", "cashier", "billing"
    ],
    "Management": [
        "hr", "marketing", "sales", "manager", "business development",
        "executive", "operations", "customer support"
    ],
    "Science": [
        "lab", "research", "chemist", "biology", "physics", "analyst",
        "scientist", "technician"
    ],
    "Government": [
        "ssc", "railway", "upsc", "bpsc", "bank", "clerk", "officer",
        "assistant", "stenographer", "constable", "government", "data entry"
    ]
}

INTERNSHIP_KEYWORDS = [
    "intern", "internship", "trainee", "apprentice", "apprenticeship",
    "fresher internship", "summer internship", "winter internship"
]

PRIVATE_JOB_EXCLUDE_KEYWORDS = [
    "intern", "internship", "trainee", "apprentice", "apprenticeship"
]


def normalize_jobs(jobs, source_name):
    normalized = []
    for job in jobs:
        title = str(job.get("title", "")).strip()
        if not title:
            continue

        normalized.append({
            "title": title,
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "experience": job.get("experience", ""),
            "description": job.get("description", ""),
            "link": job.get("link", ""),
            "source": job.get("source", source_name)
        })
    return normalized


def _job_search_text(job):
    return " ".join([
        str(job.get("title", "")),
        str(job.get("company", "")),
        str(job.get("location", "")),
        str(job.get("experience", "")),
        str(job.get("description", "")),
        str(job.get("link", "")),
        str(job.get("source", ""))
    ]).lower()


def is_internship_job(job):
    text = _job_search_text(job)
    return any(keyword in text for keyword in INTERNSHIP_KEYWORDS)


def split_private_and_internship_jobs(jobs):
    """Separate Adzuna/JSearch results into private jobs and internships."""
    private_jobs = []
    internship_jobs = []
    seen_private = set()
    seen_internship = set()

    for job in jobs:
        title = str(job.get("title", "")).strip()
        link = str(job.get("link", "")).strip()
        unique_key = (title.lower(), link.lower())

        if is_internship_job(job):
            if unique_key not in seen_internship:
                internship_jobs.append(job)
                seen_internship.add(unique_key)
        else:
            text = _job_search_text(job)
            if not any(keyword in text for keyword in PRIVATE_JOB_EXCLUDE_KEYWORDS):
                if unique_key not in seen_private:
                    private_jobs.append(job)
                    seen_private.add(unique_key)

    return private_jobs, internship_jobs


def match_jobs_advanced(skills, jobs, domain="General"):
    if not jobs:
        return []

    jobs = [job for job in jobs if job.get("title")]
    if not jobs:
        return []

    profile_text = " ".join(skills).lower().strip()
    if not profile_text:
        profile_text = domain.lower()

    job_texts = []
    for job in jobs:
        text = " ".join([
            str(job.get("title", "")),
            str(job.get("company", "")),
            str(job.get("location", "")),
            str(job.get("experience", "")),
            str(job.get("description", ""))
        ]).lower()
        job_texts.append(text)

    corpus = job_texts + [profile_text]

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    except Exception:
        similarities = [0.0] * len(jobs)

    ranked_jobs = []

    for i, job in enumerate(jobs):
        job_text = job_texts[i]

        tfidf_score = float(similarities[i]) * 100
        skill_bonus = 0
        domain_bonus = 0

        for skill in skills:
            if skill.lower() in job_text:
                skill_bonus += 6

        if domain in DOMAIN_KEYWORDS:
            for keyword in DOMAIN_KEYWORDS[domain]:
                if keyword in job_text:
                    domain_bonus += 8

        final_score = min(round(tfidf_score + skill_bonus + domain_bonus, 2), 100.0)

        ranked_job = job.copy()
        ranked_job["score"] = final_score
        ranked_jobs.append(ranked_job)

    ranked_jobs.sort(key=lambda x: x["score"], reverse=True)
    return ranked_jobs[:15]
