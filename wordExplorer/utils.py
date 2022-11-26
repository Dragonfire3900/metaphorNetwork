from .thesa import thesaQueue
import json
import gensim.downloader as api

def getWordData(words:str, loc:str= './data/synonyms/', order: int= 3, waitTime: float= 0.1):
    crawler = thesaQueue(order, waitTime= waitTime)
    crawler.add(words)

    try:
        with open(loc + f'{words}.json', 'r', encoding= 'utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    
    crawler.setStore(data)
    
    for source, subject, order in crawler:
        if source not in data:
            data[source] = set([subject])
        else:
            data[source].add(subject)
        print(f'Eval: {source}-{subject}-{order}')
    
    data = {key:list(val) for key, val in data.items()}

    with open(loc + f'{words}.json', "w", encoding="utf-8") as f:
        json.dump(data, f)

    return data

def loadWord2Vec(mName: str = 'word2vec-google-news-300'):
    """Creates an environment to use a pretrained word2vec model using gensim. Returns a function to interact with that model

    Args:
        mName (str, optional): The name of the model to load in gensim. Defaults to 'word2vec-google-news-300'.

    Returns:
        callable: A function to interact with the word2vec model
    """
    model = api.load(mName)

    def getSimilarity(data: dict, fun: callable = lambda x: x + 1, default: float = 1.01):
        """Calculates the similarity between all of the words in a given dictionary

        Args:
            data (dict): A dictionary of lists of strings. Gives all of the relationships to calculate the similarity for using the model
            fun (callable, optional): A transformation applied to the similarity after it's been calculated. Defaults to lambdax:x+1.
            default (float, optional): The default value if the words aren't in the word2vec's vocabulary. Defaults to 1.01.

        Returns:
            dict[tuple[str, str], float]: A dictionary which gives the weights of word pairs
        """
        weights = {}

        for key in data.keys():
            for item in data[key]:
                try:
                    weights[(key, item)] = fun(model.similarity(key, item))
                except KeyError:
                    weights[(key, item)] = default
        return weights
    return getSimilarity