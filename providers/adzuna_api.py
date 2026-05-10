import requests

APP_ID = "ad67441b"
APP_KEY = "0b028e5321270b81cb83beef0691b1f4"


def get_adzuna_jobs(query):
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": query,
        "results_per_page": 20
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
    except Exception as e:
        print("Adzuna API Error:", e)
        return []

    jobs = []
    for j in data.get("results", []):
        jobs.append({
            "title": j.get("title", ""),
            "company": j.get("company", {}).get("display_name", ""),
            "location": j.get("location", {}).get("display_name", ""),
            "description": j.get("description", ""),
            "link": j.get("redirect_url", ""),
            "source": "Adzuna"
        })
    return jobs
