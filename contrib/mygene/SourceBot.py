"""
Get data from the mygene/biothings mongo collections
Ready for use by wikidata bots, by merging some sources and tagging each field with a reference
"""

"""
# Data sources:
Mongo on su05
db=genedoc_src

db.ensembl_genomic_pos.findOne({'_id':'1466404'})
{
	"_id" : "1466404",
	"genomic_pos" : {
		"start" : 5605,
		"end" : 5775,
		"chr" : "XII",
		"strand" : 1
	}
}

db.ensembl_acc.findOne({'_id':'1466404'})
{
	"_id" : "1466404",
	"ensembl" : {
		"gene" : "YLL066W-B",
		"translation" : [
			{
				"rna" : "YLL066W-B",
				"protein" : "YLL066W-B"
			}
		],
		"transcript" : "YLL066W-B",
		"protein" : "YLL066W-B"
	}
}

> db.entrez_gene.findOne({_id:"1466404"})
{
	"_id" : "1466404",
	"name" : "hypothetical protein",
	"_timestamp" : ISODate("2015-10-05T00:00:00Z"),
	"entrezgene" : 1466404,
	"taxid" : 559292,
	"symbol" : "YLL066W-B",
	"locus_tag" : "YLL066W-B",
	"SGD" : "S000028672",
	"type_of_gene" : "protein-coding"
}

> db.entrez_go.findOne({_id:"1466404"})
{
	"_id" : "1466404",
	"go" : {
		"CC" : {
			"term" : "cellular_component",
			"id" : "GO:0005575",
			"evidence" : "ND"
		},
		"BP" : {
			"term" : "biological_process",
			"id" : "GO:0008150",
			"evidence" : "ND"
		},
		"MF" : {
			"term" : "molecular_function",
			"id" : "GO:0003674",
			"evidence" : "ND"
		}
	}

> db.entrez_refseq.findOne({_id:"1466404"})
{
	"_id" : "1466404",
	"refseq" : {
		"rna" : "NM_001184605.1",
		"protein" : "NP_878115.1",
		"genomic" : "NC_001144.5",
		"translation" : {
			"rna" : "NM_001184605.1",
			"protein" : "NP_878115.1"
		}
	}
}


> db.uniprot.findOne({_id:"1466404"})
{ "_id" : "1466404", "uniprot" : { "Swiss-Prot" : "Q8TGJ7" } }

Example doc:
{'SGD': 'S000002230',
 '_id': '851487',
  'ensembl': {'gene': 'YDL072C',
  'protein': 'YDL072C',
  'transcript': 'YDL072C',
  'translation': [{'protein': 'YDL072C', 'rna': 'YDL072C'}]},
 'entrezgene': 851487,
 'genomic_pos': {'chr': 'IV', 'end': 330447, 'start': 329836, 'strand': -1},
 'go': {'BP': {'evidence': 'IEA', 'id': 'GO:0006810', 'term': 'transport'},
  'CC': [{'evidence': 'IDA',
    'id': 'GO:0005783',
    'pubmed': [11914276, 20378542, 26928762],
    'term': 'endoplasmic reticulum'},
   {'evidence': 'IEA', 'id': 'GO:0005783', 'term': 'endoplasmic reticulum'}],
  'MF': {'evidence': 'ND', 'id': 'GO:0003674', 'term': 'molecular_function'}},
 'locus_tag': 'YDL072C',
 'name': 'Yet3p',
 'refseq': {'genomic': 'NC_001144.5',
  'protein': 'NP_878115.1',
  'rna': 'NM_001184605.1',
  'translation': {'protein': 'NP_878115.1', 'rna': 'NM_001184605.1'}},
 'symbol': 'YET3',
 'taxid': 559292,
 'type_of_gene': 'protein-coding',
 'uniprot': {'Swiss-Prot': 'Q8TGJ7'}}

Example doc with source tags:
{'SGD': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
         '@value': 'S000002230'},
 '_id': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
         '@value': '851487'},
 'ensembl': {'@source': {'_id': 'ensembl',
                         'release': 86,
                         'timestamp': '20161005'},
             '@value': {'gene': 'YDL072C',
                        'protein': 'YDL072C',
                        'transcript': 'YDL072C',
                        'translation': [{'protein': 'YDL072C',
                                         'rna': 'YDL072C'}]}},
 'entrezgene': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
                '@value': 851487},
 'genomic_pos': {'@source': {'_id': 'ensembl',
                             'release': 86,
                             'timestamp': '20161005'},
                 '@value': {'chr': 'IV',
                            'end': 330447,
                            'start': 329836,
                            'strand': -1}},
 'go': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
        '@value': {'BP': [{'evidence': 'IEA',
                           'id': 'GO:0006810',
                           'term': 'transport'},
                          {'evidence': 'IEA',
                           'id': 'GO:0016192',
                           'term': 'vesicle-mediated transport'}],
                   'CC': [{'evidence': 'IDA',
                           'id': 'GO:0005783',
                           'pubmed': [11914276, 20378542, 26928762],
                           'term': 'endoplasmic reticulum'}],
                   'MF': {'evidence': 'ND',
                          'id': 'GO:0003674',
                          'term': 'molecular_function'}}},
 'locus_tag': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
               '@value': 'YDL072C'},
 'name': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
          '@value': 'Yet3p'},
 'symbol': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
            '@value': 'YET3'},
 'taxid': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
           '@value': 559292},
 'type_of_gene': {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
                  '@value': 'protein-coding'},
 'uniprot': {'@source': {'_id': 'uniprot', 'timestamp': '20161006'},
             '@value': {'Swiss-Prot': 'Q07451'}},
 "refseq" : {'@source': {'_id': 'entrez', 'timestamp': '20161023'},
             '@value': {
                        "rna" : "NM_001184605.1",
                        "protein" : "NP_878115.1",
                        "genomic" : "NC_001144.5", # this is the full chromosome #TODO use this!!!
                        "translation" : {
                            "rna" : "NM_001184605.1",
                            "protein" : "NP_878115.1"
                        }
            }
        }
}

"""

from pymongo import MongoClient


def tag_dict_with_source(d, source):
    return {k: {'@value': v, '@source': source} for k, v in d.items()}


def get_data_from_mygene(taxid=559292):
    """
    Get all yeast gene/protein information from mygene source collections
    """

    db = MongoClient("su05").genedoc_src
    sources = get_source_versions()
    docs = list(tag_dict_with_source(d, sources['Entrez']) for d in db.entrez_gene.find({'taxid': taxid}))

    for doc in docs:
        entrez_id = str(doc['entrezgene']['@value'])
        d = db.ensembl_genomic_pos.find_one(entrez_id) or {}
        doc.update(tag_dict_with_source(d, sources['Ensembl']))
        d = db.ensembl_acc.find_one(entrez_id) or {}
        doc.update(tag_dict_with_source(d, sources['Ensembl']))
        d = db.entrez_go.find_one(entrez_id) or {}
        doc.update(tag_dict_with_source(d, sources['Entrez']))
        d = db.uniprot.find_one(entrez_id) or {}
        doc.update(tag_dict_with_source(d, sources['Uniprot']))
        d = db.entrez_refseq.find_one(entrez_id) or {}
        doc.update(tag_dict_with_source(d, sources['Entrez']))

    return docs


def get_source_versions():
    db = MongoClient("su05").genedoc_src
    source_names = {'Ensembl', 'Entrez', 'Uniprot'}
    sources = {source: db.src_dump.find_one({"_id": source.lower()}, {'release': True, 'timestamp': True})
               for source in source_names}
    for source, source_dict in sources.items():
        source_dict['_id'] = source
    return sources
