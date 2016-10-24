"""
Modified from Tim's MicrobeBotProteins
https://bitbucket.org/sulab/wikidatabots/raw/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotProteins.py

example microbial protein:
https://www.wikidata.org/wiki/Q22291171
"""
from collections import defaultdict

from ProteinBoxBot_Core import PBB_login, PBB_Core
from tqdm import tqdm

from HelperBot import strain_info, go_props, go_evidence_codes, make_reference
from WDHelper import WDHelper
from local import WDUSER, WDPASS


def gene_encodes_statement(record, gene_qid, protein_qid, retrieved, login):
    # ncbi_gene_reference = make_reference('ncbi_gene', 'ncbi_gene', str(record['entrezgene']), retrieved)
    ensembl_protein_reference = make_reference('ensembl', 'ensemble_protein', record['ensembl']['protein'], retrieved)

    # gene
    gene_encodes = PBB_Core.WDItemID(value=protein_qid, prop_nr='P688', references=[ensembl_protein_reference])
    gene_id = PBB_Core.WDItemID(value=gene_qid, prop_nr='P351')

    wd_item_protein = PBB_Core.WDItemEngine(item_name='', domain='genes', data=[gene_id],
                                            fast_run=True, search_only=True,
                                            fast_run_base_filter={'P351': '', 'P703': strain_info['organism_wdid']})
    wd_item_protein.update(data=[gene_encodes])

    if wd_item_protein.create_new_item:
        raise ValueError("nooo!!")
    try:
        wd_item_protein.write(login=login)
        msg = "CREATE" if wd_item_protein.create_new_item else "UPDATE"
        log('INFO', record['_id'], '', msg, wd_item_protein.wd_item_id)
    except Exception as e:
        print(e)
        log('ERROR', record['_id'], type(e), str(e), wd_item_protein.wd_item_id)


def pre_filter_go(record):
    """
    go_processed': {'MF': {}, 'CC': {'GO:0005758': {'IEA', 'IDA'},
    'GO:0005737': {'IEA', 'IDA'}, 'GO:0005739': {'IEA'},
    'GO:0005829': {'IDA'}, 'GO:0005634': {'IEA', 'IDA'}}, 'BP': {}}
    """
    record['go_processed'] = dict()
    if 'go' not in record:
        record['go'] = dict()
    for level, go_terms in record['go'].items():
        # make them all lists
        go_terms = [go_terms] if isinstance(go_terms, dict) else go_terms
        # remove the 3 top level terms
        go_terms = [go_term for go_term in go_terms if
                    go_term['term'] not in {'molecular_function', 'biological_process', 'cellular_component'}]

        # combine evidence terms for duplicate go ids
        go_processed = defaultdict(set)
        for go_term in go_terms:
            go_processed[go_term['id']].add(go_term['evidence'])
        record['go_processed'][level] = dict(go_processed)


