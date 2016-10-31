"""
Modified from Tim's MicrobeBotGenes
https://bitbucket.org/sulab/wikidatabots/raw/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotGenes.py

s288c chromosomes:
https://www.ncbi.nlm.nih.gov/genome/?term=txid559292[Organism:noexp]

example microbial gene:
https://www.wikidata.org/wiki/Q23162696




"""
import json
from datetime import datetime

from ProteinBoxBot_Core import PBB_login, PBB_Core
from tqdm import tqdm

import ChromosomeBot
from HelperBot import strain_info, make_reference, format_msg, make_ref_source, try_write
from SourceBot import get_source_version, get_data_from_mygene
from local import WDUSER, WDPASS

ENTREZ_PROP = "P351"

__metadata__ = {'name': 'YeastBot_Gene',
                'maintainer': 'GSS',
                'tags': ['yeast', 'gene'],
                'properties': ['P703', 'P279', 'P2548', 'P351', 'P2393', 'P594', 'P644', 'P645', 'P1057']
                }

PROPS = {''}

def wd_item_construction(record, strain_info, chrom_wdid, login):
    """
    generate pbb_core item object
    """

    # If the source is "entrez", the reference identifier to be used is "entrez_gene"
    # These are defined in HelperBot
    source_ref_id = {'ensembl': 'ensembl_gene',
                     'entrez': 'entrez_gene',
                     'uniprot': 'uniprot'}

    def gene_item_statements():
        """
        construct list of referenced statements to past to PBB_Core Item engine
        """
        s = []

        ############
        # external IDs
        ############
        # will be used for reference statements
        external_ids = {'entrez_gene': str(record['entrezgene']['@value']),
                        'ensembl_gene': record['ensembl']['@value']['gene']
                        }

        # entrez gene id
        entrez_ref = make_ref_source(record['entrezgene']['@source'], 'entrez_gene', external_ids['entrez_gene'])
        s.append(PBB_Core.WDString(external_ids['entrez_gene'], 'P351', references=[entrez_ref]))

        # ensembl gene id
        ensembl_ref = make_ref_source(record['ensembl']['@source'], 'ensembl_gene', external_ids['ensembl_gene'])
        s.append(PBB_Core.WDString(external_ids['ensembl_gene'], 'P594', references=[ensembl_ref]))

        ############
        # statements with no referencable sources (make by hand, for now...)
        ############
        # subclass of gene
        s.append(PBB_Core.WDItemID('Q7187', 'P279', references=[ensembl_ref]))

        # found in taxon
        s.append(PBB_Core.WDItemID(strain_info['organism_wdid'], 'P703', references=[ensembl_ref]))

        ############
        # genomic position: start, end, strand orientation, chromosome
        ############
        genomic_pos_value = record['genomic_pos']['@value']
        genomic_pos_source = record['genomic_pos']['@source']
        genomic_pos_id_prop = source_ref_id[genomic_pos_source['_id']]
        genomic_pos_ref = make_ref_source(genomic_pos_source, genomic_pos_id_prop, external_ids[genomic_pos_id_prop])

        # create chromosome qualifier
        chrom_genomeid = strain_info['chrom_genomeid_map'][genomic_pos_value['chr']]
        rs_chrom = PBB_Core.WDString(chrom_genomeid, 'P2249', is_qualifier=True)  # Refseq Genome ID

        # strand orientation
        strand_orientation = 'Q22809680' if genomic_pos_value['strand'] == 1 else 'Q22809711'
        s.append(PBB_Core.WDItemID(strand_orientation, 'P2548', references=[genomic_pos_ref]))
        # genomic start and end
        s.append(PBB_Core.WDString(str(int(genomic_pos_value['start'])), 'P644', references=[genomic_pos_ref], qualifiers=[rs_chrom]))
        s.append(PBB_Core.WDString(str(int(genomic_pos_value['end'])), 'P645', references=[genomic_pos_ref], qualifiers=[rs_chrom]))
        # chromosome
        s.append(PBB_Core.WDItemID(chrom_wdid[genomic_pos_value['chr']], 'P1057', references=[genomic_pos_ref]))

        return s

    item_name = '{} {}'.format(record['name']['@value'], record['ensembl']['@value']['gene'])
    item_description = '{} gene found in {}'.format(strain_info['organism_type'], strain_info['organism_name'])

    statements = gene_item_statements()
    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=statements,
                                         append_value=['P279'],
                                         fast_run=False,
                                         fast_run_base_filter={'P351': '', 'P703': strain_info['organism_wdid']})
    wd_item_gene.set_label(item_name)
    wd_item_gene.set_description(item_description, lang='en')
    wd_item_gene.set_aliases([record['symbol']['@value'], record['locus_tag']['@value']])

    try_write(wd_item_gene, record['_id']['@value'], ENTREZ_PROP, login)


def run(login, gene_records, chrom_wdid):
    for n, record in tqdm(enumerate(gene_records), desc=strain_info['organism_name']):
        if 'genomic_pos' not in record:
            # see: http://mygene.info/v3/gene/855814
            PBB_Core.WDItemEngine.log("ERROR", format_msg(record['_id']['@value'], "no_position", '', ENTREZ_PROP))
            continue
        if isinstance(record['genomic_pos']['@value'], list):
            # see: http://mygene.info/v3/gene/853483
            PBB_Core.WDItemEngine.log("ERROR", format_msg(record['_id']['@value'], "multiple_positions", '', ENTREZ_PROP))
            continue
        wd_item_construction(record, strain_info, chrom_wdid, login)
        return


def main(log_dir="./logs", run_id=None):
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    __metadata__['run_id'] = run_id
    log_name = 'YeastBot_gene-{}.log'.format(run_id)
    __metadata__['log_name'] = log_name
    __metadata__['release'] = get_source_version()

    records = get_data_from_mygene()

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)
    chrom_wdid = ChromosomeBot.main(login=login, log_dir=log_dir, run_id=run_id)

    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
    run(login, records, chrom_wdid)


if __name__ == "__main__":
    main()
