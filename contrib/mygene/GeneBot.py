"""
Modified from Tim's MicrobeBotGenes
https://bitbucket.org/sulab/wikidatabots/raw/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotGenes.py

s288c chromosomes:
https://www.ncbi.nlm.nih.gov/genome/?term=txid559292[Organism:noexp]

example microbial gene:
https://www.wikidata.org/wiki/Q23162696

# Example item
gene_record = {
    "_id": "1466404",
    "go": {
        "MF": {
            "id": "GO:0003674",
            "term": "molecular_function",
            "evidence": "ND"
        },
        "BP": {
            "id": "GO:0008150",
            "term": "biological_process",
            "evidence": "ND"
        },
        "CC": {
            "id": "GO:0005575",
            "term": "cellular_component",
            "evidence": "ND"
        }
    },
    "entrezgene": 1466404,
    "ensembl": {
        "protein": "YLL066W-B",
        "transcript": "YLL066W-B",
        "gene": "YLL066W-B"
    },
    "type_of_gene": "protein-coding",
    "refseq": {
        "rna": "NM_001184605",
        "protein": "NP_878115",
        "genomic": "NC_001144"
    },
    "taxid": 559292,
    "name": "hypothetical protein",
    "locus_tag": "YLL066W-B",
    "accession": {
        "rna": "NM_001184605",
        "protein": [
            "DAA09259",
            "NP_878115",
            "Q8TGJ7"
        ],
        "genomic": [
            "BK006945",
            "NC_001144"
        ]
    },
    "genomic_pos": {
        "strand": 1,
        "end": 5775,
        "start": 5605,
        "chr": "XII"
    },
    "uniprot": {
        "Swiss-Prot": "Q8TGJ7"
    },
    "SGD": "S000028672",
    "symbol": "YLL066W-B"
}

"""
import logging
from datetime import datetime

from ProteinBoxBot_Core import PBB_login, PBB_Core
from tqdm import tqdm

import ChromosomeBot
from HelperBot import strain_info, make_reference, setup_logging, log
from local import WDUSER, WDPASS

ENTREZ_PROP = "P351"

__metadata__ = {'bot_name': 'YeastBot',
                'run_name': 'gene',
                'run_id': None,
                'domain': 'gene',
                'log_name': 'YeastBot_gene'}

def wd_item_construction(gene_record, strain_info, chrom_wdid, retrieved, logger, login):
    """
    generate pbb_core item object
    """

    item_name = '{} {}'.format(gene_record['name'], gene_record['locus_tag'])
    item_description = '{} gene found in {}'.format(strain_info['organism_type'], strain_info['organism_name'])

    def gene_item_statements():
        """
        construct list of referenced statements to past to PBB_Core Item engine
        :return:
        """
        # creates reference object for WD gene item claim

        ncbi_gene_reference = make_reference('ncbi_gene', 'ncbi_gene', str(gene_record['entrezgene']), retrieved)
        ensembl_gene_reference = make_reference('ensembl', 'ensemble_gene', gene_record['ensembl']['gene'], retrieved)

        chrom_genomeid = strain_info['chrom_genomeid_map'][gene_record['genomic_pos']['chr']]
        rs_chrom = PBB_Core.WDString(value=chrom_genomeid, prop_nr='P2249', is_qualifier=True)  # Refseq Genome ID

        statements = []
        # found in taxon
        statements.append(PBB_Core.WDItemID(value=strain_info['organism_wdid'], prop_nr='P703',
                                            references=[ensembl_gene_reference]))
        # subclass of gene
        statements.append(PBB_Core.WDItemID(value='Q7187', prop_nr='P279',
                                            references=[ensembl_gene_reference]))

        # strand orientation
        strand_orientation = 'Q22809680' if gene_record['genomic_pos']['strand'] == 1 else 'Q22809711'
        statements.append(PBB_Core.WDItemID(value=strand_orientation, prop_nr='P2548',
                                            references=[ensembl_gene_reference]))

        # entrez gene id
        statements.append(PBB_Core.WDString(value=str(gene_record['entrezgene']), prop_nr='P351',
                                            references=[ncbi_gene_reference]))

        # NCBI Locus tag
        statements.append(PBB_Core.WDString(value=gene_record['locus_tag'], prop_nr='P2393',
                                            references=[ncbi_gene_reference]))
        # ensembl gene id
        statements.append(PBB_Core.WDString(value=gene_record['ensembl']['gene'], prop_nr='P594',
                                            references=[ensembl_gene_reference]))
        # genomic start and end
        statements.append(PBB_Core.WDString(value=str(int(gene_record['genomic_pos']['start'])), prop_nr='P644',
                                            references=[ensembl_gene_reference], qualifiers=[rs_chrom]))
        statements.append(PBB_Core.WDString(value=str(int(gene_record['genomic_pos']['end'])), prop_nr='P645',
                                            references=[ensembl_gene_reference], qualifiers=[rs_chrom]))

        # chromosome
        statements.append(PBB_Core.WDItemID(chrom_wdid[gene_record['genomic_pos']['chr']], 'P1057',
                                            references=[ensembl_gene_reference]))
        return statements

    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=gene_item_statements(),
                                         append_value=['P279'],
                                         fast_run=True,
                                         fast_run_base_filter={'P351': '', 'P703': strain_info['organism_wdid']})
    # pprint.pprint(wd_item_gene.get_wd_json_representation())
    wd_item_gene.set_label(item_name)
    wd_item_gene.set_description(item_description, lang='en')
    wd_item_gene.set_aliases([gene_record['symbol'], gene_record['locus_tag']])

    try_write(wd_item_gene, gene_record['_id'], logger, login)


def try_write(wd_item, record_id, logger, login):
    if wd_item.require_write:
        if wd_item.create_new_item:
            msg = "CREATE"
        else:
            msg = "UPDATE"
    else:
        msg = "SKIP"

    try:
        wd_item.write(login=login)
        log(logger, logging.INFO, record_id, msg, wd_item.wd_item_id, ENTREZ_PROP)
    except Exception as e:
        print(e)
        log(logger, logging.ERROR, record_id, str(e), wd_item.wd_item_id, ENTREZ_PROP)


def run(login, gene_records, retrieved, chrom_wdid, logger):

    for n, record in tqdm(enumerate(gene_records), desc=strain_info['organism_name'], total=gene_records.count()):
        if 'genomic_pos' not in record:
            # see: http://mygene.info/v3/gene/855814
            log(logger, logging.ERROR, record['_id'], "no_position", '', ENTREZ_PROP)
            continue
        if isinstance(record['genomic_pos'], list):
            # see: http://mygene.info/v3/gene/853483
            log(logger, logging.ERROR, record['_id'], "multiple_positions", '', ENTREZ_PROP)
            continue
        wd_item_construction(record, strain_info, chrom_wdid, retrieved, logger, login)
    gene_records.close()


def main(log_dir="./logs", run_id=None):
    import biothings
    import config
    from biothings.utils.mongo import get_src_db, get_src_dump

    biothings.config_for_app(config)
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    __metadata__['run_id'] = run_id
    logger = setup_logging(log_dir=log_dir, metadata=__metadata__)

    collection = get_src_db().yeast
    src_dump = get_src_dump()
    src_doc = src_dump.find_one({'_id': 'mygene'})
    retrieved = src_doc["release"]
    records = collection.find({'type_of_gene': 'protein-coding'}, no_cursor_timeout=True)

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)
    chrom_wdid = ChromosomeBot.main(login=login, log_dir=log_dir, run_id=run_id)

    run(login, records, retrieved, chrom_wdid, logger)


if __name__ == "__main__":
    main()
