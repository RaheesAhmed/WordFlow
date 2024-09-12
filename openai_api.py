import openai
import asyncio
import logging
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


async def fetch_openai_response(prompt, model):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a copywriting specialist focused on producing high-quality, long-form content tailored to the needs of specific audiences. Your content is original, data-driven, and adheres to best practices for readability and SEO.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error fetching OpenAI response: {e}")
        return f"Error: Unable to generate content with OpenAI. {str(e)}"


def clean_text(text):
    return (
        text.replace("##", "")
        .replace("**", "")
        .replace("###", "")
        .replace("####", "")
        .strip()
    )


# prompt = "Hello, how are you?"
# model = "gpt-4o"

# response = asyncio.run(fetch_openai_response(prompt, model))
# print(response)
