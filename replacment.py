import os
import openai
import replicate
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
import csv
import json
import re
import requests
import random
import string
import logging
import base64
import aiohttp
from datetime import datetime, timedelta
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, SpinnerColumn
from rich.console import Console
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your OpenAI and Replicate API keys
openai.api_key = "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"
os.environ["REPLICATE_API_TOKEN"] = "r8_XTZ4FXxX73INMlNnwaEk48dWmEEpGJy3TwSAC"

# Define the output directory
output_directory = r"C:\Users\zaheer\Desktop\Open AI\New Auto Blogging\Scrape"
os.makedirs(output_directory, exist_ok=True)

websites = {

}

# Utility Functions
def clean_file_path(file_path):
    cleaned_path = file_path.strip(" &\"'")  # Strip spaces, &, ", and ' characters
    return os.path.normpath(cleaned_path)  # Normalize path for the operating system

def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain.replace('www.', '')  # Remove 'www.' if present

def get_auth_header(user, password):
    auth_string = f"{user}:{password}"
    base64_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {base64_auth}", "User-Agent": "Mozilla/5.0"}

def read_csv_with_encoding(csv_file_path):
    with open(csv_file_path, 'rb') as f:
        result = chardet.detect(f.read())
        detected_encoding = result['encoding']
    try:
        df = pd.read_csv(csv_file_path, encoding=detected_encoding)
        return df
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        exit(1)

