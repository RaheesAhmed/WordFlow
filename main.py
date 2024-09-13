import asyncio
import logging
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
import pandas as pd
from config import (
    INPUT_CSV_PATH,
    OUTPUT_DIRECTORY,
    MAX_CONCURRENT_TASKS,
    get_default_settings,
    load_website_credentials,
    format_url,
)
from utils import (
    get_main_domain,
    distribute_articles,
    get_custom_filename,
    generate_random_string,
)
from scraper import scrape_elements
from serper_api import fetch_serper_results_async
from process_websites import process_website_task

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
console = Console()


async def main():
    # Load configuration and data
    defaults = await get_default_settings()
    websites = load_website_credentials()

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        return

    formatted_urls = [await format_url(url) for url in df["Website URL"]]
    data = []
    serper_cache = {}
    results = []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        overall_task = progress.add_task(
            "Overall Progress", total=len(formatted_urls) * 4, visible=True
        )

        # Scrape elements concurrently
        scraping_tasks = [scrape_elements(url, semaphore) for url in formatted_urls]
        scrape_results = await asyncio.gather(*scraping_tasks)

        for result in scrape_results:
            url, title, language, description, combined_text = result
            data.append([url, language, title, description, combined_text])
            progress.update(overall_task, advance=1, description="Scraping")

        # Process Serper results concurrently
        keyword_columns = [col for col in df.columns if col.startswith("Keyword #")]
        keywords = set(df[keyword_columns].values.flatten())
        keywords.discard(None)  # Remove None values

        serper_tasks = [
            fetch_serper_results_async(
                keyword, serper_cache, defaults["input_country"], semaphore
            )
            for keyword in keywords
        ]
        await asyncio.gather(*serper_tasks)
        progress.update(
            overall_task, advance=len(keywords), description="Fetching Serper Results"
        )

        # Process website tasks
        website_indices = list(websites.keys())
        current_website_index = 0

        website_tasks = [
            process_website_task(
                index,
                data[index][0],
                data[index],
                websites,
                website_indices,
                current_website_index,
                serper_cache,
                semaphore,
                progress,
                overall_task,
                defaults,
                df,
                results,
            )
            for index in range(len(data))
        ]

        await asyncio.gather(*website_tasks)

    # Save results grouped by domain
    results_by_domain = {}
    for result in results:
        website_url = result[0]
        main_domain = get_main_domain(website_url)
        results_by_domain.setdefault(main_domain, []).append(result)

    for domain, domain_results in results_by_domain.items():
        results_df = pd.DataFrame(
            domain_results,
            columns=[
                "Client Website URL",
                "My Post Permalink",
                "Keyword",
                "Article Category",
                "Post ID",
                "Meta Keywords",
                "Meta Description",
                "Image Alt Tag",
                "Article Title",
            ],
        )
        output_file = f"{OUTPUT_DIRECTORY}/{domain}.csv"
        results_df.to_csv(output_file, index=False)
        logging.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
