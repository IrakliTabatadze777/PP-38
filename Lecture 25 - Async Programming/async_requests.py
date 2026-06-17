from http.client import responses

import aiohttp
import asyncio



# ricky_morty_api = 'https://rickandmortyapi.com/api/character/1'
#
#
# async def fetch_data():
#     async with aiohttp.ClientSession() as session:
#         async with session.get(ricky_morty_api) as response:
#             return await response.json()
#
#
#
# async def main():
#
#     response = await fetch_data()
#     print(response)




ricky_morty_api = 'https://rickandmortyapi.com/api/character/{id}'


async def fetch_data(session: aiohttp.ClientSession, url: str):

    try:
        timeout = aiohttp.ClientTimeout(total=10)

        async with session.get(url, timeout=timeout) as response:
            response.raise_for_status()
            return await response.json()

    except aiohttp.ClientResponseError as e: # 4xx-5xx
        print(e)

    except aiohttp.ClientConnectorError as e: # couldn't connect to the server
        print(e)

    except aiohttp.ContentTypeError as e:
        print(e)

    except asyncio.TimeoutError as e:
        print(e)

    except Exception as e:
        print(e)


async def main():
    async with aiohttp.ClientSession() as session:
        # for i in range(1, 11):
        #     url = ricky_morty_api.format(id=i)
        #     response = await fetch_data(session, url)
        #     print(response)

        responses = await asyncio.gather(*[fetch_data(session=session, url=ricky_morty_api.format(id=i)) for i in range(1,11)])

        for data in responses:
            print(data)




if __name__ == '__main__':
    asyncio.run(main())
