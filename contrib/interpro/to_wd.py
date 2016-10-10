"""
For the class:
    domain: "string" # corresponds to a domain in PBB_Core.wd_property_store

For each field:
    dtype: {'external-id', 'string', 'math', 'wikibase-item', 'wikibase-property',
            'time', 'url', 'monolingualtext','quantity', 'commonsMedia', 'globe-coordinate',
            'label', 'description', 'alias'} # these three are handled separately
    property: None or 'PXXX' # can be None if dtype in {'label', 'description', 'alias'}
    references: d ?
    qualifiers: d ?
    value: actual value
"""

example = {'id': {'dtype': 'external-id', 'property': 'P2926', 'value': 'IPR001245'},
           'type': {'value': 'Domain'},  # won't be used
           'type_wdid': {'dtype': 'wikibase-item', 'property': 'P279', 'value': 'Q898273'},
           # change this to instance of?
           'name': {'dtype': 'label', 'value': 'Serine-threonine/tyrosine-protein kinase catalytic domain'},
           'description': {'dtype': 'description', 'value': {'en': 'InterPro Domain', 'fr': 'intrpeeaue domain'}},
           # dict[lang,descr] or str (default en)
           'short_name': {'dtype': 'alias', 'value': 'Ser-Thr/Tyr_kinase_cat_dom'},  # str or list of str
           'parent': {'value': 'IPR000719'},  # won't be used
           'parent_wdid': {'dtype': 'wikibase-item', 'property': 'P279', 'value': 'Q1234',
                           'references': [{'dtype': 'wikibase-item', 'property': 'P248', 'value': 'Q3047275'},
                                          # stated in
                                          {'dtype': 'string', 'property': 'P348', 'value': '1.2.3'},  # version
                                          ]}
           }

references = [{'dtype': 'wikibase-item', 'property': 'P248', 'value': 'Q3047275'},  # stated in
              {'dtype': 'string', 'property': 'P348', 'value': '1.2.3'},  # version
              ]

"""
{'drugX':
    { 'genes': [
        {'gene_id': '1234',
         'pmid': '11111',
         'source': 'ctdbase'},
         ...
         ]
    }
}
--->
{'drugX':
    { 'genes': {'value': ['Q1224','...'],
                'dtype': 'wikibase-item',
                'property': 'P1234',
                'references': [{'dtype': 'wikibase-item', 'property': 'P248', 'value': 'Qctdbase'} #stated in
                                {'dtype': 'string', 'property': 'Ppubmed', 'value': '11111'}]
                }
    }
}


"""


