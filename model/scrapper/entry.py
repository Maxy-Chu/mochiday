from fetch_jobs import fetch_all_jobs

def perform_task():
    jobs = fetch_all_jobs()
    if not jobs:
        print("No jobs found.")
        return

    import csv
    with open("./data/data2.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Saved {len(jobs)} jobs.")

perform_task()