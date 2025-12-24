import re

SENIORITY_KEYWORDS = {
    "intern": ["intern", "internship", "co-op", "coop"],
    "newgrad": ["new grad", "newgrad", "entry level", "recent graduate", "graduate", "campus"],
    "junior": ["junior", "associate", "level i", "level 1", "early career"],
    "mid": ["mid", "mid-level", "intermediate", "level ii", "level 2", "experienced"],
    "senior": ["senior", "staff", "principal", "lead", "level iii", "level 3", "level iv", "level 4"],
}

def title_filter(title: str):
    """FILTER LEVEL 1: MATCH KEYWORDS IN TITLE"""
    if not title:
        return None
    title_lower = title.lower()
    priority_order = ["intern", "newgrad", "junior", "mid", "senior"]
    for seniority in priority_order:
        for keyword in SENIORITY_KEYWORDS[seniority]:
            if keyword in title_lower:
                return seniority
    return None

def year_filter(html_text: str):
    """FILTER LEVEL 2: FIND YOE IN CONTENT"""
    html_text = re.sub(r'\s+', ' ', html_text)
    search_text = html_text.lower()
    number_words = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    years_patterns = [
    # 1. 1 year / 1+ years
    re.compile(rf'\b({number_words})\+?\s*years?\b', re.IGNORECASE),

    # 2. 1-2 years / 1 – 2 years
    re.compile(rf'\b({number_words})\s*[-–—]\s*({number_words})\s*years?\b', re.IGNORECASE),

    # 3. one to two years / one plus years
    re.compile(rf'\b({number_words})\s*(to|plus)\s*({number_words})\s*years?\b', re.IGNORECASE),

    # 4. experience of 1 year / experience: one year
    re.compile(rf'experience(?:\s*of|\s*[:])?\s*({number_words})\s*years?', re.IGNORECASE),

    # 5. experience 1-2 years
    re.compile(rf'experience\s*({number_words})\s*[-–—]\s*({number_words})\s*years?', re.IGNORECASE),
]
    
    for pattern in years_patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                try:
                    min_years = int(match[0])
                    return _map_years_to_seniority(min_years)
                except:
                    continue
            else:
                try:
                    years = int(match)
                    return _map_years_to_seniority(years)
                except:
                    continue
    
    # 2. text years: e.g. three years
    text_numbers = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
        'fifteen': 15
    }
    
    text_pattern = r'(' + '|'.join(text_numbers.keys()) + r')\s+years?'
    text_match = re.search(text_pattern, search_text, re.IGNORECASE)
    if text_match:
        years = text_numbers.get(text_match.group(1).lower(), 0)
        return _map_years_to_seniority(years)
    
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
    keywords = ["compensation", "salary", "wage", "hour", "annual", "month", "pay"]
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
            results.append(money_match.group().strip())

    if not results: 
        return "Unknown"
    return list(set(results))[0]

def entry(title, html_text):
    level_1 = title_filter(title)
    if level_1:
        return level_1
    level_2 = year_filter(html_text)
    if level_2:
        return level_2
    
    return parse_to_LLM(title, html_text)
