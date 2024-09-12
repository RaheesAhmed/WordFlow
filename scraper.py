import asyncio
import logging
from playwright.async_api import async_playwright


async def scrape_elements(url, semaphore):
    async with semaphore:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=60000)

                selectors = ["h1", "h2", "h3", "h4", "h5", "p"]
                combined_text = ""
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    texts = [await element.inner_text() for element in elements]
                    combined_text += " ".join(texts) + " "

                title = await page.title()
                description = (
                    await page.eval_on_selector(
                        'meta[name="description"]', 'el => el.getAttribute("content")'
                    )
                    or "No description available"
                )
                language = (
                    await page.evaluate(
                        "() => document.documentElement.lang || 'Not specified'"
                    )
                    or "Not specified"
                )

                combined_text = combined_text.encode("utf-8", errors="ignore").decode(
                    "utf-8", errors="ignore"
                )

                await browser.close()
                return url, title, language, description, combined_text

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return url, "Error", "Error", "Error", None


# urls = ["https://www.google.com"]  # Define urls as a list


# async def main():
#     semaphore = asyncio.Semaphore(10)
#     tasks = [scrape_elements(url, semaphore) for url in urls]
#     results = await asyncio.gather(*tasks)
#     return results


# if __name__ == "__main__":
#     asyncio.run(main())
