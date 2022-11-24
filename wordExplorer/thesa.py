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
            waitTime: int = 10,
            timeout: int = 10) -> None:
        self._url = url
        self._apiKey = apiKey
        self.wt = waitTime
        self.to = timeout
        self._qu = Queue()
        self.order = order
    
    def add(self, item):
        self._add(item, self.order)

    def _add(self, item, order: int):
        if order > 0:
            self._qu.put((item, order))

    def __iter__(self):
        while not self._qu.empty():
            word, order = self._qu.get_nowait()

            res = getData(self._url, {"word": word}, self._apiKey, self.to)

            if res.status_code == 200:
                flatten = set([item for group in res.json()[0]['meta']['syns'] for item in group])
                for item in flatten:
                    yield word, item
                    self._add(item, order - 1)
            else:
                print(f'Got error code: {res.status_code} when trying word {word}')