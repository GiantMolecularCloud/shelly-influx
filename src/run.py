"""
Shelly to InfluxDB
An application to periodically read statistics from Shelly devices and pipe them to InfluxDB.
"""

import argparse
import logging
from pathlib import Path
from time import sleep

from .config import get_config
from .influx import Influx
from .shelly import Shelly
from .timer import RepeatedTimer
from .version import __author__, __version__

logging.basicConfig(level=logging.INFO, format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main")

parser = argparse.ArgumentParser(
    description=f"""
An application to periodically read statistics from Shelly devices and pipe them to InfluxDB.
Version: {__version__}
Author: {__author__}
Link: https://github.com/GiantMolecularCloud/shelly-influx
"""
)
parser.add_argument("configfile", metavar="config", type=Path, nargs="?", help="The configuration file to load.")
parser.add_argument("--version", action="version", version=f"ShellyInflux {__version__}")


def query_and_push(shelly: Shelly, influx: Influx) -> None:
    """
    Query a Shelly and write the results to Influx.

    Parameters
    ----------
    shelly : Shelly
        The Shelly instance to query data from.
    influx : Influx
        The influx instance to write data to.
    """

    try:
        shelly.query()
        if shelly.influx_data is None:
            logger.warning(f"No data received from {shelly.name}.")
        else:
            influx.write(shelly.influx_data)
    except Exception as e:
        logger.error(e)


def main(argv: list[str] | None = None) -> None:

    args = parser.parse_args(argv)
    config = get_config(args.configfile)

    logger.info("Loaded configuration:")
    logger.info(config.model_dump_json(indent=4))

    if config.debug:
        logger.setLevel("DEBUG")

    influx = Influx(config.influx, config.debug)
    shellies = [Shelly(device_config, config.debug) for device_config in config.devices]

    timers = []
    for shelly in shellies:
        timers.append(RepeatedTimer(config.sampletime, query_and_push, shelly, influx))

    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        logger.warning("Program stopped by keyboard interrupt [CTRL_C] by user.")
    finally:
        for timer in timers:
            timer.stop()


if __name__ == "__main__":
    main()
