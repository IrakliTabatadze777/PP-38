
import requests
import time
import threading
import multiprocessing

global_lst = []
lock = threading.Lock()

def fetch_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    if response.ok:
        with lock:
            global_lst.append(response.json()['name'])

        return response.json()





def main():
    BASE_API_URL = 'https://rickandmortyapi.com/api/character/{id}'


    # fetch_data('https://rickandmortyapi.com/api/character/1')
    # fetch_data('https://rickandmortyapi.com/api/character/2')
    # fetch_data('https://rickandmortyapi.com/api/character/3')
    # fetch_data('https://rickandmortyapi.com/api/character/4')
    # fetch_data('https://rickandmortyapi.com/api/character/5')
    # fetch_data('https://rickandmortyapi.com/api/character/6')
    # fetch_data('https://rickandmortyapi.com/api/character/7')
    # fetch_data('https://rickandmortyapi.com/api/character/8')
    # fetch_data('https://rickandmortyapi.com/api/character/9')

    # for i in range(1, 21):
    #     response = fetch_data(BASE_API_URL.format(id=i))
    #     global_lst.append(response['name'])


    threads = []

    for i in range(1, 21):
        thread = threading.Thread(target=fetch_data, args=(BASE_API_URL.format(id=i),))
        threads.append(thread)


    for thread in threads:
        thread.start()


    for thread in threads:
        thread.join()

    print(threading.active_count())
    print(threading.enumerate())


start_time = time.time()
main()
end_time = time.time()

print(global_lst)
print(len(global_lst))
print(end_time - start_time)

