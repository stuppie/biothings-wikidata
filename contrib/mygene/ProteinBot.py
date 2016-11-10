"""
Modified from Tim's MicrobeBotProteins
https://bitbucket.org/sulab/wikidatabots/raw/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotProteins.py

example microbial protein:
https://www.wikidata.org/wiki/Q22291171
"""
import copy
import json
from datetime import datetime

from ProteinBoxBot_Core import PBB_login, PBB_Core, PBB_Helpers
from interproscan.WDHelper import WDHelper
from tqdm import tqdm

from HelperBot import strain_info, go_props, go_evidence_codes, format_msg, make_ref_source, try_write
from SourceBot import get_data_from_mygene, get_source_versions
from local import WDUSER, WDPASS

__metadata__ = {'name': 'YeastBot_Protein',
                'maintainer': 'GSS',
                'tags': ['yeast', 'protein'],
                'properties': ['P703', 'P279', 'P2548', 'P351', 'P2393', 'P594', 'P644', 'P645', 'P1057']
                }

ENTREZ_PROP = "P351"

source_ref_id = {'ensembl': 'ensembl_protein',
                 'entrez': 'entrez_gene',
                 'swiss_prot': 'uniprot'}


def gene_encodes_statement(gene_qid, protein_qid, id_prop, external_id, source, login):
    """

    :param gene_qid:
    :param protein_qid:
    :param id_prop:
    :param external_id:
    :param source:
    :param login:
    :return:
    """
    ensembl_protein_reference = make_ref_source(source, id_prop, external_id)

    # gene
    gene_encodes = PBB_Core.WDItemID(value=protein_qid, prop_nr='P688', references=[ensembl_protein_reference])

    wd_item_protein = PBB_Core.WDItemEngine(wd_item_id=gene_qid, domain='genes', data=[gene_encodes],
                                            fast_run=True,
                                            fast_run_base_filter={'P351': '', 'P703': strain_info['organism_wdid']})

    if wd_item_protein.create_new_item:
        raise ValueError("nooo!!")

    try_write(wd_item_protein, external_id, id_prop, login)



def preprocess_go(record):
    if 'go' not in record:
        record['go'] = {'@value': {}}
    for level, go_terms in record['go']['@value'].items():
        # make them all lists
        go_terms = [go_terms] if isinstance(go_terms, dict) else go_terms
        # remove the 3 top level terms
        go_terms = [go_term for go_term in go_terms if
                    go_term['term'] not in {'molecular_function', 'biological_process', 'cellular_component'}]
        # make pubmed field list
        for go_term in go_terms:
            if 'pubmed' not in go_term:
                go_term['pubmed'] = []
            go_term['pubmed'] = [go_term['pubmed']] if isinstance(go_term['pubmed'], int) else go_term['pubmed']
        record['go']['@value'][level] = go_terms


