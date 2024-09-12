import random
import string
import re


def generate_random_string(length=4):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def get_custom_filename(keyword=None):
    random_suffix = generate_random_string()
    if keyword:
        return f"{keyword}-{random_suffix}.webp"
    else:
        return f"{random_suffix}.webp"


def format_permalink(title):
    permalink = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    words = permalink.lower().split()[:6]
    formatted_permalink = "-".join(words)
    return formatted_permalink


def get_main_domain(url):
    domain = re.search(r"://(www\.)?(.+?)(/|$)", url)
    return domain.group(2).split(".")[0] if domain else "unknown"


def distribute_articles(keywords, total_links):
    articles_per_keyword = total_links // len(keywords)
    remainder = total_links % len(keywords)
    distribution = [
        articles_per_keyword + 1 if i < remainder else articles_per_keyword
        for i in range(len(keywords))
    ]
    return distribution