# WordPress Functions
def get_post_id(permalink, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    response = requests.get(f"{wp_site['url']}posts?slug={permalink.split('/')[-2]}", headers=headers)
    if response.status_code == 200 and response.json():
        return response.json()[0]['id']
    logging.error(f"Failed to retrieve post ID for {permalink}")
    return None

def update_post_title(post_id, new_title, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    data = {"title": new_title}
    response = requests.post(f"{wp_site['url']}posts/{post_id}", headers=headers, json=data)
    if response.status_code == 200:
        logging.info(f"Successfully updated title for post {post_id} to '{new_title}'")
    else:
        logging.error(f"Failed to update title for post {post_id}: {response.text}")

def update_post_slug(post_id, new_slug, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    data = {"slug": new_slug}
    response = requests.post(f"{wp_site['url']}posts/{post_id}", headers=headers, json=data)
    if response.status_code == 200:
        logging.info(f"Successfully updated slug for post {post_id} to '{new_slug}'")
    else:
        logging.error(f"Failed to update slug for post {post_id}: {response.text}")

def upload_image_to_wp(image_url, wp_site, alt_text):
    if not image_url.startswith('http'):
        logging.error(f"Invalid image URL: {image_url}")
        return None

    response = requests.get(image_url)
    if response.status_code != 200:
        logging.error(f"Failed to download image from {image_url}")
        return None

    image_data = response.content
    headers = {
        'Content-Disposition': f'attachment; filename="{alt_text}.webp"',
        'Content-Type': 'image/webp',
        **get_auth_header(wp_site['user'], wp_site['password'])
    }

    try:
        upload_response = requests.post(
            wp_site['url'] + 'media',
            headers=headers,
            data=image_data,
            params={'alt_text': alt_text}
        )

        if upload_response.status_code == 201:
            upload_result = upload_response.json()
            media_id = upload_result.get('id')
            return media_id
        else:
            logging.error(f"Failed to upload image to {wp_site['url']} - Status Code: {upload_response.status_code}")
            logging.error(upload_response.text)
            return None

    except Exception as e:
        logging.error(f"An error occurred while uploading image: {e}")
        return None

def update_post_image(post_id, media_id, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    data = {"featured_media": media_id}
    response = requests.post(f"{wp_site['url']}posts/{post_id}", headers=headers, json=data)
    if response.status_code == 200:
        logging.info(f"Successfully updated image for post {post_id}")
    else:
        logging.error(f"Failed to update image for post {post_id}: {response.text}")

def update_post_content(post_id, new_content, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    data = {"content": new_content}
    response = requests.post(f"{wp_site['url']}posts/{post_id}", headers=headers, json=data)
    if response.status_code == 200:
        logging.info(f"Successfully updated content for post {post_id}")
    else:
        logging.error(f"Failed to update content for post {post_id}: {response.text}")

def get_category_id(category_name, wp_site):
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    response = requests.get(f"{wp_site['url']}categories?search={category_name}", headers=headers)
    
    if response.status_code == 200 and response.json():
        return response.json()[0]['id'] 
    
    response = requests.post(f"{wp_site['url']}categories", headers=headers, json={"name": category_name})
    if response.status_code == 201:
        return response.json()['id']  
    else:
        logging.error(f"Failed to get or create category '{category_name}'. Defaulting to ID 1.")
        return 1  

def update_post_category(post_id, new_category, wp_site):
    category_id = get_category_id(new_category, wp_site)
    headers = get_auth_header(wp_site['user'], wp_site['password'])
    data = {"categories": [category_id]}
    response = requests.post(f"{wp_site['url']}posts/{post_id}", headers=headers, json=data)
    if response.status_code == 200:
        logging.info(f"Successfully updated category for post {post_id}")
    else:
        logging.error(f"Failed to update category for post {post_id}: {response.text}")

# AI and Content Generation Functions
def fetch_openai_response(prompt, input_openai_model):
    try:
        response = openai.ChatCompletion.create(
            model=input_openai_model,
            messages=[
                {"role": "system", "content": "You are a copywriting specialist focused on producing high-quality, long-form content tailored to the needs of specific audiences. Your content is original, data-driven, and adheres to best practices for readability and SEO."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Error fetching OpenAI response: {e}")
        return f"Error: Unable to generate content with OpenAI. {str(e)}"

def generate_seo_elements(overview, keyword, serper_data, title, language, description, content, url, input_language, input_openai_model):
    categories_list = [
        "Arts & Entertainment", "Business and Consumer Services", "Community and Society",
        "Computers Electronics and Technology", "Ecommerce & Shopping", "Finance", "Food and Drink",
        "Gambling", "Games", "Health", "Heavy Industry and Engineering", "Hobbies and Leisure",
        "Home and Garden", "Jobs and Career", "Law and Government", "Lifestyle", "News & Media Publishers",
        "Pets and Animals", "Reference Materials", "Science and Education", "Sports",
        "Travel and Tourism", "Vehicles"
    ]

    prompt = f"""
    You are an expert SEO copywriting specialist focused on producing high-quality, data-driven content tailored to specific audiences. Your task is to analyze the provided data, including the overview, targeting keyword, SERP insights, and competitor data, to generate SEO-optimized elements that are engaging, superior to competitors, and capable of driving significant results. Each output should be precise, formatted as specified, and aligned with best practices for SEO and user engagement.

    Your Task:
    Analyze the provided data and create the following SEO elements with an emphasis on clarity, relevance, effectiveness, and strategic superiority over competitors:

    1. Meta Keywords:
       - Objective: Generate a list of highly relevant keywords that reflect the main topics of the article.
       - Format: <meta_keywords>keyword1, keyword2, keyword3</meta_keywords>
       - Instructions:
         - Extract key themes from the overview, SERP data, and competitor insights.
         - Include the primary keyword and related terms that enhance search relevance.
         - Focus on keywords that align with user intent and are likely to perform well in search results.

    2. Meta Description:
       - Objective: Write a concise meta description that captures the essence of the article and enhances click-through rates.
       - Format: <meta_description>description text</meta_description>
       - Instructions:
         - Summarize the article in 1-2 sentences.
         - Include the targeting keyword naturally and prominently.
         - Make the description enticing and actionable to encourage clicks.
         - Keep it clean and straightforward without any special characters.

    3. Image Alt Tag:
       - Objective: Create descriptive alt text for an image that enhances SEO and accessibility.
       - Format: <img_alt>alt tag text</img_alt>
       - Instructions:
         - Describe the image content clearly and succinctly.
         - Include the targeting keyword naturally.
         - Ensure the alt text adds value to SEO and improves accessibility for screen readers.

    4. Website Title:
       - Objective: Generate a single-line info blog, eye-catching website title optimized for search engines and user engagement.
       - Format: <website_title>title text</website_title>
       - Instructions:
         - Craft a title that not only reflects the content overview but also outperforms competitor titles by offering unique value or insights.
         - Conduct a brief analysis of competitor titles; identify patterns, weaknesses, and areas for differentiation.
         - Include the targeting keyword {keyword} exactly as provided, ensuring it fits naturally and adds to the title's relevance.
         - Avoid generic phrases; instead, emphasize unique selling points, actionable language, or intriguing hooks that set your content apart.
         - Keep the title under 120 characters for optimal display in search results.
         - Ensure the title is clear, direct, and aligned with user intent, aiming to dominate competitors in search results with superior relevance and engagement.

    5. AI Image Creation Prompt:
       - Objective: Craft a detailed prompt for an AI image generation tool to create a visual that complements the article and stands out against competitor visuals.
       - Format: <ai_img_prompt>prompt text</ai_img_prompt>
       - Instructions:
         - Describe the desired image in detail, including key visual elements that should be present.
         - Align the image concept with the article’s theme and content, ensuring it directly supports the narrative and appeals to the target audience.
         - Analyze competitor visuals; identify gaps or areas where your image can add more value or a unique perspective.
         - Include specifics such as style, color palette, mood, and any thematic elements that are particularly relevant to your content and audience.
         - Emphasize any unique visual elements or creative aspects that could make the image more engaging and shareable, surpassing competitors.
         - Highlight any accessibility considerations, ensuring the image also meets inclusivity standards.

    6. Website Category:
       - Objective: Identify the main category that best represents the website.
       - Format: <website_category>category name</website_category>
       - Instructions:
         - Based on the provided information, determine the website's category.
         - Choose only one category from the list provided.
         - List of Categories: {categories_list}

    Additional Guidelines:
    - Output in only {input_language} language
    - Ensure all outputs are engaging, accurate, and well-aligned with the content, user intent, and competitive landscape.
    - Avoid any generic or overly broad terms; focus on specific, actionable language that drives results.
    - Be strategic with the keyword placement to maximize SEO effectiveness without sacrificing readability.

    Inputs Provided:
    - MY targeting website Overview: {overview}
    - MY targeting website content : {content}
    - My Targeting Keyword: {keyword}
    - My Targeting SERP Data with Competitors: {serper_data}

    Output Requirements:
    - Output in only {input_language} language
    - Provide clean, formatted data as specified for each element.
    - Focus solely on generating actionable SEO data without additional content.
    - Prioritize strategic placement of the targeting keyword and related terms to enhance SEO performance.
    - Ensure each element maximizes the content's visibility, relevance, and appeal to both search engines and readers.
    - Aim to create SEO elements that clearly outperform competitor efforts, contributing to higher rankings and engagement.
    """

    # Call the AI service and extract data using regex patterns
    response = fetch_openai_response(prompt, input_openai_model)
    meta_keywords = re.search(r'<meta_keywords>(.*?)<\/meta_keywords>', response, re.DOTALL)
    meta_description = re.search(r'<meta_description>(.*?)<\/meta_description>', response, re.DOTALL)
    img_alt = re.search(r'<img_alt>(.*?)<\/img_alt>', response, re.DOTALL)
    website_title = re.search(r'<website_title>(.*?)<\/website_title>', response, re.DOTALL)
    ai_img_prompt = re.search(r'<ai_img_prompt>(.*?)<\/ai_img_prompt>', response, re.DOTALL)
    website_category = re.search(r'<website_category>(.*?)<\/website_category>', response, re.DOTALL)

    # Return extracted data with default "Not Found" if missing
    return {
        "meta_keywords": meta_keywords.group(1).strip() if meta_keywords else "Not Found",
        "meta_description": meta_description.group(1).strip() if meta_description else "Not Found",
        "img_alt": img_alt.group(1).strip() if img_alt else "Not Found",
        "website_title": website_title.group(1).strip() if website_title else "Not Found",
        "ai_img_prompt": ai_img_prompt.group(1).strip() if ai_img_prompt else "Not Found",
        "website_category": website_category.group(1).strip() if website_category else "Not Found"
    }

# Function to find the site configuration based on a permalink
def find_site_by_permalink(permalink):
    domain = extract_domain(permalink)
    return next((site for site in websites.values() if extract_domain(site['url']) == domain), None)

# Function to edit post content by replacing URLs and anchor texts
def edit_post_content(site, post_id, replace_url=None, replace_anchor=None):
    url = f"{site['url']}posts/{post_id}"
    response = requests.get(url, auth=(site['user'], site['password']))
    if response.status_code == 200:
        post_content = response.json().get('content', {}).get('rendered', '')
        soup = BeautifulSoup(post_content, 'html.parser')

        for link in soup.find_all('a', href=True):
            # Handle URL replacement with case insensitivity
            if replace_url and link['href'].lower() == replace_url['old'].lower():
                link['href'] = replace_url['new']
            # Handle anchor text replacement with case insensitivity
            if replace_anchor and link.text.lower() == replace_anchor['old'].lower():
                link.string = replace_anchor['new']

        updated_content = str(soup)

        update_response = requests.post(url, auth=(site['user'], site['password']), json={'content': updated_content})
        if update_response.status_code == 200:
            print(f"Post {post_id} updated successfully on {site['url']}")
        else:
            print(f"Failed to update post {post_id} on {site['url']}: {update_response.text}")
    else:
        print(f"Failed to retrieve post {post_id} on {site['url']}: {response.text}")

# Function to process posts from a CSV file
def process_posts_from_csv(file_path, replace_url=None, replace_anchor=None):
    file_path = clean_file_path(file_path)
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = []
                for row in reader:
                    permalink = row.get('My Post Permalink')
                    post_id = row.get('Post ID')

                    if not permalink and not post_id:
                        print(f"Missing permalink and post ID in row: {row}")
                        continue
                    
                    site = find_site_by_permalink(permalink)

                    if site and post_id:
                        futures.append(executor.submit(edit_post_content, site, post_id, replace_url, replace_anchor))
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                for future in as_completed(futures):
                    future.result()
    except OSError as e:
        print(f"Failed to open the file. Error: {e}")

# Function to process posts from a TXT file
def process_posts_from_txt(file_path, replace_url=None, replace_anchor=None):
    file_path = clean_file_path(file_path)
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = []
                for line in lines:
                    permalink = line.strip()
                    if not permalink:
                        continue

                    site = find_site_by_permalink(permalink)

                    if site:
                        # Fetch post ID using permalink if necessary
                        slug = permalink.rstrip('/').split('/')[-1]
                        response = requests.get(f"{site['url']}posts", auth=(site['user'], site['password']), params={'slug': slug})
                        if response.status_code == 200 and response.json():
                            post_id = response.json()[0]['id']
                            futures.append(executor.submit(edit_post_content, site, post_id, replace_url, replace_anchor))
                        else:
                            print(f"Failed to find post with permalink {permalink} on {site['url']}")
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                for future in as_completed(futures):
                    future.result()
    except OSError as e:
        print(f"Failed to open the file. Error: {e}")

# Main Menu and Execution Logic
def first_menu():
    while True:
        print("Choose an option:")
        print("1. Edit Outgoing URL or Anchor Text")
        print("2. Replace something in the Post")
        print("#. Exit")
        choice = input("Enter your choice (1/2/#): ")

        if choice == '1':
            edit_url_or_anchor_text_menu()
        elif choice == '2':
            replace_post_content_menu()
        elif choice == '#':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")

# Function for editing outgoing URL or anchor text
def edit_url_or_anchor_text_menu():
    while True:
        print("\nEdit Options:")
        print("1. Edit only Outgoing URL")
        print("2. Edit only Outgoing URL anchor text")
        print("3. Edit both Outgoing URL and anchor text")
        print("0. Back to main menu")
        print("#. Exit")
        choice = input("Enter your choice (1/2/3/0/#): ")

        if choice == '0':
            return
        elif choice == '#':
            print("Exiting program.")
            exit()
        elif choice == '1':
            replace_url = {
                'old': input("Enter the URL to replace: "),
                'new': input("Enter the new URL: ")
            }
            replace_anchor = None
            submenu(replace_url, replace_anchor)
        elif choice == '2':
            replace_url = None
            replace_anchor = {
                'old': input("Enter the anchor text to replace: "),
                'new': input("Enter the new anchor text: ")
            }
            submenu(replace_url, replace_anchor)
        elif choice == '3':
            replace_url = {
                'old': input("Enter the URL to replace: "),
                'new': input("Enter the new URL: ")
            }
            replace_anchor = {
                'old': input("Enter the anchor text to replace: "),
                'new': input("Enter the new anchor text: ")
            }
            submenu(replace_url, replace_anchor)
        else:
            print("Invalid choice. Please try again.")

def replace_post_content_menu():
    while True:
        print("\nSelect what you want to change:")
        print("1. Replace the title.")
        print("2. Replace the slug.")
        print("3. Replace the AI-generated image.")
        print("4. Replace the full article content.")
        print("5. Replace the article category.")
        print("6. Edit by Post ID")
        print("7. Edit using a CSV file")
        print("8. Use drag-and-drop CSV file to edit")
        print("9. Use drag-and-drop TXT file with permalinks to edit")
        print("0. Back to main menu")
        print("#. Exit")
        choice = input("Enter your choice (1-9/0/#): ")

        if choice == '0':
            return  # Go back to the main menu
        elif choice == '#':
            print("Exiting program.")
            exit()  # Exit the program
        elif choice == '1':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                new_title = input("Enter the new title: ")
                update_post_title(post_id, new_title, site)
            else:
                print("Site not found.")
        elif choice == '2':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                new_slug = input("Enter the new slug: ")
                update_post_slug(post_id, new_slug, site)
            else:
                print("Site not found.")
        elif choice == '3':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                image_url = input("Enter the new image URL: ")
                alt_text = input("Enter the alt text for the image: ")
                media_id = upload_image_to_wp(image_url, site, alt_text)
                if media_id:
                    update_post_image(post_id, media_id, site)
                else:
                    print("Failed to upload and update the image.")
            else:
                print("Site not found.")
        elif choice == '4':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                new_content = input("Enter the new article content: ")
                update_post_content(post_id, new_content, site)
            else:
                print("Site not found.")
        elif choice == '5':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                new_category = input("Enter the new category name: ")
                update_post_category(post_id, new_category, site)
            else:
                print("Site not found.")
        elif choice == '6':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                # Implement specific post ID editing logic
                pass  # Replace with your function call
        elif choice == '7' or choice == '8':
            file_path = input("Drag and drop your CSV file here and press Enter: ")
            process_posts_from_csv(file_path)
        elif choice == '9':
            file_path = input("Drag and drop your TXT file here and press Enter: ")
            process_posts_from_txt(file_path)
        else:
            print("Invalid choice. Please try again.")

# Function to handle the submenu for specific actions
def submenu(replace_url, replace_anchor):
    while True:
        print("\nChoose a specific action:")
        print("1. Edit by Post ID")
        print("2. Edit using a CSV file")
        print("3. Use drag-and-drop CSV file to edit")
        print("4. Use drag-and-drop TXT file with permalinks to edit")
        print("0. Back to main menu")
        print("#. Exit")
        choice = input("Enter your choice (1/2/3/4/0/#): ")

        if choice == '#':
            print("Exiting program.")
            exit()
        elif choice == '0':
            return
        elif choice == '1':
            site_number = int(input("Enter the site number from the websites dictionary: "))
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                edit_post_content(site, post_id, replace_url, replace_anchor)
            else:
                print("Site not found.")
        elif choice == '2' or choice == '3':
            file_path = input("Drag and drop your CSV file here and press Enter: ")
            process_posts_from_csv(file_path, replace_url, replace_anchor)
        elif choice == '4':
            file_path = input("Drag and drop your TXT file here and press Enter: ")
            process_posts_from_txt(file_path, replace_url, replace_anchor)
        else:
            print("Invalid choice. Please try again.")

# Main entry point
if __name__ == "__main__":
    first_menu()
