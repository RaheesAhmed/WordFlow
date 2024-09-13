import requests
import csv
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

websites = {}


def delete_post_by_id(site, post_id):
    url = f"{site['url']}posts/{post_id}"
    for _ in range(3):  # Retry up to 3 times
        response = requests.delete(url, auth=(site["user"], site["password"]))
        if response.status_code == 200:
            print(f"Post {post_id} deleted successfully from {site['url']}")
            return
        elif response.status_code == 404:
            print(f"Post {post_id} not found on {site['url']}")
            return
        else:
            print(
                f"Failed to delete post {post_id} from {site['url']}: {response.text}"
            )
        time.sleep(2)  # Wait before retrying
    print(f"Failed to delete post {post_id} after multiple attempts.")


def delete_post_by_permalink(site, permalink):
    url = f"{site['url']}posts"
    slug = permalink.rstrip("/").split("/")[
        -1
    ]  # Extracts the last part of the URL as the slug
    params = {"slug": slug, "status": "any"}  # Check posts of any status
    for _ in range(3):  # Retry up to 3 times
        response = requests.get(
            url, auth=(site["user"], site["password"]), params=params
        )
        if response.status_code == 200 and response.json():
            post_id = response.json()[0]["id"]
            delete_post_by_id(site, post_id)
            return
        elif response.status_code == 404 or not response.json():
            print(f"No matching post found for slug {slug} on {site['url']}")
            return
        else:
            print(
                f"Failed to find post with permalink {permalink} on {site['url']}: {response.text}"
            )
        time.sleep(2)  # Wait before retrying
    print(f"Failed to find post with permalink {permalink} after multiple attempts.")


def clean_file_path(file_path):
    # Clean up common extra characters from drag-and-drop input
    cleaned_path = file_path.strip(" &\"'")  # Strip spaces, &, ", and ' characters
    return os.path.normpath(cleaned_path)  # Normalize path for the operating system


def extract_domain(url):
    # Extract the domain from a URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain.replace("www.", "")  # Remove 'www.' if present


def find_site_by_permalink(permalink):
    # Extract domain from the permalink and find matching site credentials
    domain = extract_domain(permalink)
    return next(
        (s for s in websites.values() if extract_domain(s["url"]) == domain), None
    )


def delete_posts_from_csv(file_path):
    # Normalize and clean up the file path
    file_path = clean_file_path(file_path)

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = []
                for row in reader:
                    permalink = row.get(
                        "My Post Permalink"
                    )  # Adjust this if the column name differs
                    post_id = row.get("Post ID")

                    if not permalink and not post_id:
                        print(f"Missing permalink and post ID in row: {row}")
                        continue

                    site = find_site_by_permalink(permalink)

                    if site:
                        if post_id:
                            futures.append(
                                executor.submit(delete_post_by_id, site, post_id)
                            )
                        elif permalink:
                            futures.append(
                                executor.submit(
                                    delete_post_by_permalink, site, permalink
                                )
                            )
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()

    except OSError as e:
        print(f"Failed to open the file. Error: {e}")


def delete_posts_from_txt(file_path):
    # Normalize and clean up the file path
    file_path = clean_file_path(file_path)

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            lines = file.readlines()
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = []
                for line in lines:
                    permalink = line.strip()
                    if not permalink:
                        continue

                    site = find_site_by_permalink(permalink)

                    if site:
                        futures.append(
                            executor.submit(delete_post_by_permalink, site, permalink)
                        )
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()

    except OSError as e:
        print(f"Failed to open the file. Error: {e}")


def main():
    print("Choose an option:")
    print("1. Delete by Post ID")
    print("2. Delete by Permalink")
    print("3. Delete by uploading a CSV file")
    print("4. Use drag-and-drop CSV file to delete posts")
    print("5. Use drag-and-drop TXT file with permalinks to delete posts")
    choice = input("Enter your choice (1/2/3/4/5): ")

    if choice == "1":
        site_number = int(input("Enter the site number from the websites dictionary: "))
        post_id = input("Enter the Post ID: ")
        site = websites.get(site_number)
        if site:
            delete_post_by_id(site, post_id)
        else:
            print("Site not found.")
    elif choice == "2":
        site_number = int(input("Enter the site number from the websites dictionary: "))
        permalink = input("Enter the Permalink: ")
        site = websites.get(site_number)
        if site:
            delete_post_by_permalink(site, permalink)
        else:
            print("Site not found.")
    elif choice == "3" or choice == "4":
        file_path = input("Drag and drop your CSV file here and press Enter: ")
        delete_posts_from_csv(file_path)
    elif choice == "5":
        file_path = input("Drag and drop your TXT file here and press Enter: ")
        delete_posts_from_txt(file_path)
    else:
        print("Invalid choice.")
