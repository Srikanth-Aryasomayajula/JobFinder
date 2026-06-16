import os
import json
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = [
    "crash", "cae", "ls-dyna", "nvh",
    "festigkeit", "berechnungsingenieur",
    "simulation", "fem", "structural", "safety",
    "entwicklungsingenieur", "ansys", "ansa"
]

STATIC_SOURCES = [
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

DYNAMIC_SOURCES = [
    {
        "company": "Akkodis",
        "search_url": "https://karriere.akkodis.com/search?query={keyword}"
    },
    {
        "company": "Ferchau",
        "search_url": "https://touch.ferchau.com/de/de?searchTerm={keyword}"
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

    keywords_text = ", ".join(job["matched_keywords"])

    message = f"""
🚀 JOB FOUND

🏢 Company: {job['company']}
💼 Position: {job['title']}

🔍 Matched Keywords:
{keywords_text}

🔗 Link:
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
    text_lower = text.lower()
    matched = []

    for k in KEYWORDS:
        if k in text_lower:
            matched.append(k)

    return matched

def scrape_search_site(company, base_url, keyword):

    jobs = []

    url = base_url.replace("{keyword}", keyword)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000)

        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "lxml")

    # extract job cards (generic)
    for a in soup.find_all("a"):

        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        if href.startswith("/"):
            base = "/".join(url.split("/")[:3])
            full_url = base + href
        else:
            full_url = href

        # IMPORTANT: ensure real job pages only
        if "search" in full_url:
            continue

        jobs.append({
            "company": company,
            "title": title,
            "url": full_url,
            "matched_keywords": [keyword]
        })

    return jobs
    
def scrape_site(company, url):

    try:
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0"
        })

        soup = BeautifulSoup(r.text, "lxml")

        jobs = []

        # -----------------------------
        # 1. LINK-LEVEL EXTRACTION
        # -----------------------------
        for a in soup.find_all("a"):

            title = a.get_text(strip=True)
            href = a.get("href")

            if not title or not href:
                continue

            if href.startswith("/"):
                base = "/".join(url.split("/")[:3])
                full_url = base + href
            else:
                full_url = href

            matched = keyword_match(title)

            if matched:
                jobs.append({
                    "company": company,
                    "title": title,
                    "url": full_url,
                    "matched_keywords": matched
                })

        return jobs

    except Exception as e:
        print(f"Error scraping {company}: {e}")
        return []

def scrape_dynamic_site(company, url):

    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(8000)

        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "lxml")

    # -----------------------------
    # 1. LINK LEVEL EXTRACTION
    # -----------------------------
    for a in soup.find_all(["a", "div"]):

        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        # matched = keyword_match(title)
        

        if href.startswith("/"):
            base = "/".join(url.split("/")[:3])
            full_url = base + href
        else:
            full_url = href

        if "search" in full_url:
            continue

        # matched = keyword_match(title)

        if not matched:
            continue
            
        jobs.append({
            "company": company,
            "title": title,
            "url": full_url,
            "matched_keywords": matched
        })

    print(company, title, matched)
    
    return jobs
    
    
# MAIN LOOP (REAL LOGIC)
all_found_jobs = []


# STATIC
for source in STATIC_SOURCES:
    all_found_jobs += scrape_site(source["company"], source["url"])

# DYNAMIC (REAL POWER)

KEYWORDS_TO_SEARCH = KEYWORDS  # reuse your existing list

for source in DYNAMIC_SOURCES:
    for keyword in KEYWORDS_TO_SEARCH:

        jobs = scrape_search_site(
            source["company"],
            source["search_url"],
            keyword
        )

        all_found_jobs += jobs

print("Jobs found:", len(all_found_jobs))

for job in all_found_jobs:

    if job["url"] in seen_urls:
        continue

    send_telegram(job)

    seen_urls.add(job["url"])
    new_jobs.append(job)


# Save updated job list
all_jobs = seen_jobs + new_jobs

with open("jobs.json", "w") as f:
    json.dump(all_jobs, f, indent=2)

print(f"Found {len(new_jobs)} new jobs")