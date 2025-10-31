"""Startup/shutdown lifecycle hooks (httpx/redis pools)"""

async def startup():
    # create httpx/redis clients here
    print("startup placeholder")

async def shutdown():
    # close clients here
    print("shutdown placeholder")
