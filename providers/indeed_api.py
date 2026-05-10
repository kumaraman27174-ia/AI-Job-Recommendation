import requests


def get_indeed_jobs(query):
    # This file uses JSearch API from RapidAPI.
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": "1a1c912624msh48259caf40d9b06p1fccdejsna110a7ab1da5",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    params = {
        "query": f"{query} in India",
        "page": "1",
        "num_pages": "1"
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        data = res.json()
    except Exception as e:
        print("JSearch API Error:", e)
        return []

    jobs = []
    for j in data.get("data", []):
        jobs.append({
            "title": j.get("job_title", ""),
            "company": j.get("employer_name", ""),
            "location": j.get("job_city") or j.get("job_country") or "",
            "description": j.get("job_description", ""),
            "link": j.get("job_apply_link") or j.get("job_google_link") or "",
            "source": "JSearch"
        })

    return jobs
