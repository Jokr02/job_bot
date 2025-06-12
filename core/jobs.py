
from core.logging import logger

async def search_jobs(days: int = 1):
    logger.info(f"🔎 Suche Jobs der letzten {days} Tage...")
    # TODO: echte Jobsuche hier implementieren

def start_job_loop(bot):
    async def job_loop():
        import asyncio
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await search_jobs()
            except Exception as e:
                logger.error(f"Fehler im Job-Loop: {e}")
            await asyncio.sleep(3600)
    bot.loop.create_task(job_loop())
