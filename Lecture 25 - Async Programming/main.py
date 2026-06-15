# ============================================================
# 1. BASIC COROUTINE
# ============================================================

import asyncio
import time


async def fetch_data():

    # time.sleep(1)

    # int("hello")

    await asyncio.sleep(1)
    print("Hello")


# ============================================================
# 2. MAIN COROUTINE
# ============================================================

async def main():
    start = time.time()

    # --------------------------------------------------------
    # primitive await
    # --------------------------------------------------------

    await fetch_data()
    await fetch_data()
    await fetch_data()

    # --------------------------------------------------------
    # create_task()
    # --------------------------------------------------------

    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(fetch_data())
    task3 = asyncio.create_task(fetch_data())

    print("All coroutines started")

    await task1
    await task2
    await task3

    # --------------------------------------------------------
    # asyncio.gather()
    # --------------------------------------------------------

    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data(),
        return_exceptions=True,
    )

    print(results)

    end = time.time()
    print(f"Total time: {end - start:.2f} seconds")




if __name__ == "__main__":
    asyncio.run(main())