def protein_item(record, strain_info, gene_qid, go_wdid_mapping, retrieved, login):
    """
    generate pbb_core item object
    """

    item_name = '{} {}'.format(record['name'], record['locus_tag'])
    item_description = '{} protein found in {}'.format(strain_info['organism_type'], strain_info['organism_name'])

    statements = []
    # ncbi_gene_reference = make_reference('ncbi_gene', 'ncbi_gene', str(record['entrezgene']), retrieved)
    ensembl_protein_reference = make_reference('ensembl', 'ensemble_protein', record['ensembl']['protein'], retrieved)

    # generate go term claims
    pre_filter_go(record)
    print(record['_id'])
    for go_type, go_records in record['go_processed'].items():
        goprop = go_props[go_type]

        for go_id, go_evidences in go_records.items():
            go_wdid = go_wdid_mapping[go_id]
            evidence_statements = []
            for go_evidence in go_evidences:
                evidence_wdid = go_evidence_codes[go_evidence]
                evidence_statements.append(PBB_Core.WDItemID(value=evidence_wdid, prop_nr='P459',
                                                             is_qualifier=True))  # determination method
            statements.append(
                PBB_Core.WDItemID(value=go_wdid, prop_nr=goprop, references=[ensembl_protein_reference],
                                  qualifiers=evidence_statements))

    WD_Item_CLAIMS = {
        'P703': strain_info['organism_wdid'],  # found in taxon
        'P279': 'Q8054',  # subclass of protein,
        'P702': gene_qid  # encodes gene
    }
    for k, v in WD_Item_CLAIMS.items():
        statements.append(PBB_Core.WDItemID(value=v, prop_nr=k, references=[ensembl_protein_reference]))

    # set refseq protein id
    statements.append(PBB_Core.WDString(value=record['refseq']['protein'], prop_nr='P637',
                                        references=[ensembl_protein_reference]))
    # set uniprot id
    statements.append(PBB_Core.WDString(value=record['uniprot']['Swiss-Prot'], prop_nr='P352',
                                        references=[ensembl_protein_reference]))
    # set ensembl protein id
    statements.append(PBB_Core.WDString(value=str(record['ensembl']['protein']), prop_nr='P705',
                                        references=[ensembl_protein_reference]))

    wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='proteins', data=statements,
                                            append_value=['P279'],
                                            fast_run=True,
                                            fast_run_base_filter={'P352': '', 'P703': strain_info['organism_wdid']})
    wd_item_protein.set_label(item_name)
    wd_item_protein.set_description(item_description, lang='en')
    wd_item_protein.set_aliases([record['symbol'], record['locus_tag']])

    try:
        wd_item_protein.write(login=login)
        msg = "CREATE" if wd_item_protein.create_new_item else "UPDATE"
        log('INFO', record['_id'], '', msg, wd_item_protein.wd_item_id)
    except Exception as e:
        print(e)
        log('ERROR', record['_id'], type(e), str(e), wd_item_protein.wd_item_id)


def log(level, main_data_id, exception_type, message, wd_id):
    PBB_Core.WDItemEngine.log(level,
                              '{main_data_id}, "{exception_type}", "{message}", {wd_id}'.format(
                                  main_data_id=main_data_id, exception_type=exception_type, message=message,
                                  wd_id=wd_id))


def run(records, retrieved):
    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

    # get all entrez gene id -> wdid mappings, where found in taxon is this strain
    gene_wdid_mapping = WDHelper().id_mapper("P351", (("P703", strain_info['organism_wdid']),))

    # get all goID to wdid mappings
    go_wdid_mapping = WDHelper().id_mapper("P686")

    for n, record in tqdm(enumerate(records), desc=strain_info['organism_name'], total=records.count()):
        gene_qid = gene_wdid_mapping[str(record['entrezgene'])]
        protein_item(record, strain_info, gene_qid, go_wdid_mapping, retrieved, login)

    # get all ensembl gene id -> wdid mappings, where found in taxon is this strain
    protein_wdid_mapping = WDHelper().id_mapper("P705", (("P703", strain_info['organism_wdid']),))

    for n, record in tqdm(enumerate(records), desc=strain_info['organism_name'], total=records.count()):
        gene_qid = gene_wdid_mapping[str(record['entrezgene'])]
        protein_qid = protein_wdid_mapping[record['ensemble']['protein']]
        gene_encodes_statement(record, gene_qid, protein_qid, retrieved, login)


def main(log_dir=None):
    import biothings
    import config
    from biothings.utils.mongo import get_src_db, get_src_dump

    biothings.config_for_app(config)
    if log_dir:
        PBB_Core.WDItemEngine.log_file_path = log_dir

    collection = get_src_db().yeast

    src_dump = get_src_dump()
    src_doc = src_dump.find_one({'_id': 'mygene'})
    retrieved = src_doc["release"]
    print(retrieved)

    run(collection.find({'type_of_gene': 'protein-coding', '_id': '856785'}), retrieved)


if __name__ == "__main__":
    main()
