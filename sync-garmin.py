#!/usr/bin/env python3

from garminconnect import (
  Garmin,
  GarminConnectConnectionError,
  GarminConnectTooManyRequestsError,
  GarminConnectAuthenticationError,
)
import datetime
from influxdb_client_3 import InfluxDBClient3, Point, WritePrecision
import configparser
import logging
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()
logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stdout)

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Debug mode enabled.")

class GarminImport:
  def __init__(
    self,
    config_file_path,
  ):
    logging.debug("reading config")
    self.config = configparser.ConfigParser()
    self.config.read(config_file_path)
    self.influx_client = self.__get_influx_client()
    self.garmin_client = self.__get_garmin_client()
    self.date = datetime.date.today() - datetime.timedelta(days=1)

  def __get_garmin_client(self):
    try:
      client = Garmin()
      client.login("~/.garminconnect")
    except (
      GarminConnectConnectionError,
      GarminConnectAuthenticationError,
      GarminConnectTooManyRequestsError,
    ) as err:
      print(f"Error occurred during Garmin Connect Client get initial client: {err}")
      quit()
    except Exception:
      print("Unknown error occurred during Garmin Connect Client get initial client")
      quit()
    return client

  def __get_influx_client(self):
    host = self.config.get("InfluxDB", "host")
    bucket = self.config.get("InfluxDB", "bucket")
    org = self.config.get("InfluxDB", "organisation")
    token = self.config.get("InfluxDB", "token")

    return InfluxDBClient3(
      token = token,
      host = host,
      org = org,
      database = bucket,
    )

  def __write_heart_rates(self):
    data = self.garmin_client.get_heart_rates(self.date.isoformat())
    values = data.get('heartRateValues')
   
    points = []
    for timestamp, heart_rate in values:
      dt = datetime.datetime.fromtimestamp(timestamp / 1000, datetime.UTC)
      point = (
        Point("heart_rate")
        .time(dt)
        .tag("source", "garmin")
        .field("value", heart_rate)
      )
      points.append(point) 
      
    self.influx_client.write(points)
    logging.info("heart rates written to influx")

  def __write_step_data(self):
    data = self.garmin_client.get_steps_data(self.date.isoformat())

    points = []
    for entry in data:
      point = (
        Point("steps")
        .tag("activity", entry['primaryActivityLevel'])
        .field("value", entry['steps'])
        .time(entry['endGMT'], WritePrecision.NS)
      )
      points.append(point) 
    self.influx_client.write(points)
    logging.info("step data written to influx")

  def __write_sleep_data(self):
    data = self.garmin_client.get_sleep_data(self.date.isoformat())
    sleep_data = data.get('dailySleepDTO')

    point = (
      Point("sleep")
      .field("total_sleep_time", sleep_data['sleepTimeSeconds'])
      .field("nap_time", sleep_data['napTimeSeconds'])
      .field("deep_sleep", sleep_data['deepSleepSeconds'])
      .field("light_sleep", sleep_data['lightSleepSeconds'])
      .field("rem_sleep", sleep_data['remSleepSeconds'])
      .field("awake_time", sleep_data['awakeSleepSeconds'])
      .field("sleep_score", sleep_data['sleepScores']['overall']['value'])
      .time(datetime.datetime.fromtimestamp(sleep_data['sleepStartTimestampGMT'] / 1000, datetime.UTC), WritePrecision.NS)
    )
    self.influx_client.write(point)
    logging.info("sleep data written to influx")

  def write_data(self):
    logging.info(f"Starting Garmin connect sync for {self.date.isoformat()}")
    self.__write_heart_rates()
    self.__write_step_data()
    self.__write_sleep_data()

GarminImport(".secrets").write_data()
