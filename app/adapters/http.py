"""Shared httpx AsyncClient placeholder"""
class AsyncClientPlaceholder:
    async def get(self, url):
        return {"url": url}
