import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Input and Output Directories
INPUT_CSV_PATH = os.getenv("INPUT_CSV_PATH", "Input Data.csv")
OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "output")

# Default Settings
DEFAULT_INPUT_LANGUAGE = "English"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_INPUT_COUNTRY = "us"
DEFAULT_IMAGE_OUTPUT_COUNT = 1
DEFAULT_IMAGE_AI_MODEL = "black-forest-labs/flux-schnell"
DEFAULT_PUBLISH_STATUS = "publish"
DEFAULT_POST_DATE_ADJUSTMENT = -5

# Concurrency Settings
MAX_CONCURRENT_TASKS = 20

# Website Credentials
WEBSITE_CREDENTIALS_FILE = os.getenv(
    "WEBSITE_CREDENTIALS_FILE", "website_credentials.json"
)


# Function to adjust the post date based on the number of days
def adjust_post_date(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")


async def adjust_post_date(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")


# Function to ensure each URL starts with 'https://'
async def format_url(url):
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def format_permalink(title):
    permalink = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    words = permalink.lower().split()[:6]
    formatted_permalink = "-".join(words)
    return formatted_permalink


async def get_default_settings():
    return {
        "input_language": DEFAULT_INPUT_LANGUAGE,
        "input_openai_model": DEFAULT_OPENAI_MODEL,
        "input_country": DEFAULT_INPUT_COUNTRY,
        "image_output_count": DEFAULT_IMAGE_OUTPUT_COUNT,
        "default_slug_function": format_permalink,
        "default_category": None,
        "publish_status": DEFAULT_PUBLISH_STATUS,
        "image_ai_model": DEFAULT_IMAGE_AI_MODEL,
        "post_date_adjustment": DEFAULT_POST_DATE_ADJUSTMENT,
    }


def load_website_credentials():
    with open(WEBSITE_CREDENTIALS_FILE, "r") as file:
        return json.load(file)
