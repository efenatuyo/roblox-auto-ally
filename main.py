from src import async_lock, proxy, cookie, ally_sender, webhook_queue

import asyncio, aiohttp, random, json

async def main():
    config = json.loads(open("config.json", "r").read())
    cookies = open("cookies.txt", "r").read().rstrip("\n").splitlines()
    proxies = proxy.make(len(cookies) * 50)
    
    cookie_objects = []
    cookie_region_unlock_tasks = []
    async with aiohttp.ClientSession() as session:
        for _cookie in cookies:
            cookie_object = cookie.RobloxCookie(_cookie, proxies)
            cookie_objects.append(cookie_object)
            if config["region_unlock_cookies"]:
                cookie_region_unlock_tasks.append(cookie_object.region_unlock(session))
        await async_lock.limited_gather(config["total_threads"], *cookie_region_unlock_tasks)
        
        webhook_queue_task = webhook_queue.webhook_queue()
        await asyncio.gather(*[ally_sender.start_process(session, cookie_objects, config["group_id"], webhook_queue_task, config["total_threads"], config["send_failed_request_webhook"]), webhook_queue_task.start(session, config["webhook"], config["webhook_wait_time"])])
        
    
asyncio.run(main())
