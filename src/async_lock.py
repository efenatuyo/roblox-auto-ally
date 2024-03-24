import asyncio

async def sem_task(semaphore, coroutine):
    try:
        async with semaphore:
            return await coroutine
    except Exception as e:
        print(f"Error in coroutine: {e}")

async def limited_gather(max_concurrency, *coroutines):
    semaphore = asyncio.Semaphore(max_concurrency)
    return await asyncio.gather(*[sem_task(semaphore, coro) for coro in coroutines])