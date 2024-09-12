import logging
import asyncio
import replicate
from config import REPLICATE_API_TOKEN

replicate.api_key = REPLICATE_API_TOKEN


async def generate_image_async(image_prompt, image_output_count, image_ai_model):
    try:
        output = await replicate.async_run(
            image_ai_model,
            input={"prompt": image_prompt, "num_outputs": image_output_count},
        )
        if output and isinstance(output, list) and len(output) > 0:
            return output[0]
        else:
            logging.error("Failed to generate image: No valid output received")
    except replicate.exceptions.ModelError as e:
        logging.error(f"Failed to generate image: {e}")
    except Exception as e:
        logging.error(f"Error generating image: {e}")
    return None


# image_prompt = "A beautiful landscape with a river and mountains"
# image_output_count = 1
# image_ai_model = (
#     "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
# )

# image_url = asyncio.run(
#     generate_image_async(image_prompt, image_output_count, image_ai_model)
# )
# print(image_url)
