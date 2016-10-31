import xml.etree.ElementTree as ET
from time import gmtime, strftime

import requests
from ProteinBoxBot_Core import PBB_Core
from ProteinBoxBot_Core import PBB_login

from HelperBot import try_write
from local import WDUSER, WDPASS


class Pubmed():

    login = PBB_login.WDLogin(user=WDUSER, pwd=WDPASS)

    def __init__(self, pmid):
        self.pmid = str(pmid)
        self.title = None
        self.dois = None
        self.reference = None
        self.statements = None

    def get_if_exists(self):
        url = "http://wdq.wmflabs.org/api?q=string[698:{}]"
        result = requests.get(url.format(self.pmid)).json()["items"]
        if len(result) > 1:
            print("warning, multiple items found for pmid {}".format(self.pmid))
        return result[0] if result else None

    def get_pubmed(self):
        pubmedUrl = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=Pubmed&Retmode=xml&id='
        r = requests.get(pubmedUrl+ self.pmid)
        root = ET.fromstring(r.text)
        self.title = root.findall(".//MedlineCitation/Article/ArticleTitle")[0].text
        doiset = root.findall(".//ArticleIdList/ArticleId[@IdType='doi']")
        self.dois = [x.text for x in doiset]

    def make_reference(self):
        refStatedIn = PBB_Core.WDItemID(value='Q180686', prop_nr='P248', is_reference=True)
        refPubmedId = PBB_Core.WDString(value=self.pmid, prop_nr='P698', is_reference=True)
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        self.reference = [refStatedIn, refPubmedId, refRetrieved]

    def make_statements(self):
        s = []
        # instance of scientific article
        s.append(PBB_Core.WDItemID('Q13442814', 'P31', references=[self.reference]))
        # pmid
        s.append(PBB_Core.WDExternalID(self.pmid, 'P698', references=[self.reference]))
        # title
        s.append(PBB_Core.WDMonolingualText(self.title, 'P1476', references=[self.reference]))
        for doi in self.dois:
            s.append(PBB_Core.WDExternalID(doi, 'P356', references=[self.reference]))
        self.statements = s

    def create(self):
        pmid_wdid = self.get_if_exists()
        if pmid_wdid:
            return pmid_wdid
        self.get_pubmed()
        self.make_reference()
        self.make_statements()
        item = PBB_Core.WDItemEngine(item_name=self.title, data=self.statements, domain="scientific_article")
        item.set_label(self.title)
        item.set_description(description='scientific article', lang='en')
        try_write(item, self.pmid, 'P698', self.login)
        return item.wd_item_id