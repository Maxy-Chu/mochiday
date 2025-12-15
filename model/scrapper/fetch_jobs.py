import csv
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import utils.seniority_filter.lever_seniority as lever_filter
import cloudscraper

# -----------------------------
# 构建 Cloudflare 兼容 session
# -----------------------------
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

KEYWORDS = [
    "engineer", "developer", "programmer", "full stack",
    "frontend", "backend", "web developer"
]

CSV_FILE = "./data/data1.csv"

LEVER_COMPANIES = [
    "spotify",
    "stripe",
    "doordash",  # 真实在 Lever 上的
    "lyft",
    "metabase"
]

GREENHOUSE_COMPANIES = [
    "affirm",
    "cloudflare",
    "notion",
    "discord",
    "roblox",
    "openai"
]

ASHBY_COMPANIES = [
    "ramp",
    "brex",
    "linear",
    "retool",
    "figma"
]


def contains_keyword(title: str):
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def now_utc():
    """确保是 offset-aware datetime"""
    return datetime.now(tz=datetime.utcnow().astimezone().tzinfo)


# =========================================================
# 1. Lever
# =========================================================
def fetch_lever_jobs(company, last_hours=24):
    url = f"https://jobs.lever.co/{company}?mode=json"

    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
        jobs_json = response.json()
    except Exception:
        logging.error(f"Failed fetching Lever for {company}")
        return []

    jobs = []
    now = now_utc()

    for job in jobs_json:
        try:
            posted = datetime.fromisoformat(job["postedAt"].replace("Z", "+00:00"))
        except:
            continue

        if now - posted > timedelta(hours=last_hours):
            continue

        title = job.get("text", "")
        if not contains_keyword(title):
            continue

        job_url = f"https://jobs.lever.co/{company}/{job['id']}"
        details = parse_lever_detail(job_url)

        if details:
            jobs.append(details)

    return jobs


def parse_lever_detail(url: str):
    try:
        resp = scraper.get(url, timeout=10)
        resp.raise_for_status()
    except:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.string if soup.title else "Unknown"

    if "-" in title:
        company, pos = title.split("-", 1)
    else:
        company, pos = "Unknown", title

    desc = soup.find("div", class_="content")
    years = salary = reqs = None
    if desc:
        years = lever_filter.find_years(desc)
        salary = lever_filter.find_salary(desc)
        reqs = lever_filter.find_requirements(desc)

    posted_tag = soup.find("meta", {"name": "lever:posted_at"})
    posted = posted_tag["content"] if posted_tag else None

    return {
        "company": company.strip(),
        "job_title": pos.strip(),
        "years": years,
        "salary": salary,
        "requirements": reqs,
        "apply_url": url + "/apply",
        "posted_at": posted,
        "source": "lever"
    }


# =========================================================
# 2. Greenhouse
# =========================================================
def fetch_greenhouse_jobs(company, last_hours=24):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except:
        logging.error(f"Failed fetching Greenhouse for {company}")
        return []

    jobs = []
    now = now_utc()

    for job in data.get("jobs", []):
        try:
            updated = datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
        except:
            continue

        if now - updated > timedelta(hours=last_hours):
            continue

        title = job.get("title", "")
        if not contains_keyword(title):
            continue

        jobs.append({
            "company": company,
            "job_title": title,
            "years": None,
            "salary": None,
            "requirements": None,
            "apply_url": job["absolute_url"],
            "posted_at": job["updated_at"],
            "source": "greenhouse"
        })

    return jobs


# =========================================================
# 3. AshbyHQ
# =========================================================
def fetch_ashby_jobs(company, last_hours=24):
    url = f"https://jobs.ashbyhq.com/api/org/{company}/jobs"

    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
        jobs_json = response.json()
    except:
        logging.error(f"Failed fetching Ashby for {company}")
        return []

    jobs = []
    now = now_utc()

    for job in jobs_json:
        try:
            posted = datetime.fromisoformat(job["createdAt"].replace("Z", "+00:00"))
        except:
            continue

        if now - posted > timedelta(hours=last_hours):
            continue

        title = job.get("title", "")
        if not contains_keyword(title):
            continue

        jobs.append({
            "company": company,
            "job_title": title,
            "years": None,
            "salary": None,
            "requirements": None,
            "apply_url": job["jobUrl"],
            "posted_at": job["createdAt"],
            "source": "ashby"
        })

    return jobs


# =========================================================
# 统一入口
# =========================================================
def fetch_all_jobs():
    all_jobs = []

    for c in LEVER_COMPANIES:
        all_jobs.extend(fetch_lever_jobs(c))

    for c in GREENHOUSE_COMPANIES:
        all_jobs.extend(fetch_greenhouse_jobs(c))

    for c in ASHBY_COMPANIES:
        all_jobs.extend(fetch_ashby_jobs(c))

    return all_jobs