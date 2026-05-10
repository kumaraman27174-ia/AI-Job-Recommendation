import requests
from bs4 import BeautifulSoup

def get_sarkari_jobs():
    url="https://www.sarkariresult.com/"
    res=requests.get(url)
    soup=BeautifulSoup(res.text,"html.parser")

    jobs=[]
    for a in soup.find_all("a"):
        title=a.text.strip()
        if "Apply" in title or "Recruitment" in title:
            jobs.append({"title":title,"link":a.get("href")})
    return jobs[:20]