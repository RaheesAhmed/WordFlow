# WordFlow Configuration Guide

This guide provides detailed information on how to configure and customize WordFlow to suit your specific needs. Proper configuration ensures optimal performance and functionality of the WordFlow application.

## Table of Contents

- [WordFlow Configuration Guide](#wordflow-configuration-guide)
  - [Table of Contents](#table-of-contents)
  - [Environment Variables](#environment-variables)
  - [WordPress Site Configuration](#wordpress-site-configuration)
  - [AI Model Settings](#ai-model-settings)
  - [Content Generation Settings](#content-generation-settings)
  - [SEO Settings](#seo-settings)
  - [Image Generation Settings](#image-generation-settings)
  - [Scheduling Options](#scheduling-options)
  - [Performance Tuning](#performance-tuning)

## Environment Variables

WordFlow uses environment variables for sensitive information and global settings. Create a `.env` file in the root directory of the project and add the following variables:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
SERPER_API_KEY=your_serper_api_key_here

# Default Settings
DEFAULT_LANGUAGE=English
DEFAULT_OPENAI_MODEL=gpt-3.5-turbo
DEFAULT_IMAGE_MODEL=stability-ai/stable-diffusion
DEFAULT_COUNTRY=us

# Performance Settings
BATCH_SIZE=5
MAX_CONCURRENT_REQUESTS=20
```

Replace the placeholder values with your actual API keys and preferred default settings.

## WordPress Site Configuration

WordPress sites are configured in the `websites` dictionary in the `app.py` file. Add or modify sites using the following format:

```python
websites = {
    1: {
        "url": "https://example.com/wp-json/wp/v2/",
        "user": "your_username",
        "password": "your_password"
    },
    # Add more sites as needed
}
```

Ensure that you're using application passwords for enhanced security. To generate an application password:

1. Go to your WordPress dashboard
2. Navigate to Users → Profile
3. Scroll down to the Application Passwords section
4. Enter a name for the application password and click "Add New"
5. Copy the generated password and use it in the configuration

## AI Model Settings

Configure AI model settings in the Streamlit sidebar:

- **Input Language**: Select the primary language for content generation.
- **OpenAI Model**: Choose between different OpenAI models (e.g., GPT-3.5-turbo, GPT-4).
- **Image AI Model**: Select the AI model for image generation.

These settings can be adjusted per session in the Streamlit interface.

## Content Generation Settings

Customize content generation in the `generate_html_content` function:

- Modify the HTML structure for generated content
- Adjust the word count or structure of different sections
- Customize the prompt to fit your content style and requirements

## SEO Settings

SEO settings are managed in the `generate_seo_elements` function:

- Modify the list of generated SEO elements
- Adjust the format of meta descriptions, titles, and keywords
- Customize the prompt to align with your SEO strategy

## Image Generation Settings

Configure image generation settings in the Streamlit sidebar:

- **Number of Images**: Set the number of images to generate per post
- **Image AI Model**: Choose the AI model for image generation

Adjust the `generate_image_async` function to modify image generation parameters.

## Scheduling Options

Post scheduling options are available in the Streamlit sidebar:

- **Relative to today**: Schedule posts relative to the current date
- **Specific date**: Set an exact date and time for post publishing

Modify the `create_post_async` function to adjust how posts are scheduled and published.

## Performance Tuning

Optimize performance by adjusting the following settings:

- **BATCH_SIZE**: Number of keywords processed in each batch (in `.env` file)
- **MAX_CONCURRENT_REQUESTS**: Maximum number of concurrent API requests (in `.env` file)
- Adjust the `asyncio.Semaphore` value in the code to control concurrency

Monitor the application's performance and adjust these values as needed based on your system's capabilities and API rate limits.

---

Remember to restart the Streamlit application after making changes to the configuration files or environment variables. If you encounter any issues or need further customization, please refer to the project's documentation or open an issue on the GitHub repository.