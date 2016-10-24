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

def make_reference(source, id_prop, identifier, retrieved):
    source_items = {'uniprot': 'Q905695',
                    'ncbi_gene': 'Q20641742',
                    'ncbi_taxonomy': 'Q13711410',
                    'swiss_prot': 'Q2629752',
                    'trembl': 'Q22935315',
                    'ensembl': 'Q1344256'}

    prop_ids = {'uniprot': 'P352',
                'ncbi_gene': 'P351',
                'ncbi_taxonomy': 'P685',
                'ncbi_locus_tag': 'P2393',
                'ensemble_gene': 'P594',
                'ensemble_protein': 'P705'
                }

    reference = [
        PBB_Core.WDItemID(value=source_items[source], prop_nr='P248', is_reference=True),  # stated in
        PBB_Core.WDString(value=str(identifier), prop_nr=prop_ids[id_prop], is_reference=True),  # Link to ID
        PBB_Core.WDTime(retrieved.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)]
    return reference