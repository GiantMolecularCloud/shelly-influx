# Shelly to Influx

An application to periodically read statistics from Shelly devices and pipe them to InfluxDB.
All statistics available through the `/status` endpoint are forwarded to Influxdb.

Supported (tested) Shelly devices:

-   Shelly 3EM
-   Shelly 1PM
-   Shelly Plug S
    Other devices should work as well because this script just takes all available data and reformats them in a way that InfluxDB accepts.

Built docker images are available on [Docker Hub](https://hub.docker.com/r/giantmolecularcloud/shelly-influx).

## Local execution

-   Install requirements: `pip install -r docker/requirements.txt`
-   Customize the config file `config/example_config.py`
-   And run: `python src/run.py config/customized_config.py`

## docker

-   Build the image: `docker build -t shelly-influx:latest -f docker/Dockerfile .`
-   Customize the config file in `config/example_config.py` and save it as `config.yaml`.
-   Run the container: ` docker run -v /path/to/your/config/directory:/config shelly-influx:latest shelly-influx`

## Options

Options for the application itself, the InfluxDB connection and all connected devices are configured using a config file.
The docker image assumes that this file is called `config.yaml` but for local execution the name can be whatever.

Most config options can be omitted because they have default values defined.

Saving credentials of any sort in a plain text file is obviously a bad idea, however, I meant to run this application on an isolated device with very little attack surface. Think about your specific thread model before blindly running this. Or better: fix it and issue a pull request.

### General options

| config     | default | explanation                                                    |
| ---------- | ------- | -------------------------------------------------------------- |
| sampletime | 30      | Time intervall in seconds to query connected devices for data. |
| debug      | false   | Log debug messages.                                            |

### InfluxDB settings

Options of the section `influx`.

| config | default  | explanation                                       |
| ------ | -------- | ------------------------------------------------- |
| ip     | 127.0.01 | IP address of the machine InfluxDB is running on. |
| port   | 8086     | Port to connect to InfluxDB.                      |
| user   | root     | User to access the InfluxDB database.             |
| passwd | root     | Password to access the InfluxDB database.         |
| dbname | shelly   | Database to write the measurements to.            |

### Shelly devices

This must be list of devices. If you only configure a single device, it is just a list with a single entry.

| config | default    | explanation                                                                       |
| ------ | ---------- | --------------------------------------------------------------------------------- |
| name   | no default | Identifier for the Shelly. This will be the name of the measurement in InfluxDB.  |
| type   | no default | Type of Shelly. Meant to correctly treat different models but not used currently. |
| ip     | no default | IP address of the Shelly device.                                                  |
| port   | 80         | Port of the Shelly device.                                                        |
| user   | shelly     | User to access the Shelly's web interface.                                        |
| passwd | no default | Password to access the Shelly's web interface.                                    |
