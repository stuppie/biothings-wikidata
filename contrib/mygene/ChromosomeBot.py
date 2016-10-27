"""
Example mouse chromosome 5
https://www.wikidata.org/wiki/Q15304656
"""
import json
from datetime import datetime
import logging

from ProteinBoxBot_Core import PBB_Core, PBB_login

from HelperBot import strain_info, format_msg
from local import WDUSER, WDPASS

__metadata__ = {'bot_name': 'YeastBot',
                'run_name': 'chromosome',
                'run_id': None,
                'domain': 'chromosome',
                'log_name': None}


def make_ref(retrieved, genome_id):
    refs = [
        PBB_Core.WDItemID(value='Q20641742', prop_nr='P248', is_reference=True),  # stated in ncbi gene
        PBB_Core.WDString(value=genome_id, prop_nr='P2249', is_reference=True),  # Link to Refseq Genome ID
        PBB_Core.WDTime(retrieved.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)
    ]
    return refs


def make_chroms(strain_info, retrieved, login):
    chrom_wdid = {}
    for chrom_num, genome_id in strain_info['chrom_genomeid_map'].items():

        item_name = '{} chromosome {}'.format(strain_info['organism_name'], chrom_num)
        item_description = '{} chromosome'.format(strain_info['organism_type'])
        print(item_name)
        print(genome_id)

        reference = make_ref(retrieved, genome_id)
        statements = []
        statements.append(
            PBB_Core.WDItemID(value='Q37748', prop_nr='P279', references=[reference]))  # subclass of chromosome
        statements.append(PBB_Core.WDItemID(value=strain_info['organism_wdid'], prop_nr='P703',
                                            references=[reference]))  # found in taxon
        statements.append(PBB_Core.WDString(value=genome_id, prop_nr='P2249', references=[reference]))  # genome id

        wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='chromosome', data=statements,
                                        append_value=['P279'], fast_run=True,
                                        fast_run_base_filter={'P703': strain_info['organism_wdid'], 'P2249': ''})

        if wd_item.require_write:
            print("require write")
            wd_item.set_label(item_name)
            wd_item.set_description(item_description, lang='en')
            try:
                msg = "CREATE" if wd_item.create_new_item else "UPDATE"
                wd_item.write(login=login)
                PBB_Core.WDItemEngine.log("INFO", format_msg(genome_id, msg, wd_item.wd_item_id, external_id_prop='P2249'))
            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log("ERROR", format_msg(genome_id, str(e), wd_item.wd_item_id, external_id_prop='P2249'))
        else:
            chrom_wdid[chrom_num] = wd_item.wd_item_id
            PBB_Core.WDItemEngine.log("INFO", format_msg(genome_id, "SKIP", wd_item.wd_item_id, external_id_prop='P2249'))

    return chrom_wdid


def main(login=None, log_dir="./logs", run_id=None):
    if not login:
        login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)
    retrieved = datetime.now()
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H:%M')
    __metadata__['run_id'] = run_id
    log_name = 'YeastBot_chromosome-{}.log'.format(run_id)
    __metadata__['log_name'] = log_name

    PBB_Core.WDItemEngine.setup_logging(log_dir=log_dir, log_name=log_name, header=json.dumps(__metadata__))
    chrom_wdid = make_chroms(strain_info, retrieved, login)
    return chrom_wdid


if __name__ == "__main__":
    print(main())
