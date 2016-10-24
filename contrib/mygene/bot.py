"""

- Check if the organism is in wikidata
    if not, create strain item. link strain item to parent

- Add or update all gene items

- Add or update all protein items

- Create encodes/encoded by links


"""

# https://bitbucket.org/sulab/wikidatabots/src/c448a375f97daf279bec71fd800d551dedecd9af/automated_bots/genes/bacteria/MicrobeBotController.py?at=jenkins-automation&fileviewer=file-view-default
# https://bitbucket.org/sulab/wikidatabots/src/c448a375f97daf279bec71fd800d551dedecd9af/genes/microbes/MicrobeBotGenes.py?at=jenkins-automation&fileviewer=file-view-default
import argparse
import os

import GeneBot
import ProteinBot

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run mygene wikidata import bot')
    parser.add_argument('--log_dir', help='directory to store logs', type=str)
    args = parser.parse_args()
    log_dir = args.log_dir if args.log_dir else os.getcwd()
    GeneBot.main(log_dir=log_dir)
    ProteinBot.main(log_dir=log_dir)