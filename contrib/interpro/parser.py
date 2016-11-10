"""
This should parse a raw file into json/mongo
"""
import gzip
import os
import subprocess
from itertools import groupby

import lxml.etree as et
from dateutil import parser as dup


from tqdm import tqdm

#DATA_DIR = "/home/gstupp/projects/wikidatabots/interproscan/data"


def parse_release_info(data_folder):
    file_path = os.path.join(data_folder, "interpro.xml.gz")
    f = gzip.GzipFile(file_path)
    context = iter(et.iterparse(f, events=("start", "end")))
    event, root = next(context)

    for event, db_item in context:
        if event == "end" and db_item.tag == "dbinfo":
            db_item.attrib['_id'] = db_item.attrib['dbname']
            yield dict(db_item.attrib)
        root.clear()


def parse_interpro_xml(data_folder):
    file_path = os.path.join(data_folder, "interpro.xml.gz")
    f = gzip.GzipFile(file_path)
    context = iter(et.iterparse(f, events=("start", "end")))
    event, root = next(context)

    for event, itemxml in context:
        if event == "end" and itemxml.tag == "interpro":
            item = dict(name=itemxml.find('name').text, **itemxml.attrib)
            item['_id'] = item['id']
            item['protein_count'] = int(item['protein_count'])
            parents = [x.attrib['ipr_ref'] for x in itemxml.find("parent_list").getchildren()] if itemxml.find(
                "parent_list") is not None else None
            children = [x.attrib['ipr_ref'] for x in itemxml.find("child_list").getchildren()] if itemxml.find(
                "child_list") is not None else None
            contains = [x.attrib['ipr_ref'] for x in itemxml.find("contains").getchildren()] if itemxml.find(
                "contains") is not None else None
            found_in = [x.attrib['ipr_ref'] for x in itemxml.find("found_in").getchildren()] if itemxml.find(
                "found_in") is not None else None
            if parents:
                assert len(parents) == 1
                item['parent'] = parents[0]
            item['children'] = children
            item['contains'] = contains
            item['found_in'] = found_in
            yield item
        root.clear()


def parse_protein_ipr(data_folder, ipr_items, debug=False):
    file_path = os.path.join(data_folder, "protein2ipr.dat.gz")
    print(file_path)
    p = subprocess.Popen(["zcat", file_path], stdout=subprocess.PIPE).stdout
    d = {}
    p2ipr = map(lambda x: x.decode('utf-8').rstrip().split('\t'), p)
    n = 0
    for key, lines in tqdm(groupby(p2ipr, key=lambda x: x[0]), total=51536456, miniters=1000000):
        # the total is just for a time estimate. Nothing bad happens if the total is wrong
        n += 1
        if debug and n > 1000:
            break
        protein = []
        for line in lines:
            uniprot_id, interpro_id, name, ext_id, start, stop = line
            protein.append({'uniprot_id': uniprot_id, 'interpro_id': interpro_id, 'name': name,
                            'ext_id': ext_id, 'start': start, 'stop': stop})

        # group list of domain in a protein by ipr
        prot_items = [ipr_items[x] for x in set(x['interpro_id'] for x in protein)]
        # Of all families, which one is the most precise? (remove families that are parents of any other family in this list)
        families = [x for x in prot_items if x['type'] == "Family"]
        families_id = set(x['id'] for x in families)
        parents = set(family['parent'] for family in families if 'parent' in family)
        # A protein be in multiple families. ex: http://www.ebi.ac.uk/interpro/protein/A0A0B5J454
        specific_families = families_id - parents
        has_part = [x['id'] for x in prot_items if x['type'] != "Family"]
        yield {'_id': key, 'subclass': list(specific_families), 'has_part': list(has_part)}


"""
d = {"A0A0H3JGZ6": [
{
  "ext_id": "G3DSA:3.40.50.360",
  "uniprot_id": "A0A0H3JGZ6",
  "name": "Flavoprotein-like domain",
  "start": "1",
  "interpro_id": "IPR029039",
  "stop": "174"
},
{
  "ext_id": "SSF52218",
  "uniprot_id": "A0A0H3JGZ6",
  "name": "Flavoprotein-like domain",
  "start": "1",
  "interpro_id": "IPR029039",
  "stop": "143"
}
]}
"""