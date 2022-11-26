from time import sleep
import requests
import json
from queue import Queue

from nltk.data import find

def getData(url: str, data: dict, apiKey: str, timeout= 10) -> requests.Response:
    with open("./data/secrets.json", encoding="utf-8") as f:
        secret = json.load(f)
    resp = requests.get(url.format(**data, key= secret[apiKey]), timeout= timeout)
    del secret, f
    return resp

class thesaQueue:
    def __init__(self,
            order: int = 3,
            url: str = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{word}?key={key}",
            apiKey: str = "thesa",
            waitTime: float = 0.1,
            timeout: int = 10) -> None:
        self._url = url
        self._apiKey = apiKey
        self.wt = waitTime
        self.to = timeout
        self._qu = Queue()
        self.order = order
        self.store = None
    
    def add(self, item):
        self._add(item, self.order)

    def _add(self, item, order: int):
        if order > 0:
            self._qu.put((item, order))

    def setStore(self, store):
        assert store is not None
        self.store = store

    def __iter__(self):
        while not self._qu.empty():
            word, order = self._qu.get_nowait()

            if self.store is not None:
                if word in self.store:
                    print(f"Word {word} was already known using store")
                    for item in self.store[word]:
                        self._add(item, order - 1)
                    continue

            res = getData(self._url, {"word": word}, self._apiKey, self.to)

            if res.status_code == 200:
                flatten = set([item for group in res.json()[0]['meta']['syns'] for item in group])
                for item in flatten:
                    yield word, item, order
                    self._add(item, order - 1)
            else:
                print(f'Got error code: {res.status_code} when trying word {word}')
            sleep(self.wt)

    def __str__(self):
        return f"ThesaQu(order: {self.order}, wt: {self.wt}, to: {self.to}) with queue size: {self._qu.qsize()}"