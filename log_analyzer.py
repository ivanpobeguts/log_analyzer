#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gzip
import re
import json
import statistics
from string import Template
from datetime import datetime
from collections import namedtuple
import logging
import argparse


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


TEMPLATE_PATH = "./report.html"

ERROR_THRESHOLD = 0.5

logger = logging.getLogger(__name__)

NginxLog = namedtuple('NginxLog', 'log_path date')


def find_recent_log_file(config):
	path = config["LOG_DIR"]
	recent_log = NginxLog(None, datetime.min)
	for file_name in os.listdir(path):
		try:
			exp = re.search(r"^nginx-access-ui.log-(\d{8})(\.gz)?$", file_name)
			log_name = exp.group(0)
			date_str = exp.group(1)
			date = datetime.strptime(date_str, '%Y%m%d')
			if date > recent_log.date:
				recent_log = NginxLog("/".join([path, log_name]), date)
		except (AttributeError, ValueError) as e:
			pass
	return recent_log



def parse_file_info(path):
	requests_num = 0
	errors_num = 0
	sum_request_time = 0
	stat_dict = {}
	for line in fetch_file_lines(path):
		try:
			exp = re.search(r"\"((GET|POST|DELETE|PUT) (.+) HTTP/(1.0|1.1))(.+)(\d+\.\d{3})$", line)
			url = exp.group(3)
			request_time = exp.group(6)

			if url not in stat_dict:
				stat_dict[url] = {
					"count": 0,
					"time_sum": 0,
					"time_max": 0,
					"time_avg": 0,
					"time_values": [],
					"time_med": 0
				}
			stat_dict[url]["time_sum"] += float(request_time)
			stat_dict[url]["time_max"] = max(float(request_time), stat_dict[url]["time_max"])
			stat_dict[url]["time_avg"] = (stat_dict[url]["time_avg"] * stat_dict[url]["count"] + float(request_time)) / (stat_dict[url]["count"] + 1)
			stat_dict[url]["time_values"].append(float(request_time))
			stat_dict[url]["count"] += 1

			sum_request_time += float(request_time)
		except AttributeError as e:
			errors_num += 1

		requests_num += 1

	for url in stat_dict.keys():
		stat_dict[url]["time_med"] = round(statistics.median(stat_dict[url]["time_values"]), 3)
		stat_dict[url]["count_perc"] = round(stat_dict[url]["count"] / requests_num * 100, 3)
		stat_dict[url]["time_perc"] = round(stat_dict[url]["time_sum"] / sum_request_time * 100, 3)
		stat_dict[url]["time_avg"] = round(stat_dict[url]["time_avg"], 3)
		stat_dict[url]["time_sum"] = round(stat_dict[url]["time_sum"], 3)
		stat_dict[url]["time_max"] = round(stat_dict[url]["time_max"], 3)
		stat_dict[url].pop("time_values", None)


	try:
		if errors_num/requests_num >= ERROR_THRESHOLD:
			logger.info(f"Attention! {ERROR_THRESHOLD * 100} % of log file was not parsed!")
	except ZeroDivisionError:
		logger.info(f"No logs found in logfile {path}")
	return stat_dict


def fetch_file_lines(file_path):
	file_handler = gzip.open if file_path.endswith(".gz") else open
	with file_handler(file_path, "rb") as fp:
		for line in fp.readlines():
			line = line.decode('utf-8')
			yield line


def get_template_str(path=TEMPLATE_PATH):
	with open(path, "r") as file:
		return file.read()


def save_report(report_str, file_name, config):
	file_path = config["REPORT_DIR"]
	with open("/".join([file_path, file_name]), "w+") as file:
		file.write(report_str)


def prepare_dict_for_template(stat_dict, config):
	report_size = config["REPORT_SIZE"]
	table_json_list = []
	stat_dict = dict(sorted(stat_dict.items(), key=lambda x: x[1]["time_sum"], reverse=True)[:report_size])
	for k, v in stat_dict.items():
		v["url"] = k
		table_json_list.append(v)
	return {"table_json": table_json_list}


def render_template(stat_dict, config):
	template_str = get_template_str()
	table_json = prepare_dict_for_template(stat_dict, config)
	return Template(template_str).safe_substitute(table_json)


def get_args():
	parser = argparse.ArgumentParser(description='Config file')
	parser.add_argument('--config', type=str, default='./default_config.json', help='Custom script config')
	return parser.parse_args().config


def parse_input_args(config_file):
	config = {
	    "REPORT_SIZE": 1000,
	    "REPORT_DIR": "./reports",
	    "LOG_DIR": "./log"
	}	

	try:
		with open(config_file, 'r') as json_file:
			new_config = json.load(json_file)
			config = {**config, **new_config}
	except json.decoder.JSONDecodeError:
		pass
	except FileNotFoundError:
		err_mes = "Cannot parse config file"
		logger.error(err_mes)
		raise FileNotFoundError(err_mes)
	logging.basicConfig(
		     filename=config.get('SCRIPT_LOGS_DIR'),
		     level=logging.INFO, 
		     format= '[%(asctime)s] %(levelname).1s %(message)s',
		     datefmt='%Y.%m.%d %H:%M:%S'
			)
	return config


def main():
	try:
		config_file = get_args()
		config = parse_input_args(config_file)

		logger.info("Searching for recent log file...")
		recent_log = find_recent_log_file(config)

		if not recent_log.log_path:
			logger.info("No log file found")
			return

		logger.info(f"Log file {recent_log.log_path} found")

		logger.info("Parsing file...")
		file_info_dict = parse_file_info(recent_log.log_path)

		logger.info("Generate and save report")
		report_str = render_template(file_info_dict, config)
		report_file_path = f"report-{datetime.strftime(recent_log.date, '%Y.%m.%d')}.html"
		save_report(report_str, report_file_path, config)

		logger.info(f"Report was successfully built and is stored in {report_file_path}")
	except:
		logger.exception("Unexpected error")



if __name__ == "__main__":
    main()
