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

from ProteinBoxBot_Core import PBB_login, PBB_Core, PBB_Helpers
from tqdm import tqdm

import ChromosomeBot
from HelperBot import strain_info, format_msg, make_ref_source
from SourceBot import get_source_versions, get_data_from_mygene
from local import WDUSER, WDPASS

ENTREZ_PROP = "P351"

PROPS = {'found in taxon': 'P703',
         'subclass of': 'P279',
         'strand orientation': 'P2548',
         'Entrez Gene ID': 'P351',
         'NCBI Locus tag': 'P2393',
         'Ensembl Gene ID': 'P594',
         'genomic start': 'P644',
         'genomic end': 'P645',
         'chromosome': 'P1057'}

__metadata__ = {'name': 'YeastBot_Gene',
                'maintainer': 'GSS',
                'tags': ['yeast', 'gene'],
                'properties': list(PROPS.values())
                }

def wd_item_construction(record, strain_info, chrom_wdid, login):
    """
    generate pbb_core item object
    """

    # If the source is "entrez", the reference identifier to be used is "entrez_gene"
    # These are defined in HelperBot
    source_ref_id = {'Ensembl': 'ensembl_gene',
                     'Entrez': 'entrez_gene',
                     'Uniprot': 'uniprot'}

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
                        'ensembl_gene': record['ensembl']['@value']['gene'],
                        'locus_tag': record['locus_tag']['@value']
                        }

        # entrez gene id
        entrez_ref = make_ref_source(record['entrezgene']['@source'], 'entrez_gene', external_ids['entrez_gene'])
        s.append(PBB_Core.WDString(external_ids['entrez_gene'], PROPS['Entrez Gene ID'], references=[entrez_ref]))

        # ensembl gene id
        ensembl_ref = make_ref_source(record['ensembl']['@source'], 'ensembl_gene', external_ids['ensembl_gene'])
        s.append(PBB_Core.WDString(external_ids['ensembl_gene'], PROPS['Ensembl Gene ID'], references=[ensembl_ref]))

        # ncbi locus tag
        s.append(PBB_Core.WDString(external_ids['locus_tag'], PROPS['NCBI Locus tag'], references=[entrez_ref]))

        ############
        # statements with no referencable sources (make by hand, for now...)
        ############
        # subclass of gene
        s.append(PBB_Core.WDItemID('Q7187', PROPS['subclass of'], references=[ensembl_ref]))

        # found in taxon
        s.append(PBB_Core.WDItemID(strain_info['organism_wdid'], PROPS['found in taxon'], references=[ensembl_ref]))

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
        s.append(PBB_Core.WDItemID(strand_orientation, PROPS['strand orientation'], references=[genomic_pos_ref]))
        # genomic start and end
        s.append(PBB_Core.WDString(str(int(genomic_pos_value['start'])), PROPS['genomic start'], references=[genomic_pos_ref], qualifiers=[rs_chrom]))
        s.append(PBB_Core.WDString(str(int(genomic_pos_value['end'])), PROPS['genomic end'], references=[genomic_pos_ref], qualifiers=[rs_chrom]))
        # chromosome
        chr_genomic_id = strain_info['chrom_genomeid_map'][genomic_pos_value['chr']]
        s.append(PBB_Core.WDItemID(chrom_wdid[chr_genomic_id], PROPS['chromosome'], references=[genomic_pos_ref]))

        return s

    item_name = '{} {}'.format(record['name']['@value'], record['ensembl']['@value']['gene'])
    item_description = '{} gene found in {}'.format(strain_info['organism_type'], strain_info['organism_name'])

    statements = gene_item_statements()
    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=statements,
                                         append_value=[PROPS['subclass of']],
                                         fast_run=True,
                                         fast_run_base_filter={PROPS['Entrez Gene ID']: '', PROPS['found in taxon']: strain_info['organism_wdid']})
    wd_item_gene.set_label(item_name)
    wd_item_gene.set_description(item_description, lang='en')
    wd_item_gene.set_aliases([record['symbol']['@value'], record['locus_tag']['@value']])

    PBB_Helpers.try_write(wd_item_gene, record['_id']['@value'], ENTREZ_PROP, login)


def run(login, gene_records, chrom_wdid):
    for record in tqdm(gene_records):
        if 'genomic_pos' not in record:
            # see: http://mygene.info/v3/gene/855814
            PBB_Core.WDItemEngine.log("WARNING", format_msg(record['_id']['@value'], "no_position", '', ENTREZ_PROP))
            continue
        if isinstance(record['genomic_pos']['@value'], list):
            # see: http://mygene.info/v3/gene/853483
            PBB_Core.WDItemEngine.log("WARNING", format_msg(record['_id']['@value'], "multiple_positions", '', ENTREZ_PROP))
            continue
        wd_item_construction(record, strain_info, chrom_wdid, login)


def main(log_dir="./logs", run_id=None):
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    __metadata__['run_id'] = run_id
    __metadata__['timestamp'] = str(datetime.now())

    log_name = 'YeastBot_gene-{}.log'.format(run_id)
    __metadata__['log_name'] = log_name
    __metadata__['sources'] = get_source_versions()

    records = get_data_from_mygene()

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

    chrom_wdid = PBB_Helpers.id_mapper("P2249", (("P703", "Q27510868"),))

    if PBB_Core.WDItemEngine.logger is not None:
        PBB_Core.WDItemEngine.logger.handles = []
    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
    run(login, records, chrom_wdid)


if __name__ == "__main__":
    main()
