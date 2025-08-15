import asyncio
import logging
from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings
from post_to_facebook_with_image import post_to_facebook, post_text_to_facebook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_to_facebook_task(ctx, user_id: str, caption: str, image_path: str = None):
    """Background task for posting to Facebook"""
    try:
        logger.info(f"Processing Facebook post for user {user_id}")
        
        if image_path and settings.AI_DISABLE_IMAGE_GENERATION is False:
            result = post_to_facebook(caption, image_path)
        else:
            result = post_text_to_facebook(caption)
        
        logger.info(f"Facebook post result for user {user_id}: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Error posting to Facebook for user {user_id}: {e}")
        return {"status": "error", "message": str(e)}

async def startup(ctx):
    logger.info("Worker started")

async def shutdown(ctx):
    logger.info("Worker shutdown")

class WorkerSettings:
    functions = [post_to_facebook_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

if __name__ == "__main__":
    # Run the worker
    from arq import run_worker
    run_worker(WorkerSettings)
