import re

SENIORITY = {
    "intern": -1,
    "newgrad": 0,
    "junior": 1,
    "mid": 3,
    "senior": 6
}

def find_seniority(title, soup):
    """Find seniority using known information"""
    # quick return if title or position has keywords
    for seniority in SENIORITY.keys():
        if seniority in title.lower():
            return seniority
    job_des_tags = soup.find("div", class_="content")
    
    years = find_years(job_des_tags)
    # quick return if content has keywords or exact YOE
    if years == SENIORITY["intern"]:
        return "intern"
    elif years == SENIORITY["newgrad"]:
        return "newgrad"
    elif SENIORITY["newgrad"] <= years < SENIORITY["mid"]:
        return "junior"
    elif SENIORITY["mid"] <= years < SENIORITY["senior"]:
        return "mid"
    elif years >= SENIORITY["senior"]:
        return "senior"
    
    # return salary and job requirement for LLM input
    else:
        salary = find_salary(job_des_tags)
        req = find_requirements(job_des_tags)
        return f"title: {title}, salary: {salary}, requirement: {req}"

def find_years(tags) -> int:
    """Find (YOE) in Job Description"""
    text = tags.get_text(" ", strip=True) if tags else ""
    
    years = -2
    if "grad" in text:
        return 0
    elif "intern" in text:
        return -1
    
    years_match = re.search(r'(\d+)\+?\s+years?', text, re.IGNORECASE)
    if years_match:
        numbers = re.findall(r'\d+', years_match.group(0))
        years = int(numbers[0])
    
    return years

def find_salary(tags) -> str:
    if not tags:
        return ""
    salary_keywords = ["$", "salary", "compensation", "pay", "annual", "hourly"]
    all_paragraphs = tags.find_all(["p","li"], text=True)
    filtered_paragraphs = []
    for para in all_paragraphs:
        for k in salary_keywords:
            if k.lower() in para.lower():
                filtered_paragraphs.append(para)
    return " ".join(filtered_paragraphs) if filtered_paragraphs else ""


def find_requirements(content) -> str:
    if not content:
        return ""
    requirements = []
    req_headers = ["require", "qualif", "have", "responsib"]
    for header in req_headers:
        section = content.find(
            lambda tag: tag.name in ["h2","h3","strong"] and header in tag.get_text().lower()
        )
        if section:
            next_siblings = []
            for sibling in section.find_next_siblings():
                if sibling.name in ["h2","h3","strong"]:
                    break
                next_siblings.append(
                    sibling.get_text(" ", strip=True) if hasattr(sibling,"get_text") else str(sibling).strip()
                )
            requirements = next_siblings
            break
    return " ".join(requirements) if requirements else ""
