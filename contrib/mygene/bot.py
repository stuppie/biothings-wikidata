"""

- Check if the organism is in wikidata
    if not, create strain item. link strain item to parent

- Add or update all gene items

- Add or update all protein items

- Create encodes/encoded by links


# known error
https://en.wikipedia.org/wiki/Gcn2

"""

# https://bitbucket.org/sulab/wikidatabots/src/c448a375f97daf279bec71fd800d551dedecd9af/automated_bots/genes/bacteria/MicrobeBotController.py?at=jenkins-automation&fileviewer=file-view-default
# https://bitbucket.org/sulab/wikidatabots/src/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotGenes.py?at=jenkins-automation&fileviewer=file-view-default
import argparse
import os
from datetime import datetime

import GeneBot
import ProteinBot

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run mygene wikidata import bot')
    parser.add_argument('--log_dir', help='directory to store logs', type=str)
    parser.add_argument('--run_id', help='run id', type=str)
    args = parser.parse_args()
    log_dir = args.log_dir if args.log_dir else "./logs"
    run_id = args.run_id if args.run_id else datetime.now().strftime('%Y%m%d_%H:%M')

    # GeneBot.main(log_dir=log_dir, run_id=run_id)
    ProteinBot.main(log_dir=log_dir, run_id=run_id)