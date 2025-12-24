from server.utils.engine import (
    get_ashby_job_details,
    get_lever_job_details,
    get_greenhouse_job_details,
    JobSite,
    TBS,
    regex)
from server.config.queries import COMPREHENSIVE_SOFTWARE_ENGINEER_QUERY
from model.scrapper import secrets
import time
import random
import requests
import re
import logging
import csv
from enum import Enum

class TBS(Enum):
    PAST_DAY = "d1"
    PAST_WEEK = "w1"
    PAST_MONTH = "m1"
    PAST_YEAR = "y1"

def find_jobs_googleAPI(
    keyword: str,
    job_sites: list[JobSite],
    tbs: TBS | None = None,
    max_results: int = 50,
):
    """
    Use Google Custom Search API to find job URLs。
    """

    search_sites = " OR ".join([f"site:{site.value}" for site in job_sites])
    search_query = f"{keyword} ({search_sites})"
    print(f"Searching for {search_query} using Google CSE API")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": secrets.GOOGLE_API_KEY,
        "cx": secrets.GOOGLE_CSE_ID,
        "q": search_query,
        "num": max_results,
        "dateRestrict": tbs, 
    }

    if tbs:
        # Google CSE dateRestrict format: 'd1' last 1 day, 'd7' last 1 week
        params["dateRestrict"] = tbs.value

    result_urls = []
    start_index = 1
    while len(result_urls) < max_results:
        params["start"] = start_index
        response = requests.get(url, params=params)
        try:
            data = response.json()
        except Exception as e:
            print("Error decoding JSON from Google API:", e)
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            result_urls.append(item["link"])
            if len(result_urls) >= max_results:
                break

        start_index += 10
        if "nextPage" not in data.get("queries", {}):
            break

        time.sleep(random.uniform(1, 3))

    print("Google search result:", result_urls)
    
    job_urls_by_board = {}
    for job_site in job_sites:
        job_urls_for_job_site = [
            url for url in result_urls if re.search(regex[job_site], url)
        ]
        job_urls_by_board[job_site] = job_urls_for_job_site

    return job_urls_by_board

def handle_job_insert(writer, job_urls: list[str], job_site: JobSite):
    for link in job_urls:
        try:
            job_details = []
            if job_site == JobSite.LEVER:
                job_details = get_lever_job_details(link)
            elif job_site == JobSite.GREENHOUSE:
                job_details = get_greenhouse_job_details(link)
            elif job_site == JobSite.ASHBY:
                job_details = get_ashby_job_details(link)
            else:
                continue
            job = {}
            job["company"] = job_details[0]
            job["job_title"] = job_details[1]
            job["image"] = job_details[2]
            job["job_url"] = link
            job["job_board"] = job_site.name
            job["seniority"] = job_details[3]
            print(f"Inserting job: {job}")
            writer.writerow(job)
        except Exception as e:
            logging.error(f"Failed to process job: {str(e)}")

def perform_task():
    job_urls_by_board = find_jobs_googleAPI(
        COMPREHENSIVE_SOFTWARE_ENGINEER_QUERY,
        [JobSite.LEVER, JobSite.GREENHOUSE, JobSite.ASHBY],
        TBS.PAST_WEEK,
        5,
    )
    if not job_urls_by_board:
        print("No jobs found.")
        return
    with open("./model/data/dataset1.csv", "a", newline="", encoding="utf-8") as f:
        fieldnames = ["company", "job_title", "image", "job_url", "job_board", "seniority"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for job_board, job_urls in job_urls_by_board.items():
            handle_job_insert(writer, job_urls, job_board)

perform_task()


