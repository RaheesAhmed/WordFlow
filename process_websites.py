import asyncio
from seo_generator import generate_seo_elements, generate_html_content
from utils import distribute_articles
from image_generator import generate_image_async
from wordpress_api import upload_image_to_wp, create_post_async
import pandas as pd


async def process_website_task(
    index,
    website_url,
    row,
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
):
    language, title, meta_description, all_text_content = row[1:5]

    if "Error" in row:
        language = "Unknown"
        title = "Unknown"
        meta_description = "Unknown"
        all_text_content = "No content available due to scraping error."

    num_keywords = (
        int(df.at[index, "Number of Keywords"])
        if pd.notna(df.at[index, "Number of Keywords"])
        else 0
    )
    num_links = (
        int(df.at[index, "Number oF Links"])
        if pd.notna(df.at[index, "Number oF Links"])
        else 0
    )
    keywords = [
        df.at[index, f"Keyword # {i}"]
        for i in range(1, num_keywords + 1)
        if pd.notna(df.at[index, f"Keyword # {i}"])
    ]

    distribution = distribute_articles(keywords, num_links)

    async with semaphore:
        task_id = progress.add_task(
            f"Processing {website_url}",
            total=len(keywords) * 4,
            visible=True,
        )

        tasks = []  # List to hold tasks for concurrent execution
        for keyword, num_articles in zip(keywords, distribution):
            for _ in range(num_articles):
                serper_info = serper_cache.get(keyword, {"keywords": ""})
                seo_elements = generate_seo_elements(
                    all_text_content,
                    keyword,
                    serper_info,
                    title,
                    language,
                    meta_description,
                    all_text_content,
                    website_url,
                    defaults["input_language"],
                    defaults["input_openai_model"],
                )

                meta_keywords = seo_elements["meta_keywords"]
                meta_description = seo_elements["meta_description"]
                img_alt_tag = seo_elements["img_alt"]
                cached_title = seo_elements["website_title"]
                image_prompt = seo_elements["ai_img_prompt"]
                category = seo_elements["website_category"]

                # Create tasks for article generation, image generation, and post creation
                article_task = asyncio.create_task(
                    generate_html_content(
                        all_text_content,
                        keyword,
                        serper_info,
                        title,
                        language,
                        meta_description,
                        website_url,
                        defaults,
                    )
                )
                image_task = asyncio.create_task(
                    generate_image_async(
                        image_prompt,
                        defaults["image_output_count"],
                        defaults["image_ai_model"],
                    )
                )

                tasks.append(
                    (
                        article_task,
                        image_task,
                        keyword,
                        meta_keywords,
                        meta_description,
                        img_alt_tag,
                        cached_title,
                        category,
                    )
                )

        # Run all tasks concurrently
        results_tasks = await asyncio.gather(
            *[asyncio.gather(article, image) for article, image, *_ in tasks]
        )

        # Process each result from concurrent tasks
        post_tasks = []
        for i, (html_content, image_url) in enumerate(results_tasks):
            (
                keyword,
                meta_keywords,
                meta_description,
                img_alt_tag,
                cached_title,
                category,
            ) = tasks[i][2:]

            wp_site = websites[
                website_indices[current_website_index % len(website_indices)]
            ]
            current_website_index += 1

            # Reset index after reaching the last website
            if current_website_index >= len(website_indices):
                current_website_index = 0

            media_id = (
                await upload_image_to_wp(image_url, wp_site, img_alt_tag)
                if image_url
                else None
            )
            progress.update(overall_task, advance=1)
            progress.update(task_id, advance=1)

            if media_id:
                tags = (
                    meta_keywords.split(", ")
                    if meta_keywords != "Not Found"
                    else [keyword]
                )
                post_task = asyncio.create_task(
                    create_post_async(
                        html_content,
                        wp_site,
                        keyword,
                        meta_description,
                        media_id,
                        category,
                        meta_keywords,
                        meta_description,
                        cached_title,
                        tags,
                        defaults["default_slug_function"],
                        defaults["publish_status"],
                        defaults["post_date_adjustment"],
                    )
                )

                post_tasks.append(post_task)

        # Run all post creation tasks concurrently
        post_results = await asyncio.gather(*post_tasks)

        for result in post_results:
            if result:
                permalink, post_id, article_title = result
                results.append(
                    [
                        website_url,
                        permalink,
                        keyword,
                        category,
                        post_id,
                        meta_keywords,
                        meta_description,
                        img_alt_tag,
                        article_title,
                    ]
                )

        progress.update(task_id, visible=False)