def protein_item(record, strain_info, gene_qid, go_wdid_mapping, login, add_pubmed):
    """
    generate pbb_core item object
    """

    item_name = '{} {}'.format(record['name']['@value'], record['ensembl']['@value']['protein'])
    item_description = '{} protein found in {}'.format(strain_info['organism_type'], strain_info['organism_name'])

    s = []

    ############
    # external IDs
    ############
    # will be used for reference statements
    external_ids = {'entrez_gene': str(record['entrezgene']['@value']),
                    'ensembl_protein': record['ensembl']['@value']['protein'],
                    'ensembl_gene': record['ensembl']['@value']['gene'],
                    'refseq_protein': record['refseq']['@value']['protein'],
                    'uniprot': record['uniprot']['@value']['Swiss-Prot']}

    # ensembl protein id
    ensembl_ref = make_ref_source(record['ensembl']['@source'], 'ensembl_protein', external_ids['ensembl_protein'])
    s.append(PBB_Core.WDString(external_ids['ensembl_protein'], 'P705', references=[ensembl_ref]))
    # refseq protein id
    refseq_ref = make_ref_source(record['refseq']['@source'], 'refseq_protein', external_ids['refseq_protein'])
    s.append(PBB_Core.WDString(external_ids['refseq_protein'], 'P637', references=[refseq_ref]))
    # uniprot id
    uniprot_ref = make_ref_source(record['uniprot']['@source'], 'uniprot', external_ids['uniprot'])
    s.append(PBB_Core.WDString(external_ids['uniprot'], 'P352', references=[uniprot_ref]))

    ############
    # GO terms
    # TODO: https://www.wikidata.org/wiki/Q3460832
    ############

    preprocess_go(record)
    print(record)
    go_source = record['go']['@source']
    go_id_prop = source_ref_id[go_source['_id']]
    reference = make_ref_source(go_source, go_id_prop, external_ids[go_id_prop])
    for go_level, go_records in record['go']['@value'].items():
        level_wdid = go_props[go_level]
        for go_record in go_records:
            go_wdid = go_wdid_mapping[go_record['id']]
            evidence_wdid = go_evidence_codes[go_record['evidence']]
            evidence_statement = PBB_Core.WDItemID(value=evidence_wdid, prop_nr='P459',is_qualifier=True)
            this_reference = copy.deepcopy(reference)
            if add_pubmed:
                for pubmed in go_record['pubmed']:
                    pmid_wdid = PBB_Helpers.PubmedStub(pubmed).create(login)
                    this_reference.append(PBB_Core.WDItemID(pmid_wdid, 'P248', is_reference=True))
            s.append(PBB_Core.WDItemID(go_wdid, level_wdid, references=[this_reference], qualifiers=[evidence_statement]))


    ############
    # statements with no referencable sources (make by hand, for now...)
    ############
    # subclass of protein
    s.append(PBB_Core.WDItemID('Q8054', 'P279', references=[ensembl_ref]))

    # found in taxon
    s.append(PBB_Core.WDItemID(strain_info['organism_wdid'], 'P703', references=[ensembl_ref]))

    # encodes gene
    s.append(PBB_Core.WDItemID(gene_qid, 'P702', references=[ensembl_ref]))


    try:
        wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='proteins', data=s,
                                                append_value=['P279'],
                                                fast_run=True,
                                                fast_run_base_filter={'P352': '', 'P703': strain_info['organism_wdid']})
        wd_item_protein.set_label(item_name)
        wd_item_protein.set_description(item_description, lang='en')
        wd_item_protein.set_aliases([record['symbol']['@value'], record['locus_tag']['@value']])
    except Exception as e:
        print(e)
        PBB_Core.WDItemEngine.log("ERROR", format_msg(record['entrezgene']['@value'], str(e), None, ENTREZ_PROP))
        return

    try_write(wd_item_protein, record['entrezgene']['@value'], 'P351', login)


def run(login, records, add_pubmed):

    # get all entrez gene id -> wdid mappings, where found in taxon is this strain
    gene_wdid_mapping = WDHelper().id_mapper("P351", (("P703", strain_info['organism_wdid']),))

    # get all goID to wdid mappings
    go_wdid_mapping = WDHelper().id_mapper("P686")

    for record in tqdm(records, desc=strain_info['organism_name']):
        entrez_gene = str(record['entrezgene']['@value'])
        if entrez_gene not in gene_wdid_mapping:
            PBB_Core.WDItemEngine.log("ERROR", format_msg(record['_id']['@value'], "gene_not_found", None, ENTREZ_PROP))
            continue
        gene_qid = gene_wdid_mapping[entrez_gene]
        protein_item(record, strain_info, gene_qid, go_wdid_mapping, login, add_pubmed)


def run_encodes(login, records):
    # get all entrez gene id -> wdid mappings, where found in taxon is this strain
    gene_wdid_mapping = PBB_Helpers.id_mapper("P351", (("P703", strain_info['organism_wdid']),))

    # get all ensembl protein id -> wdid mappings, where found in taxon is this strain
    protein_wdid_mapping = PBB_Helpers.id_mapper("P705", (("P703", strain_info['organism_wdid']),))

    for record in tqdm(records, desc=strain_info['organism_name']):
        entrez_gene = str(record['entrezgene']['@value'])
        if entrez_gene not in gene_wdid_mapping:
            PBB_Core.WDItemEngine.log("ERROR", format_msg(record['_id']['@value'], "gene_not_found", None, ENTREZ_PROP))
            continue
        gene_qid = gene_wdid_mapping[entrez_gene]
        protein_qid = protein_wdid_mapping[record['ensembl']['@value']['protein']]
        gene_encodes_statement(gene_qid, protein_qid, 'ncbi_gene', entrez_gene, record['ensembl']['@source'], login)


def main(log_dir="./logs", run_id=None, add_pubmed=True):
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    __metadata__['run_id'] = run_id
    log_name = 'YeastBot_protein-{}.log'.format(run_id)
    __metadata__['log_name'] = log_name
    __metadata__['sources'] = get_source_versions()

    records = get_data_from_mygene()

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)
    if PBB_Core.WDItemEngine.logger is not None:
        PBB_Core.WDItemEngine.logger.handles = []
    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
    run(login, records, add_pubmed)

    log_name = 'YeastBot_encodes-{}.log'.format(run_id)
    __metadata__['log_name'] = log_name
    __metadata__['name'] = "YeastBot_Encodes"
    if PBB_Core.WDItemEngine.logger is not None:
        PBB_Core.WDItemEngine.logger.handles = []
    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
    run_encodes(login, records)


if __name__ == "__main__":
    main()
