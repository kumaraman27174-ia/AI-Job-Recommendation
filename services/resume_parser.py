import os
import re
import PyPDF2

try:
    from docx import Document
except ImportError:
    Document = None


SKILL_DB = {
    "tech": [
        "python", "java", "c", "c++", "c#", "html", "css", "javascript",
        "typescript", "react", "node", "nodejs", "express", "flask", "django",
        "mysql", "sql", "mongodb", "php", "bootstrap", "tailwind", "git",
        "github", "api", "json", "machine learning", "data science", "ai",
        "nlp", "deep learning", "computer vision", "pandas", "numpy", "excel",
        "power bi", "tableau", "aws", "azure", "cloud", "testing"
    ],
    "commerce": [
        "accounting", "tally", "gst", "taxation", "finance", "banking",
        "auditing", "bookkeeping", "payroll", "cost accounting", "economics",
        "financial analysis", "ms excel", "sap"
    ],
    "management": [
        "marketing", "digital marketing", "sales", "hr", "human resource",
        "management", "leadership", "business development", "communication",
        "operations", "customer support", "customer handling", "team management"
    ],
    "science": [
        "biology", "chemistry", "physics", "mathematics", "lab work",
        "research", "statistics", "biotechnology", "microbiology",
        "environment science"
    ],
    "government": [
        "ssc", "bank", "banking exam", "railway", "upsc", "bpsc", "state pcs",
        "typing", "data entry", "reasoning", "general knowledge", "gk",
        "english", "quantitative aptitude", "aptitude", "current affairs",
        "computer basics", "stenography", "clerk", "office assistant",
        "constable", "patwari", "assistant", "officer"
    ],
    "general": [
        "teamwork", "problem solving", "decision making", "adaptability",
        "time management", "hardworking", "quick learner", "presentation"
    ]
}


def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        return ""


def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
    except Exception:
        return ""
    return clean_text(text)


def extract_text_from_docx(file_path):
    if Document is None:
        return ""

    try:
        doc = Document(file_path)
        text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])
        return clean_text(text)
    except Exception:
        return ""


def extract_skills(text):
    found_skills = set()
    text = clean_text(text)

    for _, skills in SKILL_DB.items():
        for skill in skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text):
                found_skills.add(skill)

    return sorted(found_skills)


def detect_domain(skills, qualification="", preferred_job_type="", govt_exam_target=""):
    skills_lower = [s.lower() for s in skills]
    q = qualification.lower()
    pjt = preferred_job_type.lower()
    govt_target = govt_exam_target.lower()

    if "government" in pjt or govt_target:
        return "Government"

    if any(x in q for x in ["bca", "mca", "b.tech", "btech", "computer", "it", "software"]):
        return "Tech"

    if any(x in q for x in ["bcom", "mcom", "commerce", "account", "finance"]):
        return "Commerce"

    if any(x in q for x in ["bba", "mba", "management", "business"]):
        return "Management"

    if any(x in q for x in ["bsc", "msc", "science", "physics", "chemistry", "biology", "math"]):
        return "Science"

    tech_hits = sum(1 for s in skills_lower if s in [x.lower() for x in SKILL_DB["tech"]])
    commerce_hits = sum(1 for s in skills_lower if s in [x.lower() for x in SKILL_DB["commerce"]])
    management_hits = sum(1 for s in skills_lower if s in [x.lower() for x in SKILL_DB["management"]])
    science_hits = sum(1 for s in skills_lower if s in [x.lower() for x in SKILL_DB["science"]])
    govt_hits = sum(1 for s in skills_lower if s in [x.lower() for x in SKILL_DB["government"]])

    domain_scores = {
        "Tech": tech_hits,
        "Commerce": commerce_hits,
        "Management": management_hits,
        "Science": science_hits,
        "Government": govt_hits
    }

    best_domain = max(domain_scores, key=domain_scores.get)
    return best_domain if domain_scores[best_domain] > 0 else "General"