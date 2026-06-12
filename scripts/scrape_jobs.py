import os
import json
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = [
    "crash",
    "cae",
    "ls-dyna",
    "festigkeit",
    "nvh",
    "berechnungsingenieur"
]

# DEMO JOBS
jobs = [
    {
        "title": "Berechnungsingenieur Crash",
        "company": "Mercedes",
        "url": "https://jobs.mercedes-benz.com"
    },
    {
        "title": "Software Developer",
        "company": "Some Company",
        "url": "https://example.com"
    }
]

for job in jobs:

    title = job["title"].lower()

    if any(keyword in title for keyword in KEYWORDS):

        message = f"""
🚀 New Job Found

Company: {job['company']}

Position:
{job['title']}

Link:
{job['url']}
"""

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message
            }
        )