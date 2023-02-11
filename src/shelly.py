import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from config import ShellyConfig


class Shelly:
    def __init__(self, config: ShellyConfig, debug: bool = False) -> None:

        self.name = config.name
        self.type = config.type
        self.ip = config.ip
        self.port = config.port
        self.user = config.user
        self.passwd = config.passwd
        self.timeout = 2
        self.debug = debug
        self.logger = logging.getLogger(self.name)
        self.request: Optional[requests.request] = None
        self.influx_data: Optional[list] = None

        if self.debug:
            self.logger.setLevel("DEBUG")

    def _get_measures_from_json(self, measures: Dict[str, Any], json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reformat the nested JSON response from a Shelly into a flat dictionary.

        Parameters
        ----------
        measures : Dict[str, Any]
            Dictionary with further measures or empty.
        json : Dict[str, Any]
            The JSON response from the Shelly.

        Returns
        -------
        Dict[str, Any]
            Updated measures dictionary.
        """

        for key, value in json.items():
            if isinstance(value, list):
                for idx, listitem in enumerate(value):
                    for listkey, listvalue in listitem.items():
                        measures[key + f"{idx}_" + listkey] = listvalue
            else:
                if isinstance(value, dict):
                    for dictkey, dictvalue in value.items():
                        measures[key + "_" + dictkey] = dictvalue
                else:
                    measures[key] = value
        return measures

    def query(self) -> None:
        """
        Connect to the Shelly and read data from it.
        """

        request_time = datetime.utcnow()
        try:
            request = requests.get(
                f"http://{self.ip}/status",
                verify=False,
                auth=(self.user, self.passwd),
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            self.logger.info(f"Request to Shelly {self.name} timed out.")
        else:
            measures = {}
            measures["request_status_code"] = request.status_code
            measures["request_reason"] = request.reason
            measures["request_elapsed"] = request.elapsed.total_seconds()
            if request.status_code == 200:
                json = request.json()
                if "unixtime" in json.keys():  # Shelly 3PM
                    time = datetime.utcfromtimestamp(json["unixtime"])
                elif "meters0_timestamp" in json.keys():  # Shelly Plug S
                    time = datetime.utcfromtimestamp(json["meters0_timestamp"])
                else:
                    time = request_time
                measures = self._get_measures_from_json(measures, json)
            else:
                time = request_time

            request.close()

            self.influx_data = [
                {
                    "measurement": self.name,
                    "time": time,
                    "fields": measures,
                }
            ]
