import asyncio

class webhook_queue:
    messages = []
    
    async def start(self, session, webhook, webhook_wait_time):
        while True:
            try:
                if self.messages:
                    await session.post(webhook, json={"content": "\n".join(self.messages)})
                    self.messages = []
            except:
                continue
            finally:
                await asyncio.sleep(webhook_wait_time)