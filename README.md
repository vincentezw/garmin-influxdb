# Python Garmin Connect to InfluxDB

Made possible by [GarminConnect PyPi](https://pypi.org/project/garminconnect/) and [InfluxDB PyPi](https://influxdb-python.readthedocs.io/en/latest/include-readme.html). They do all the heavy lifting.

## Script setup

Create a file .secrets in this folder with your login details for ESB networks and InfluxDB. This needs to be in the following format:

```
[InfluxDB]
bucket = esb
host = http://localhost:8086
organisation = <your org>
token = <your access token>
```

Install the requirements with `pip install -r requirements.txt`.

## Python virtual environment

It may be easiest to use a virtual environment:

1. Initialise the environment with `python -venv .venv`
2. Activate the environment with `source .venv/bin/activate`
3. That's it!

