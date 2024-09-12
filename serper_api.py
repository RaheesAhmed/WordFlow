import json
import logging
import asyncio
import aiohttp
from config import SERPER_API_KEY


async def fetch_serper_results_async(keyword, serper_cache, input_country, semaphore):
    async with semaphore:
        if keyword in serper_cache:
            return serper_cache[keyword]

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = json.dumps({"q": keyword, "gl": input_country})

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        serper_cache[keyword] = data
                        return data
                    else:
                        logging.error(
                            f"Failed to fetch Serper results: {response.status}"
                        )
            except Exception as e:
                logging.error(f"Error fetching Serper results: {e}")
        return None


# keyword = "web design"
# serper_cache = {}
# input_country = "us"
# semaphore = asyncio.Semaphore(10)


# async def main():
#     result = await fetch_serper_results_async(keyword, serper_cache, input_country, semaphore)
#     print(result)


# asyncio.run(main())
