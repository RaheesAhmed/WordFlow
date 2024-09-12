import base64
import logging
import requests
import aiohttp
from config import adjust_post_date, format_permalink
from utils import get_custom_filename


def get_auth_header(user, password):
    auth_string = f"{user}:{password}"
    base64_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {base64_auth}", "User-Agent": "Mozilla/5.0"}


# Function to get the WordPress category ID or create it if not exists
def get_category_id(category_name, wp_site):
    headers = get_auth_header(wp_site["user"], wp_site["password"])
    response = requests.get(
        f"{wp_site['url']}categories?search={category_name}", headers=headers
    )

    if response.status_code == 200 and response.json():
        return response.json()[0]["id"]

    response = requests.post(
        f"{wp_site['url']}categories", headers=headers, json={"name": category_name}
    )
    if response.status_code == 201:
        return response.json()["id"]
    else:
        logging.error(
            f"Failed to get or create category '{category_name}'. Defaulting to ID 1."
        )
        return 1


# Function to get the WordPress tag ID or create it if not exists
def get_tag_id(tag_name, wp_site):
    headers = get_auth_header(wp_site["user"], wp_site["password"])
    response = requests.get(f"{wp_site['url']}tags?search={tag_name}", headers=headers)

    if response.status_code == 200 and response.json():
        return response.json()[0]["id"]

    response = requests.post(
        f"{wp_site['url']}tags", headers=headers, json={"name": tag_name}
    )
    if response.status_code == 201:
        return response.json()["id"]
    else:
        logging.error(f"Failed to get or create tag '{tag_name}'.")
        return None


# Function to upload an image to WordPress and return media ID with alt text
def upload_image_to_wp(image_url, wp_site, alt_text):
    custom_filename = get_custom_filename()

    response = requests.get(image_url)
    if response.status_code != 200:
        logging.error(f"Failed to download image from {image_url}")
        return None

    image_data = response.content
    headers = {
        "Content-Disposition": f'attachment; filename="{custom_filename}"',
        "Content-Type": "image/webp",
        **get_auth_header(wp_site["user"], wp_site["password"]),
    }

    try:
        upload_response = requests.post(
            wp_site["url"] + "media",
            headers=headers,
            data=image_data,
            params={"alt_text": alt_text},
        )

        if upload_response.status_code == 201:
            upload_result = upload_response.json()
            media_id = upload_result.get("id")
            return media_id
        else:
            logging.error(
                f"Failed to upload {custom_filename} to {wp_site['url']} - Status Code: {upload_response.status_code}"
            )
            logging.error(upload_response.text)
            return None

    except Exception as e:
        logging.error(f"An error occurred while uploading image: {e}")
        return None


# Async function to publish posts to WordPress
async def create_post_async(
    content,
    website,
    keyword,
    description,
    media_id,
    category,
    meta_keywords,
    meta_description,
    cached_title,
    tag_names,
    slug_function,
    publish_status,
    post_date_adjustment,
):
    headers = get_auth_header(website["user"], website["password"])
    slug = slug_function(cached_title)
    category_id = get_category_id(category, website) if category else 1
    tag_ids = [get_tag_id(tag_name, website) for tag_name in tag_names]
    tag_ids = [tag_id for tag_id in tag_ids if tag_id is not None]
    post_date = adjust_post_date(post_date_adjustment)
    data = {
        "title": cached_title,
        "slug": slug,
        "content": content,
        "status": publish_status,
        "categories": [category_id],
        "tags": tag_ids,
        "featured_media": media_id,
        "date": post_date,
        "meta": {
            "rank_math_focus_keyword": keyword,
            "rank_math_description": meta_description,
            "rank_math_keywords": meta_keywords,
        },
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{website['url']}posts", headers=headers, json=data
            ) as response:
                response.raise_for_status()
                post_data = await response.json()
                permalink = post_data.get("link", "")
                post_id = post_data["id"]
                logging.info(f"Post published successfully. Permalink: {permalink}")
                return permalink, post_id, cached_title
        except Exception as e:
            logging.error(f"Failed to publish post: {e}")
            return None, None, None
