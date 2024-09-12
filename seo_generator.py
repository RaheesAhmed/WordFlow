import asyncio
import re
from openai_api import fetch_openai_response


async def generate_seo_elements(
    overview,
    keyword,
    serper_data,
    title,
    language,
    description,
    content,
    url,
    input_language,
    input_openai_model,
):
    categories_list = [
        "Arts & Entertainment",
        "Business and Consumer Services",
        "Community and Society",
        "Computers Electronics and Technology",
        "Ecommerce & Shopping",
        "Finance",
        "Food and Drink",
        "Gambling",
        "Games",
        "Health",
        "Heavy Industry and Engineering",
        "Hobbies and Leisure",
        "Home and Garden",
        "Jobs and Career",
        "Law and Government",
        "Lifestyle",
        "News & Media Publishers",
        "Pets and Animals",
        "Reference Materials",
        "Science and Education",
        "Sports",
        "Travel and Tourism",
        "Vehicles",
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
         - Align the image concept with the article's theme and content, ensuring it directly supports the narrative and appeals to the target audience.
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
    response = await fetch_openai_response(prompt, input_openai_model)
    meta_keywords = re.search(
        r"<meta_keywords>(.*?)<\/meta_keywords>", response, re.DOTALL
    )
    meta_description = re.search(
        r"<meta_description>(.*?)<\/meta_description>", response, re.DOTALL
    )
    img_alt = re.search(r"<img_alt>(.*?)<\/img_alt>", response, re.DOTALL)
    website_title = re.search(
        r"<website_title>(.*?)<\/website_title>", response, re.DOTALL
    )
    ai_img_prompt = re.search(
        r"<ai_img_prompt>(.*?)<\/ai_img_prompt>", response, re.DOTALL
    )
    website_category = re.search(
        r"<website_category>(.*?)<\/website_category>", response, re.DOTALL
    )

    # Return extracted data with default "Not Found" if missing
    return {
        "meta_keywords": (
            meta_keywords.group(1).strip() if meta_keywords else "Not Found"
        ),
        "meta_description": (
            meta_description.group(1).strip() if meta_description else "Not Found"
        ),
        "img_alt": img_alt.group(1).strip() if img_alt else "Not Found",
        "website_title": (
            website_title.group(1).strip() if website_title else "Not Found"
        ),
        "ai_img_prompt": (
            ai_img_prompt.group(1).strip() if ai_img_prompt else "Not Found"
        ),
        "website_category": (
            website_category.group(1).strip() if website_category else "Not Found"
        ),
    }


async def generate_html_content(
    overview, keyword, serper_data, url, content, input_language, input_openai_model
):
    prompt = f"""
    Generate a comprehensive 3500 word SEO-optimized blog article in HTML format based on the overview, keyword, and SERP data provided.
    - Objective: Generate a comprehensive 3500+ word SEO-optimized blog article in only {input_language} on the specified topic, formatted in HTML.
       - Format: <html><article>...</article></html>
       - Instructions:
         - Use the provided website niche, content, and keyword overview extensively, ensuring the content is unique, informative, engaging, and logically structured.
         - The writing style should be conversational and human-like, making the content accessible and appealing to a broad audience.
         - Include headings, paragraphs, lists, and other HTML elements needed for a well-structured article.
         - Ensure to create a must only 1 (single hyperlink in article) hyperlink using the format `<a href="{url}/" target="_blank" rel="noreferrer noopener">{keyword}</a>`, using the provided keyword as the anchor text only, avoiding terms like "visit" or "click here". Place the link naturally within the first or second paragraph, ensuring it fits seamlessly with the content without being forced.
         - Follow the specified HTML content structure, with headings that are specific to the keyword and overview provided, reflecting unique aspects, trends, benefits, challenges, or future opportunities.

       Format: <article>

          <!-- Introduction -->

          <p>
            Begin with a compelling introduction (approx. 600-700 words) that captures the reader's interest, highlighting the importance and relevance of {keyword} in the context provided by the overview. Discuss how {keyword} impacts the target audience or sector, setting the stage for the detailed insights to follow. Incorporate the hyperlink naturally, for example:
            <a href="{url}" target="_blank" rel="noreferrer noopener">{keyword}</a>.
          </p>

          <!-- Historical Context and Evolution -->

          <h2>History and Evolution of {keyword}</h2>

          <p>
            (Approx. 500-600 words) Cover the origins and development of {keyword}, including significant milestones and historical trends that have shaped its current form. Explain why understanding this history is valuable to the audience, and how it can inform current strategies or decisions. Relate these historical insights to the present scenario described in the overview.
          </p>

          <!-- Core Benefits and Practical Applications -->

          <h2>Benefits and Applications of {keyword}</h2>

          <p>
            (Approx. 600-700 words) Highlight the primary advantages of engaging with {keyword}, emphasizing its effectiveness in the context provided by the overview. Provide practical examples or scenarios where {keyword} is particularly beneficial, addressing the audience's needs or challenges. Link these benefits directly to the audience's pain points or goals.
          </p>

          <!-- How {keyword} Works or Key Components -->

          <h2>How {keyword} Works</h2>

          <p>
            (Approx. 500-600 words) Delve into the workings of {keyword}, breaking down its essential components or methodologies. Describe how each element contributes to its overall functionality and effectiveness. Use clear, accessible language, and incorporate real-world examples to enhance understanding.
          </p>

          <!-- Challenges, Limitations, and Common Misconceptions -->

          <h2>Challenges and Misconceptions About {keyword}</h2>

          <p>
            (Approx. 500-600 words) Discuss any drawbacks, challenges, or limitations associated with {keyword}. Provide a balanced view, including perspectives that might deter engagement, and offer solutions or counterpoints where applicable. Highlight common misconceptions and correct them with evidence-based explanations.
          </p>

          <!-- Future Trends and Emerging Opportunities -->

          <h2>Future Trends in {keyword}</h2>

          <p>
            (Approx. 600-700 words) Analyze upcoming trends and emerging opportunities in the realm of {keyword}. Discuss how changes in technology, market dynamics, or consumer behavior could shape its future. Identify specific opportunities that the audience should be aware of, and suggest actionable steps to prepare for or capitalize on these trends.
          </p>

          <!-- Conclusion: Emphasizing the Importance and Next Steps -->

          <h2>(Generate a unqiue {keyword} and Next Steps)</h2>

          <p>
            (Approx. 400-500 words) Summarize the key points discussed in the article, reiterating the importance of {keyword} within its specific context. Provide practical advice or next steps for the reader, encouraging further engagement with the topic. Close with a compelling statement that reinforces the value of staying informed and proactive about {keyword}, tailored to the audience's needs as outlined in the overview.
          </p>

      </article>

    Inputs Provided:
    - MY targeting website Overview: {overview}
    - MY targeting website content : {content}
    - My Targeting Keyword: {keyword}
    - My Targeting SERP Data with Competitors: {serper_data}

    """

    response = await fetch_openai_response(prompt, input_openai_model)
    html_content = re.search(r"<html>(.*?)<\/html>", response, re.DOTALL)
    return html_content.group(1).strip() if html_content else "No HTML Content Found"


# overview = "web design"
# keyword = "web design"
# serper_data = "web design"
# title = "web design"
# language = "english"
# description = "web design"
# content = "web design"
# url = "web design"
# input_language = "english"
# input_openai_model = "gpt-4o"

# seo_elements = asyncio.run(
#     generate_seo_elements(
#         overview,
#         keyword,
#         serper_data,
#         title,
#         language,
#         description,
#         content,
#         url,
#         input_language,
#         input_openai_model,
#     )
# )

# print(seo_elements)

# overview = "web design"
# keyword = "web design"
# serper_data = "web design"
# title = "web design"
# language = "english"
# description = "web design"
# content = "web design"
# url = "web design"
# input_language = "english"
# input_openai_model = "gpt-4o"

# html_content = asyncio.run(
#     generate_html_content(
#         overview, keyword, serper_data, url, content, input_language, input_openai_model
#     )
# )

# print(html_content)
