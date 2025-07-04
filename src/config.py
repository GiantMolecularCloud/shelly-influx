import logging
from pathlib import Path
from typing import List, Self

import yaml
from pydantic import BaseModel, StrictInt, StrictStr, field_validator, model_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("config")


class InfluxConfig(BaseModel):
    """
    Pydantic model for the Influx subsection of the config.
    """

    ip: StrictStr = "127.0.0.1"
    port: StrictInt = 8086
    user: StrictStr = "root"
    passwd: StrictStr = "root"
    dbname: StrictStr = "shelly"

    @model_validator(mode="after")
    def check_credentials(self) -> Self:
        if self.user == "root" and self.passwd == "root":
            logger.warning("The default credentials should not be used. Create a dedicated influx user instead.")
        return self


class ShellyConfig(BaseModel):
    name: StrictStr
    type: StrictStr
    ip: StrictStr
    user: StrictStr = "shelly"
    passwd: StrictStr

    @model_validator(mode="after")
    def check_plus_device_user(self) -> Self:
        if "Plus" in self.type and self.user != "admin":
            logger.warning(f'Device "{self.name}" is a Plus device but user is not "admin".')
        return self


class ShellyInfluxConfig(BaseModel):
    """
    Pydantic model for the Shelly - Influx config file.
    """

    influx: InfluxConfig
    sampletime: StrictInt = 30
    debug: bool = False
    devices: List[ShellyConfig]

    @classmethod
    @field_validator("devices")
    def check_configured_devices(cls, value: List) -> List:
        if len(value) == 0:
            raise ValueError("No Shelly devices configured.")
        if len(value) > 10:
            logger.warning("Too many devices may slow the program down. This code does not yet run asynchronously.")
        return value

    @classmethod
    @field_validator("sampletime")
    def warn_short_sampletime(cls, value: int) -> int:
        if value < 5:
            logger.warning(
                "Sample time is short and may not be reachable due to latencies. This code does not yet run asynchronously."
            )
        return value


def get_config(configfile: Path) -> ShellyInfluxConfig:
    """
    Parse the config file into a Pydantic model.

    Parameters
    ----------
    configfile : str
        Path to the config file including file name and extension.

    Returns
    -------
    ShellyInfluxConfig
        Parsed and validated config.
    """

    if configfile.suffix not in [".yaml", ".yml"]:
        raise ValueError("Config file must be YAML with suffix .yaml or .yml")
    with open(configfile) as f:
        config = yaml.safe_load(f)
        return ShellyInfluxConfig(**config)
