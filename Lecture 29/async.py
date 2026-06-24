import asyncio
import aiohttp
import time

# __enter__
# __exit__

# __aenter__
# __aexit__



async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()




async def main():
    BASE_API_URL = 'https://rickandmortyapi.com/api/character/{id}'


    tasks = []
    for i in range(1, 21):
        task = asyncio.create_task(fetch_data(BASE_API_URL.format(id=i)))
        tasks.append(task)
        # await fetch_data(BASE_API_URL.format(id=i))



    await asyncio.gather(*tasks)



if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())

    end = time.time()
    print(end - start)
