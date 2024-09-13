import requests
import csv
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


websites = {}


def clean_file_path(file_path):
    cleaned_path = file_path.strip(" &\"'")  # Strip spaces, &, ", and ' characters
    return os.path.normpath(cleaned_path)  # Normalize path for the operating system


def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain.replace("www.", "")  # Remove 'www.' if present


def find_site_by_permalink(permalink):
    domain = extract_domain(permalink)
    return next(
        (s for s in websites.values() if extract_domain(s["url"]) == domain), None
    )


def edit_post_content(site, post_id, replace_url=None, replace_anchor=None):
    url = f"{site['url']}posts/{post_id}"
    response = requests.get(url, auth=(site["user"], site["password"]))
    if response.status_code == 200:
        post_content = response.json().get("content", {}).get("rendered", "")
        soup = BeautifulSoup(post_content, "html.parser")

        for link in soup.find_all("a", href=True):
            # Handle URL replacement with case insensitivity
            if replace_url and link["href"].lower() == replace_url["old"].lower():
                link["href"] = replace_url["new"]
            # Handle anchor text replacement with case insensitivity
            if replace_anchor and link.text.lower() == replace_anchor["old"].lower():
                link.string = replace_anchor["new"]

        updated_content = str(soup)

        update_response = requests.post(
            url,
            auth=(site["user"], site["password"]),
            json={"content": updated_content},
        )
        if update_response.status_code == 200:
            print(f"Post {post_id} updated successfully on {site['url']}")
        else:
            print(
                f"Failed to update post {post_id} on {site['url']}: {update_response.text}"
            )
    else:
        print(f"Failed to retrieve post {post_id} on {site['url']}: {response.text}")


def process_posts_from_csv(file_path, replace_url=None, replace_anchor=None):
    file_path = clean_file_path(file_path)
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = []
                for row in reader:
                    permalink = row.get("My Post Permalink")
                    post_id = row.get("Post ID")

                    if not permalink and not post_id:
                        print(f"Missing permalink and post ID in row: {row}")
                        continue

                    site = find_site_by_permalink(permalink)

                    if site and post_id:
                        futures.append(
                            executor.submit(
                                edit_post_content,
                                site,
                                post_id,
                                replace_url,
                                replace_anchor,
                            )
                        )
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                for future in as_completed(futures):
                    future.result()
    except OSError as e:
        print(f"Failed to open the file. Error: {e}")


def process_posts_from_txt(file_path, replace_url=None, replace_anchor=None):
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
                        # Fetch post ID using permalink if necessary
                        slug = permalink.rstrip("/").split("/")[-1]
                        response = requests.get(
                            f"{site['url']}posts",
                            auth=(site["user"], site["password"]),
                            params={"slug": slug},
                        )
                        if response.status_code == 200 and response.json():
                            post_id = response.json()[0]["id"]
                            futures.append(
                                executor.submit(
                                    edit_post_content,
                                    site,
                                    post_id,
                                    replace_url,
                                    replace_anchor,
                                )
                            )
                        else:
                            print(
                                f"Failed to find post with permalink {permalink} on {site['url']}"
                            )
                    else:
                        print(f"No site found for URL in permalink: {permalink}")

                for future in as_completed(futures):
                    future.result()
    except OSError as e:
        print(f"Failed to open the file. Error: {e}")


def main_menu():
    while True:
        print("Choose an option:")
        print("1. Edit only Outgoing URL")
        print("2. Edit only Outgoing URL anchor text")
        print("3. Edit both Outgoing URL and anchor text")
        print("#. Exit")
        choice = input("Enter your choice (1/2/3/#): ")

        if choice == "#":
            print("Exiting program.")
            break
        elif choice == "0":
            continue
        elif choice == "1":
            replace_url = {
                "old": input("Enter the URL to replace: "),
                "new": input("Enter the new URL: "),
            }
            replace_anchor = None
            submenu(replace_url, replace_anchor)
        elif choice == "2":
            replace_url = None
            replace_anchor = {
                "old": input("Enter the anchor text to replace: "),
                "new": input("Enter the new anchor text: "),
            }
            submenu(replace_url, replace_anchor)
        elif choice == "3":
            replace_url = {
                "old": input("Enter the URL to replace: "),
                "new": input("Enter the new URL: "),
            }
            replace_anchor = {
                "old": input("Enter the anchor text to replace: "),
                "new": input("Enter the new anchor text: "),
            }
            submenu(replace_url, replace_anchor)
        else:
            print("Invalid choice. Please try again.")


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

        if choice == "#":
            print("Exiting program.")
            exit()
        elif choice == "0":
            return
        elif choice == "1":
            site_number = int(
                input("Enter the site number from the websites dictionary: ")
            )
            post_id = input("Enter the Post ID: ")
            site = websites.get(site_number)
            if site:
                edit_post_content(site, post_id, replace_url, replace_anchor)
            else:
                print("Site not found.")
        elif choice == "2" or choice == "3":
            file_path = input("Drag and drop your CSV file here and press Enter: ")
            process_posts_from_csv(file_path, replace_url, replace_anchor)
        elif choice == "4":
            file_path = input("Drag and drop your TXT file here and press Enter: ")
            process_posts_from_txt(file_path, replace_url, replace_anchor)
        else:
            print("Invalid choice. Please try again.")
