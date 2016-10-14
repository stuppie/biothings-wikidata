from config_common import *
APP_PATH="/home/gstupp/projects/biothings/wikidata"
ES_HOST = 'localhost:9200'

ES_INDEX_NAME = "interpro"
ES_INDEX_NAME_TIER1 = "interpro"
ES_INDEX_TYPE = "interpro"


ES_SCROLL_TIME = '1m'
ES_SCROLL_SIZE = 10


# relevant for running in prod
INCLUDE_DOCS = False  # if True, include the links to mygene.info docs

# *****************************************************************************
# Google Analytics Settings
# *****************************************************************************
# Google Analytics Account ID
GA_ACCOUNT = 'UA-xxxxxxxx-x'
# Turn this to True to start google analytics tracking
GA_RUN_IN_PROD = False


# ################ #
# MYGENE HUB VARS  #
# ################ #

# webserver to show hub status
DATA_WWW_ROOT_URL = "http://localhost:8000"

DATA_SRC_SERVER = 'localhost'
DATA_SRC_PORT = 27017
DATA_SRC_DATABASE = 'wikidata_src'

DATA_TARGET_SERVER = 'localhost'
DATA_TARGET_PORT = 27017
DATA_TARGET_DATABASE = 'wikidata'

DATA_SERVER_USERNAME = ''
DATA_SERVER_PASSWORD = ''

LOG_FOLDER = 'logs'

# Absolute path !
DATA_ARCHIVE_ROOT = '/home/gstupp/projects/biothings/wikidata/data'
# if True then all data directory will be kept
# otherwise only latest will be kept (while downloading, previous
# version will be removed)
ARCHIVE_DATA = True

# Path to ASCP install directory
# (see "bin" and "etc" are). See http://asperasoft.com
# http://download.asperasoft.com/download/sw/connect/3.6.2/aspera-connect-3.6.2.117442-linux-64.tar.gz
ASCP_ROOT = '~/opt/aspera_connect'

# fill with "host", "username" and "key" keys
# to create a SSH tunnel to feed ES
ES_HOST_TUNNEL_CFG = {}

TARGET_ES_INDEX_SUFFIX = '_current'

# fill with "token", "roomid" and "from" keys
# to broadcast message to a Hipchat room
HIPCHAT_CONFIG = { "token" : "", "roomid" : "", "from" : "" }

# path to ipcluster json config file (if any)
CLUSTER_CLIENT_JSON = None
