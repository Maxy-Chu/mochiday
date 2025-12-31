import re

SENIORITY_KEYWORDS = {
    "intern": ["intern", "internship", "co-op", "coop"],
    "newgrad": ["new grad", "ng", "newgrad", "entry level", "graduate", "campus"],
    "junior": ["junior", "jr", "associate", "level i", "level 1", "early career", "neer i", "l3", "l4"],
    "mid": ["mid", "mid-level", "intermediate", "level ii", "level 2", "experienced", "neer ii", "iii", "l5"],
    "senior": ["senior", "sr" ,"staff", "principal", "lead", "level iii", "level 3", "level iv", "iv", "level 4", "l6", "l7"],
}

def title_filter(title: str):
    """FILTER LEVEL 1: MATCH KEYWORDS IN TITLE"""
    if not title:
        return None
    title_lower = title.lower()
    keywords = ["intern", "newgrad", "junior", "mid", "senior"]
    for seniority in keywords:
        for keyword in SENIORITY_KEYWORDS[seniority]:
            if keyword in title_lower:
                return seniority
    return None

def year_filter(html_text: str):
    """FILTER LEVEL 2: FIND YOE IN CONTENT"""
    html_text = re.sub(r'\s+', ' ', html_text)

    # ---------- keywords ----------
    keywords = [
        "experience", "yoe", "qualification", "require"
    ]
    keyword_pattern = re.compile(
        r'(' + '|'.join(map(re.escape, keywords)) + r')',
        re.IGNORECASE
    )

    # ---------- number mapping ----------
    text_numbers = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
        'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12,
        'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'several': 3, 'few': 3,
    }

    number_words = '|'.join(text_numbers.keys())

    # ---------- year patterns ----------
    years_pattern = re.compile(
        rf'(?:'
        rf'(\d+)\+?\s*years?'                            # 1 / 1+ years
        rf'|'
        rf'(\d+)\s*[-–—]\s*(\d+)\s*years?'               # 1-2 years
        rf'|'
        rf'({number_words})\+?\s*years?'                 # one / one+ years
        rf'|'
        rf'({number_words})\s*[-–—]\s*({number_words})\s*years?'  # one-two years
        rf'|'
        rf'({number_words})\s*(?:to|plus)\s*({number_words})\s*years?' # one to two years
        rf')',
        re.IGNORECASE
    )

    # ---------- search near keywords ----------
    for m in keyword_pattern.finditer(html_text):
        pos = m.start()
        segment = html_text[max(0, pos - 150): pos + 300]

        y_match = years_pattern.search(segment)
        if not y_match:
            continue

        groups = y_match.groups()

        # numeric
        if groups[0]:
            return _map_years_to_seniority(int(groups[0]))
        if groups[1] and groups[2]:
            return _map_years_to_seniority(int(groups[1]))

        # text numbers
        for g in groups:
            if g and g.lower() in text_numbers:
                return _map_years_to_seniority(text_numbers[g.lower()])

    return None

def _map_years_to_seniority(years):
    if years == -1:
        return "intern"
    elif years == 0:
        return "newgrad"
    elif 0 < years < 3:
        return "junior"
    elif 3<= years <= 5:
        return "mid"
    else:
        return "senior"

def parse_to_LLM(title: str, content_text: str):
    salary = find_salary(content_text)
    return f"title: {title}, salary: {salary}"

def find_salary(html_text: str):
    """FIND SALARY IN CONTENT"""
    html_text = re.sub(r'\s+', ' ', html_text)
    money_pattern = re.compile(
        r'(?:'                                 
            r'(?:\$|USD)\s?\d{1,3}(?:,\d{3})*\s*[kK]?'   # $130K / USD 130K
            r'|'
            r'\d{1,3}(?:,\d{3})*\s*[kK]?\s?(?:USD|\$)'   # 130K USD / 130K $
        r')'
        r'(?:\s*[-–—]\s*'                      # allow salary range
            r'(?:\$|USD)?\s?\d{1,3}(?:,\d{3})*\s*[kK]?\s?(?:USD|\$)?'
        r')?',
        re.VERBOSE
    )
    keywords = ["compensation", "salary", "wage", "hour", "annual", "month"]
    keyword_pattern = re.compile(
        r'(' + '|'.join(map(re.escape, keywords)) + r')',
        re.IGNORECASE
    )
    results = []
    for m in keyword_pattern.finditer(html_text):
        pos = m.start()
        # find keyword
        segment = html_text[max(0, pos-150): pos+300]
        money_match = money_pattern.search(segment)
        if money_match:
            item = money_match.group().strip()
            if _is_valid_money(item):
                results.append(item)

    if not results: 
        return "Unknown"
    return list(set(results))[0]

def _is_valid_money(item):
    MIN_SALARY = 100
    MAX_SALARY = 2000000
    try:
        parts = re.split(r'[-–—]', item)
        value = parts[0].upper().replace("USD", "").replace("$", "").strip()
        multiplier = 1
        if value.endswith("K"):
            multiplier = 1000
            value = value[:-1]
        value = value.replace(",", "")
        amount = float(value) * multiplier
        return MIN_SALARY <= amount <= MAX_SALARY
    except Exception:
        return False

def entry(title, soup):
    html_text = soup.get_text(separator=" ", strip=True)
    level_1 = title_filter(title)
    if level_1:
        return level_1
    level_2 = year_filter(html_text)
    if level_2:
        return level_2
    
    return parse_to_LLM(title, html_text)
