from itertools import chain

import rdflib
from rdflib.plugins.sparql import prepareQuery
from rdflib.term import URIRef
from tqdm import tqdm


def get_all_ids(g):
    # get all ids that could have an equivalent class
    q = prepareQuery("""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    select * where {
      ?s owl:equivalentClass|^owl:equivalentClass ?x .
      filter (?s != ?x)
    }
    """)
    result = g.query(q)
    all_ids = set(chain(*[(str(r[0]), str(r[1])) for r in result]))

    return all_ids



def do_queries(g, ids):
    # get all (symetrical, follow chains) equivalent classes for each id
    d = []
    for id in tqdm(ids):
        q = prepareQuery("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
        select * where {
            ?s (owl:equivalentClass|^owl:equivalentClass)* ?x .
        }""")
        result = g.query(q, initBindings={'s': URIRef(id)})
        equiv_class = [x.split("/")[-1] for x in set(chain(*list(result)))]
        d.append({'_id': id.split("/")[-1].replace("_", ":"), 'equivalent_class': [x.replace("_", ":") for x in equiv_class]})
    return d


def parse(file_path):
    g = rdflib.Graph()
    g.parse(file_path)

    all_ids = get_all_ids(g)
    #all_doids = {x for x in all_ids if x.startswith("DOID")}
    #all_umls = {x for x in all_ids if x.startswith("UMLS")}
    d = do_queries(g, all_ids)
    for x in d:
        yield x


if __name__ == "__main__":
    d = list(parse("/home/gstupp/projects/biothings/wikidata/data/20161019/mondo/mondo.owl"))

    from pymongo import MongoClient
    db = MongoClient().mondo.mondo
    db.drop()
    db.insert_many(d)

    """
    {'_id': 'DOID:1386',
     'equivalent_class': ['MESH:D000012',
      'Orphanet:14',
      'DOID:1386',
      'OMIM:200100',
      'UMLS:C1862596',
      'UMLS:C0000744',
      'UMLS:C0020597']}
    """

def summary():
    from collections import Counter
    from pymongo import MongoClient
    db = MongoClient().mondo.mondo
    Counter([len([x for x in doc['equivalent_class'] if x.startswith("DOID")]) for doc in db.find({'_id':{'$regex':'^UMLS'}})])
    Counter([len([x for x in doc['equivalent_class'] if x.startswith("UMLS")]) for doc in db.find({'_id': {'$regex': '^DOID'}})])
    Counter([len([x for x in doc['equivalent_class'] if x.startswith("Orphanet")]) for doc in db.find({'_id': {'$regex': '^DOID'}})])

    db.find_one('DOID:1386')
    db.find_one('UMLS:C0000744')
    db.find_one('DOID:0002116')