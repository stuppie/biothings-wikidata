from typing import List

import networkx
from .obo import read_obo
from biothings.utils.common import list2dict
from networkx.readwrite import json_graph


print("Dont use this for equaivalent class because it doesn't have it. use owl file")

def graph_to_d(graph):
    """
    :param graph: A networkx graph made from reading ontology
    :type graph: networkx.classes.multidigraph.MultiDiGraph
    :return:
    """
    node_link_data = json_graph.node_link_data(graph)
    nodes = node_link_data['nodes']

    idx_id = {idx: node['id'] for idx, node in enumerate(nodes)}
    for link in node_link_data['links']:
        # store the edges (links) within the graph
        key = link['key']
        source = link['source']
        target = link['target']

        if key not in nodes[source]:
            nodes[source][key] = set()
        nodes[source][key].add(idx_id[target])

    # for mongo insertion
    for node in nodes:
        node['_id'] = node['id']
        del node['id']
        for k, v in node.items():
            if isinstance(v, set):
                node[k] = list(v)
    d = {node['_id']: node for node in nodes}

    return d


def parse(file_path):
    graph = read_obo(open(file_path).readlines())
    d = graph_to_d(graph)
    for v in d.values():
        yield v


if __name__ == "__main__":
    d = parse("/home/gstupp/projects/biothings/wikidata/data/20161018/mondo/mondo.obo")