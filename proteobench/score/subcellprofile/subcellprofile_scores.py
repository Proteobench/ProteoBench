import json
from io import StringIO

import domaps


def json_download(sd: domaps.SpatialDataset) -> StringIO:
    sio = StringIO()
    json.dump(sd.analysed_datasets_dict, sio, indent=4, sort_keys=True)
    sio.seek(0)
    return sio

class Subcellprofile_Scores:

    def __init__(self):
        self.sd: domaps.SpatialDataset = None

    def generate_SpatialDataset(
        self,
        content: StringIO,
        settings: dict,
    ):
        """
        Generate a SpatialDataset object from the content and settings.
        """
        sd = domaps.SpatialDataset.from_settings(settings)
        sd.run_pipeline(content=content)
        self.sd = sd