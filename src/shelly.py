import logging
from datetime import datetime, timezone
from typing import Any

import requests
from requests.auth import HTTPDigestAuth

from .config import ShellyConfig


class Shelly:
    def __init__(self, config: ShellyConfig, debug: bool = False) -> None:

        self.name = config.name
        self.type = config.type
        self.timeout = 2
        self.debug = debug
        self.logger = logging.getLogger(self.name)
        self.request: requests.request | None = None
        self.influx_data: list[dict] | None = None

        # For Shelly Plus devices, use the PLUGS_UI
        if "Plus" in self.type:
            self.uri = f"http://{config.ip}/rpc/Switch.GetStatus?id=0"
            self.auth = HTTPDigestAuth(config.user, config.passwd)
        else:
            self.uri = f"http://{config.ip}/status"
            self.auth = (config.user, config.passwd)

        if self.debug:
            self.logger.setLevel("DEBUG")

    def _get_measures_from_json(self, measures: dict[str, Any], json: dict[str, Any]) -> dict[str, Any]:  # noqa:CCR001
        """
        Reformat the nested JSON response from a Shelly into a flat dictionary.

        Parameters
        ----------
        measures : dict[str, Any]
            Dictionary with further measures or empty.
        json : dict[str, Any]
            The JSON response from the Shelly.

        Returns
        -------
        dict[str, Any]
            Updated measures dictionary.
        """

        # explode list and dictionaries
        for key, value in json.items():
            if isinstance(value, list):
                for idx, listitem in enumerate(value):
                    for listkey, listvalue in listitem.items():
                        if isinstance(listvalue, list):
                            for idx2, listitem2 in enumerate(listvalue):
                                measures[f"{key}{idx}_{listkey}{idx2}"] = listitem2
                        else:
                            measures[f"{key}{idx}_{listkey}"] = listvalue
            else:
                if isinstance(value, dict):
                    for dictkey, dictvalue in value.items():
                        measures[f"{key}_{dictkey}"] = dictvalue
                else:
                    measures[key] = value

        # explode remaining lists
        for key in list(measures.keys()):
            value = measures[key]
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    measures[f"{key}_{idx}"] = item
                del measures[key]

        return measures

    def query(self) -> None:
        """
        Connect to the Shelly and read data from it.
        """

        request_time = datetime.now(timezone.utc)
        try:
            request = requests.get(
                self.uri,
                verify=False,
                auth=self.auth,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            self.logger.info(f"Request to Shelly {self.name} timed out.")
        else:
            measures = {
                "request_status_code": request.status_code,
                "request_reason": request.reason,
                "request_elapsed": request.elapsed.total_seconds(),
            }
            if request.status_code == 200:
                json = request.json()
                if "unixtime" in json:  # Shelly 3PM
                    time = datetime.fromtimestamp(json["unixtime"], timezone.utc)
                elif "meters0_timestamp" in json:  # Shelly Plug S
                    time = datetime.fromtimestamp(json["meters0_timestamp"], timezone.utc)
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
