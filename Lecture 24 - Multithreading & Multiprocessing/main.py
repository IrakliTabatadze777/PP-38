# ============================================================
# 1. BASIC THREADS
# ============================================================

import threading
import time


def worker(task):
    print(f"Started worker: {task}")
    time.sleep(5)
    print(f"Finished worker: {task}")


start = time.time()

thread1 = threading.Thread(
    target=worker,
    args=("Task 1",),
    name="Thread-1",
)

thread2 = threading.Thread(
    target=worker,
    args=("Task 2",),
    name="Thread-2",
)

thread1.start()
thread2.start()

print(threading.active_count())
print(threading.enumerate())

thread1.join()
thread2.join()

print(threading.enumerate())

end = time.time()
print(f"Total time: {end - start}")


# ============================================================
# 2. THREADS + HTTP REQUESTS
# ============================================================

import requests


count = 0


def fetch_data(task, post_id):
    global count

    print(f"Fetching data from {task}...")

    base_url = "https://jsonplaceholder.typicode.com/photos/{id}"
    response = requests.get(base_url.format(id=post_id))

    count += 1
    return response.json()


start = time.time()

thread_list = []

for i in range(1, 1001):
    thread = threading.Thread(
        target=fetch_data,
        args=(f"Task-{i}", i),
    )
    thread_list.append(thread)

for thread in thread_list:
    thread.start()

for thread in thread_list:
    thread.join()

print(f"Request count: {count}")

end = time.time()
print(f"Total time: {end - start}")


# ============================================================
# 3. RACE CONDITION AND LOCK
# ============================================================

lock = threading.Lock()
counter = 0


def increment():
    global counter

    for _ in range(10_000_000):
        with lock:
            counter += 1


threads = [
    threading.Thread(target=increment)
    for _ in range(5)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

print(counter)


# ============================================================
# 4. MULTIPROCESSING
# ============================================================

import multiprocessing


counter = 0


def increment():
    global counter

    for _ in range(10_000_000):
        counter += 1


if __name__ == "__main__":
    processes = [
        multiprocessing.Process(target=increment)
        for _ in range(10)
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    print(counter)

    with multiprocessing.Pool() as pool:
        result = pool.map(increment, [10_000_000])

    print(result)


# ============================================================
# 5. THREADPOOLEXECUTOR AND FUTURES
# ============================================================

from concurrent.futures import ThreadPoolExecutor, as_completed

urls = [
    f"https://jsonplaceholder.typicode.com/comments/{i}"
    for i in range(1, 21)
]


def fetch_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


with ThreadPoolExecutor(max_workers=5) as executor:

    # Example 1: executor.map()
    results = list(executor.map(fetch_data, urls))

    # Example 2: submit() + as_completed()
    future_to_url = {
        executor.submit(fetch_data, url): url
        for url in urls
    }

    for future in as_completed(future_to_url):
        print(future.result())

print(results)
print(len(results))


# ============================================================
# 6. PRODUCER-CONSUMER WITH QUEUE
# ============================================================

import queue


task_queue = queue.Queue(maxsize=2)


def producer():
    for i in range(1, 11):
        task_queue.put(f"Task {i}")

    task_queue.put(None)


def consumer():
    while True:
        item = task_queue.get()

        if item is None:
            break

        print(f"Finished: {item}")


producer_thread = threading.Thread(target=producer)
consumer_thread = threading.Thread(target=consumer)

producer_thread.start()
consumer_thread.start()

producer_thread.join()
consumer_thread.join()