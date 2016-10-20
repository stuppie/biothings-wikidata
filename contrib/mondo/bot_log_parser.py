import pandas as pd
from io import StringIO

def parse_info(file_path):
    """
    2016-10-10 16:24:23,060 INFO item_updated IPR026494 Q24785812
    2016-10-10 16:26:55,996 INFO item_updated A0A0E0XWW8 Q24278509
    2016-10-10 16:26:57,587 INFO item_updated A0A0E0XWX1 Q24282146
    """

    df = pd.read_csv(file_path, sep=" ", names=['date','time','level','msg','id','wdid'])
    item_updated = len(df.query("msg == 'item_updated'"))
    item_created = len(df.query("msg == 'item_created'"))
    return item_updated, item_created


def parse_exc(file_path):
    """
    >2016-10-10 16:29:43,213 ERROR wdid_not_found A0A0E0XXX8 Q24277976
    Traceback (most recent call last):
      File "bot.py", line 239, in create_uniprot_relationships
        append_value=["P279", "P527", "P361"])
      File "/home/gstupp/projects/wikidatabots/ProteinBoxBot_Core/PBB_Core.py", line 160, in __init__
        self.init_fastrun()
      File "/home/gstupp/projects/wikidatabots/ProteinBoxBot_Core/PBB_Core.py", line 211, in init_fastrun
        cqid=self.wd_item_id)
      File "/home/gstupp/projects/wikidatabots/ProteinBoxBot_Core/PBB_fastrun.py", line 96, in check_data
        for prop_nr, dt in self.prop_data[qid].items():
    KeyError: 'Q24277976'
    """
    lines = [line[1:] for line in open(file_path).readlines() if line.startswith(">")]
    df = pd.read_csv(StringIO("\n".join(lines)), sep=" ", names=['date','time','level','msg','id','wdid'])
    return df