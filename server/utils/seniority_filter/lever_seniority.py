import re

def find_requirements(content) -> str:
    # 提取任职要求/资格 (requirements)
    # 常见格式: "Requirements", "Qualifications", "You should have", "Must have"
    requirements = None
    req_headers = ["require", "qualif", "have", "responsib"]
    for header in req_headers:
        section = content.find(lambda tag: tag.name in ["h2", "h3", "strong"] and header in tag.get_text().lower())
        if section:
            # 获取 header 后面的内容
            next_siblings = []
            for sibling in section.find_next_siblings():
                if sibling.name in ["h2", "h3", "strong"]:  # 遇到下一个 header 停止
                    break
                next_siblings.append(sibling.get_text(" ", strip=True))
            requirements = " ".join(next_siblings).strip()
            break
    
    return requirements

def find_years(tags) -> int:
    # 提取工作经验 (years)
    text = tags.get_text(" ", strip=True)
    # 通常会出现 "X years" 或 "X+ years" 字样
    years = None
    years_match = re.search(r'(\d+)\+?\s+years?', text, re.IGNORECASE)
    if years_match:
        numbers = re.findall(r'\d+', years_match.group(0))
        years = int(numbers[0])
    
    return years

def find_salary(tags) -> int:
    salary_keywords = ["$", "salary", "compensation", "pay", "annual", "hourly"]
    paragraphs = tags.find_all(text=True)
    # 匹配 "$120,000 - $150,000" 或 "$120,000"
    pattern = r'\$(\d{1,3}(?:,\d{3})*)(?:\s*-\s*\$(\d{1,3}(?:,\d{3})*))?'

    for para in paragraphs:
        if any(k in para.lower() for k in salary_keywords):
            match = re.search(pattern, para)
            if match:
                low = int(match.group(1).replace(",", ""))
                if match.group(2):
                    high = int(match.group(2).replace(",", ""))
                    return (low + high) // 2
                else:
                    return low
    return None