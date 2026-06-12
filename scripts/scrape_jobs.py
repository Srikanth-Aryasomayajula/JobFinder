import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = [
    "crash", "cae", "ls-dyna", "nvh",
    "festigkeit", "berechnungsingenieur",
    "simulation", "fem", "structural", "safety"
]

CAREER_SOURCES = [
    {
        "company": "Mercedes-Benz",
        "url": "https://jobs.mercedes-benz.com/search",
    },
    {
        "company": "Porsche",
        "url": "https://jobs.porsche.com/",
    },
    {
        "company": "Bosch",
        "url": "https://www.bosch.de/karriere/jobboerse/",
    }
]

# Load existing jobs (avoid duplicates)
try:
    with open("jobs.json", "r") as f:
        seen_jobs = json.load(f)
except:
    seen_jobs = []

seen_urls = {job["url"] for job in seen_jobs}

new_jobs = []


def send_telegram(job):
    message = f"""
🚀 New Job Found

Company: {job['company']}
Title: {job['title']}

Link:
{job['url']}
"""
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        }
    )


def keyword_match(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)


def scrape_generic(company, url):
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")

        links = soup.find_all("a")

        jobs = []

        for a in links:
            title = a.get_text(strip=True)
            href = a.get("href")

            if not title or not href:
                continue

            full_url = href
            if href.startswith("/"):
                full_url = url.rstrip("/") + href

            if full_url in seen_urls:
                continue

            if keyword_match(title):
                jobs.append({
                    "company": company,
                    "title": title,
                    "url": full_url,
                    "date_found": str(datetime.now())
                })

        return jobs

    except Exception as e:
        print(f"Error scraping {company}: {e}")
        return []


for source in CAREER_SOURCES:
    jobs = scrape_generic(source["company"], source["url"])

    for job in jobs:
        send_telegram(job)
        new_jobs.append(job)

        seen_urls.add(job["url"])


# Save updated job list
all_jobs = seen_jobs + new_jobs

with open("jobs.json", "w") as f:
    json.dump(all_jobs, f, indent=2)

print(f"Found {len(new_jobs)} new jobs")