from datetime import datetime
from ProteinBoxBot_Core import PBB_Core

strain_info = {
    "organism_type": "fungal",
    "organism_name": "Saccharomyces cerevisiae S288c",
    "organism_wdid": "Q27510868",
    # strain-specific chromosome to Refseq Genome ID mapping
    "chrom_genomeid_map": {
        'I': 'NC_001133.9',
        'II': 'NC_001134.8',
        'III': 'NC_001135.5',
        'IV': 'NC_001136.10',
        'IX': 'NC_001141.2',
        'MT': 'NC_001224.1',
        'Mito': 'NC_001224.1',  # ensembl calls it Mito (from mygene)
        'V': 'NC_001137.3',
        'VI': 'NC_001138.5',
        'VII': 'NC_001139.9',
        'VIII': 'NC_001140.6',
        'X': 'NC_001142.9',
        'XI': 'NC_001143.9',
        'XII': 'NC_001144.5',
        'XIII': 'NC_001145.3',
        'XIV': 'NC_001146.8',
        'XV': 'NC_001147.6',
        'XVI': 'NC_001148.4'
    }
}

go_props = {'MF': 'P680',
            'CC': 'P681',
            'BP': 'P682'
            }
go_evidence_codes = {
    'EXP': 'Q23173789',
    'IDA': 'Q23174122',
    'IPI': 'Q23174389',
    'IMP': 'Q23174671',
    'IGI': 'Q23174952',
    'IEP': 'Q23175251',
    'ISS': 'Q23175558',
    'ISO': 'Q23190637',
    'ISA': 'Q23190738',
    'ISM': 'Q23190825',
    'IGC': 'Q23190826',
    'IBA': 'Q23190827',
    'IBD': 'Q23190833',
    'IKR': 'Q23190842',
    'IRD': 'Q23190850',
    'RCA': 'Q23190852',
    'TAS': 'Q23190853',
    'NAS': 'Q23190854',
    'IC': 'Q23190856',
    'ND': 'Q23190857',
    'IEA': 'Q23190881',
    'IMR': 'Q23190842'
}

source_items = {'uniprot': 'Q905695',
                'ncbi_gene': 'Q20641742', # these two are the same?  --v
                'entrez':    'Q20641742',
                'ncbi_taxonomy': 'Q13711410',
                'swiss_prot': 'Q2629752',
                'trembl': 'Q22935315',
                'ensembl': 'Q1344256',
                'refseq': 'Q7307074'}

prop_ids = {'uniprot': 'P352',
            'ncbi_gene': 'P351',
            'entrez_gene': 'P351',
            'ncbi_taxonomy': 'P685',
            'ncbi_locus_tag': 'P2393',
            'ensembl_gene': 'P594',
            'ensembl_protein': 'P705',
            'refseq_protein': 'P637'
            }


# TODO: Make bot automatically query for these, and create if not exists
release_items = {'ensembl': {"86": "Q27613766",
                             "83": "Q21996330"}}


def try_write(wd_item, record_id, record_prop, login):
    if wd_item.require_write:
        if wd_item.create_new_item:
            msg = "CREATE"
        else:
            msg = "UPDATE"
    else:
        msg = "SKIP"

    try:
        wd_item.write(login=login)
        PBB_Core.WDItemEngine.log("INFO", format_msg(record_id, msg, wd_item.wd_item_id, record_prop))
    except Exception as e:
        print(e)
        PBB_Core.WDItemEngine.log("ERROR", format_msg(record_id, str(e), wd_item.wd_item_id, record_prop))


def make_ref_source(source_doc, id_prop, identifier):
    """
    Reference is made up of:
    stated_in: if the source has a release #:
        release edition
        else, stated in the source
    link to id: link to identifier in source
    retrieved: only if source has no release #

    :param source_doc:
    :param id_prop:
    :param identifier:
    :return:
    """
    # source_doc = {'_id': 'uniprot', 'timestamp': '20161006'}
    # source_doc = {'_id': 'ensembl', 'release': 86, 'timestamp': '20161005'}
    source = source_doc['_id']
    if source not in source_items:
        raise ValueError("Unknown source for reference creation: {}".format(source))
    if id_prop not in prop_ids:
        raise ValueError("Unknown id_prop for reference creation: {}".format(id_prop))

    link_to_id = PBB_Core.WDString(value=str(identifier), prop_nr=prop_ids[id_prop], is_reference=True)

    if "release" in source_doc:
        release = str(source_doc['release'])
        if release not in release_items[source]:
            raise ValueError("Must create release by hand, for now...: {}".format(source_doc))
        stated_in = PBB_Core.WDItemID(value=release_items[source][release], prop_nr='P248', is_reference=True)
        reference = [stated_in, link_to_id]
    else:
        date_string = source_doc['timestamp']
        retrieved = datetime.strptime(date_string,"%Y%m%d")
        stated_in = PBB_Core.WDItemID(value=source_items[source], prop_nr='P248', is_reference=True)
        retrieved = PBB_Core.WDTime(retrieved.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)
        reference = [stated_in, retrieved, link_to_id]
    return reference




def make_reference(source, id_prop, identifier, retrieved):
    reference = [
        PBB_Core.WDItemID(value=source_items[source], prop_nr='P248', is_reference=True),  # stated in
        PBB_Core.WDString(value=str(identifier), prop_nr=prop_ids[id_prop], is_reference=True),  # Link to ID
        PBB_Core.WDTime(retrieved.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)]
    return reference


def format_msg(main_data_id, message, wd_id, external_id_prop=None):
    # escape double quotes and quote string with commas,
    # so it can be read by pd.read_csv(fp, escapechar='\\')
    message = message.replace("\"", "\\\"")
    message = "\"" + message + "\"" if "," in message else message
    message = message.replace(",", "")
    msg = '{main_data_id},{message},{wd_id},{prop}'.format(
        main_data_id=main_data_id, message=message,
        wd_id=wd_id, prop=external_id_prop)
    return msg
