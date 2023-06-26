from time import sleep
from typing import List
import requests
import json
from queue import Queue
from abc import ABC

def getData(url: str, data: dict, apiKey: str, timeout= 10) -> requests.Response:
    with open("./data/secrets.json", encoding="utf-8") as f:
        secret = json.load(f)
    resp = requests.get(url.format(**data, key= secret[apiKey]), timeout= timeout)
    del secret, f
    return resp

class thesaurusCrawler(ABC):
    def __init__(self,
            order: int = 1,
            url: str = None,
            apiKey: str = None,
            waitTime: float = 0.1,
            timeout: int = 10) -> None:
        super().__init__()
        assert apiKey is not None
        assert url is not None
        
        if order >= 0:
            self.order = order
        else:
            self.order = 1

        self._url = url
        self._key = apiKey

        if waitTime > 0.0:
            self.wt = waitTime
        else:
            self.wt = 0.1
        
        if timeout > 0:
            self.to = timeout
        else:
            self.to = 10

        self._qu = Queue()
        self.store = None

    def add(self, item):
        self._add(item, self.order)

    def _add(self, item, order: int):
        if order > 0:
            self._qu.put((item, order))

    def setStore(self, store):
        assert store is not None
        self.store = store

    def iterJson(self, resJson: List[dict], currWord: str) -> str:
        """A generator which yields individual elements given a json response that you would like to add to the crawler

        Args:
            resJson (List[dict]): The raw json response
            currWord (str): The current word which is being evaluated

        Raises:
            NotImplementedError: Only raised in abstract base class

        Returns:
            str: Yields a single string which you would like to search next
        """
        raise NotImplementedError()

    def __iter__(self):
        while not self._qu.empty():
            word, order = self._qu.get_nowait()

            if self.store is not None:
                if word in self.store:
                    # print(f"Word {word} was already known using store")
                    for item in self.store[word]:
                        self._add(item, order - 1)
                    continue

            res = getData(self._url, {"word": word}, self._key, self.to)

            if res.status_code == 200:
                flatten = []
                for item in self.iterJson(res.json(), word):
                    if item != word:
                        flatten.append(item)
                flatten = set(flatten)
                for item in flatten:
                    yield word, item, order
                    self._add(item, order - 1)
            else:
                print(f'Got error code: {res.status_code} when trying word {word}')
            sleep(self.wt)

    def __str__(self):
        return f"Thesaurus Crawler(order: {self.order}, wt: {self.wt}, to: {self.to}) with queue size: {self._qu.qsize()}"

class websterCrawl(thesaurusCrawler):
    def __init__(self, order: int = 3, waitTime: float = 0.1, timeout: int = 10) -> None:
        super().__init__(
            order,
            "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{word}?key={key}",
            "thesa",
            waitTime,
            timeout
        )
    
    def iterJson(self, resJson: List[dict], currWord: str) -> str:
        for defin in resJson:
            if defin['meta']['id'].lower() != currWord.lower():
                continue
            for group in defin['meta']['syns']:
                for item in group:
                    if item != currWord:
                        yield item

    def __str__(self):
        return f"Thesa Crawler(order: {self.order}, wt: {self.wt}, to: {self.to}) with queue size: {self._qu.qsize()}"

class bighugeCrawl(thesaurusCrawler):
    def __init__(self, order: int = 1, waitTime: float = 0.1, timeout: int = 10) -> None:
        super().__init__(
            order,
            "https://words.bighugelabs.com/api/2/{key}/{word}/json",
            "bighugelabs",
            waitTime,
            timeout
        )

    def iterJson(self, resJson: List[dict], currWord: str) -> str:
        for group in resJson.values():
            for item in group.get('syn', []):
                yield item