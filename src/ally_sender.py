import random, asyncio

from . import async_lock

class RobloxAllySender:

    @staticmethod
    async def scrape_assets(session, cookie):
        items =  await session.get(f"https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&salesTypeFilter=1&sortType=3&subcategory=ClassicShirts", 
                            cookies={".ROBLOSECURITY": cookie.cookie}, 
                            headers={"x-csrf-token": await cookie.x_token(session)},
                            proxy=cookie.proxy)
        if items.status != 200:
            return []
        return [item['id'] for item in (await items.json())["data"]]
    
    @staticmethod
    async def get_allies_group(session, cookie, group_id, already_found):
        response = await session.get(f"https://groups.roblox.com/v1/groups/{group_id}/relationships/allies?maxRows=100&sortOrder=Asc&startRowIndex=0",
                                cookies={".ROBLOSECURITY": cookie.cookie},
                                headers={"x-csrf-token": await cookie.x_token(session)},
                                proxy=cookie.proxy)
        if response.status != 200:
           return []
        groups = []
        for group in (await response.json())["relatedGroups"]:
           if group["id"] not in already_found:
              open("src/data/already_added.txt", "a").write(f"\n{group['id']}")
              groups.append(group["id"])
        return groups

    @staticmethod
    async def sort_assets(session, cookie, already_added, asset_ids):
        response = await session.post("https://catalog.roblox.com/v1/catalog/items/details", 
                                json={"items": [{"itemType": "Asset", "id": id} for id in asset_ids]},
                                cookies={".ROBLOSECURITY": cookie.cookie},
                                headers={"x-csrf-token": await cookie.x_token(session)},
                                proxy=cookie.proxy)
        if response.status != 200:
            return []
        groups = []
        for item in (await response.json())["data"]:
            if item["creatorType"] == "Group" and item["creatorTargetId"] not in already_added:
                already_added.append(item["creatorTargetId"])
                open("src/data/already_added.txt", "a").write(f"\n{item['creatorTargetId']}")
                groups.append(item["creatorTargetId"])
        return groups
    
    @staticmethod
    async def send_ally_request(session, cookie, group_id, GROUP_ID, webhook_queue, send_fail):
        response = await session.post(f"https://groups.roblox.com/v1/groups/{GROUP_ID}/relationships/allies/{group_id}",
                                cookies={".ROBLOSECURITY": cookie.cookie}, 
                                headers={"x-csrf-token": await cookie.x_token(session)},
                                proxy=cookie.proxy)
        if response.status == 200:
            print(f"+ {group_id}")
            webhook_queue.messages.append(f"Sent ally request to group: {group_id}")
        else:
            if send_fail:
                print(f"- {group_id}")
                webhook_queue.messages.append(await response.text())
        cookie.proxy = random.choice(cookie.proxies)
        
async def handle_group(session, cookie, group, group_id, webhook_queue, already_found, send_fail):
    await RobloxAllySender.send_ally_request(session, cookie, group, group_id, webhook_queue, send_fail)
    return await RobloxAllySender.get_allies_group(session, cookie, group, already_found)
    
async def start_process(session, cookies, group_id, webhook_queue, threads, send_fail):
    already_found = open("src/data/already_added.txt", "r").read().rsplit("\n")
    allies = []
    while True:
        try:
            random_cookie = random.choice(cookies)
            for group in await RobloxAllySender.sort_assets(session, random_cookie, already_found, await RobloxAllySender.scrape_assets(session, random_cookie)):
                already_found.append(group)
                allies.append(group)
                while allies:
                    tasks = []
                    current_index = 0
                    for group in allies:
                        if current_index == len(cookies):
                            current_index = 0
                            break
                        else:
                            tasks.append(handle_group(session, cookies[current_index], group, group_id, webhook_queue, already_found, send_fail))
                            allies.remove(group)
                            current_index += 1
                    for response in await async_lock.limited_gather(threads, *tasks):
                        for group in response:
                            if group not in allies:
                                allies.append(group)
                    await asyncio.sleep(60 / len(cookies))
        except:
            pass
