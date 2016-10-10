# LOGGING #
import logging
LOGGER_NAME = "mygene.hub"
# this will affect any logging calls
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)
# log to console by default
logger.addHandler(logging.StreamHandler())


ALLOWED_OPTIONS = ['_source', 'start', 'from_', 'size', 'sort', 'explain',
                   'version', 'aggs', 'fetch_all', 'species', 'fields',
                   'userfilter', 'exists', 'missing', 'include_tax_tree',
                   'species_facet_filter']

ES_DOC_TYPE = 'gene'

STATUS_CHECK_ID = '1017'

FIELD_NOTES_PATH = ''
JSONLD_CONTEXT_PATH = ''

GENOME_ASSEMBLY = {
    "human": "hg38",
    "mouse": "mm10",
    "rat": "rn4",
    "fruitfly": "dm3",
    "nematode": "ce10",
    "zebrafish": "zv9",
    "frog": "xenTro3",
    "pig": "susScr2"
}

TAXONOMY = {
    "human": 9606,
    "mouse": 10090,
    "rat": 10116,
    "fruitfly": 7227,
    "nematode": 6239,
    "zebrafish": 7955,
    "thale-cress": 3702,
    "frog": 8364,
    "pig": 9823
}

SPECIES_LI = ['human', 'mouse', 'rat', 'fruitfly', 'nematode', 'zebrafish',
              'thale-cress', 'frog', 'pig']


# 'category' in google analytics event object
GA_EVENT_CATEGORY = 'v3_api'
# url for google analytics tracker
GA_TRACKER_URL = 'mygene.info'

# *****************************************************************************
# URL settings
# *****************************************************************************
# For URL stuff
ANNOTATION_ENDPOINT = 'gene'
QUERY_ENDPOINT = 'query'
API_VERSION = 'v3'

# *****************************************************************************
# Tests
# *****************************************************************************
# use this file as nosetest config file
NOSETEST_SETTINGS = "config"
# Env. var containing root URL to services
HOST_ENVAR_NAME = "MG_HOST"

# translate data source
# (keys will be used as regex pattern, case-ignored)
# /!\ values can be evaled as regex by ES
# so special chars may need escape.
# Ex: "refseq.\*" should be escaped 2 times,
# one for ES, one for python ES client
# Also, make sure using raw python string so there's no
# need to actually escape here again...
SOURCE_TRANSLATORS = {
    "refseq:":  r"refseq.\\\*:",
    "accession:":   r"accession.\\\*:",
    "reporter:":    r"reporter.\\\*:",
    "interpro:":    r"interpro.\\\*:",
    # GO:xxxxx looks like a ES raw query, so just look for 
    # the term as a string in GO's ID (note: searching every keys
    # will raise an error because pubmed key is a int and we're 
    # searching with a string term.
    "GO:":          r"go.\\\*.id:go\\\:",
    #"GO:":          r"go.\\\*:go.",
    "homologene:":  r"homologene.\\\*:",
    "reagent:":     r"reagent.\\\*:",
    "uniprot:":     r"uniprot.\\\*:",

    "ensemblgene:":         "ensembl.gene:",
    "ensembltranscript:":   "ensembl.transcript:",
    "ensemblprotein:":      "ensembl.protein:",

    # some specific datasources needs to be case-insentive
    "hgnc:":        r"HGNC:",
    "hprd:":        r"HPRD:",
    "mim:":        r"MIM:",
    "mgi:":        r"MGI:",
    "ratmap:":      r"RATMAP:",
    "rgd:":      r"RGD:",
    "flybase:":      r"FLYBASE:",
    "wormbase:":    r"WormBase:",
    "tair:":      r"TAIR:",
    "zfin:":      r"ZFIN:",
    "xenbase:":      r"Xenbase:",
    "mirbase:":     r"miRBase:",

}


# ################ #
# MYGENE HUB VARS  #
# ################ #

DATA_SRC_MASTER_COLLECTION = 'src_master'   # for metadata of each src collections
DATA_SRC_DUMP_COLLECTION = 'src_dump'       # for src data download information
DATA_SRC_BUILD_COLLECTION = 'src_build'     # for src data build information

DATA_TARGET_MASTER_COLLECTION = 'db_master'

# time in seconds for dispatcher to check new jobs
DISPATCHER_SLEEP_TIME = 1
# Use default storage
SOURCE_STORAGE_CLASS = None # use default one
