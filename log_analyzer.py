#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gzip
import re
import statistics
from string import Template
from datetime import datetime
from collections import namedtuple


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

TEMPLATE_PATH = "./report.html"

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def find_recent_log_file(path="./log"):
	NginxLog = namedtuple('NginxLog', 'log_path date')
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
			print(e)
		except Exception as e:
			print(e)
	return recent_log



def parse_file_info(path="./log/nginx-access-ui.log-20170630"):
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
	return stat_dict, requests_num, errors_num


def fetch_file_lines(file_path):
	file_handler = gzip.open if file_path.endswith(".gz") else open
	with file_handler(file_path, "rb") as fp:
		for line in fp.readlines():
			line = line.decode('utf-8')
			yield line


def get_template_str(path=TEMPLATE_PATH):
	with open(path, "r") as file:
		return file.read()


def save_report(report_str, file_name, file_path=config["REPORT_DIR"]):
	with open("/".join([file_path, file_name]), "w+") as file:
		file.write(report_str)


def prepare_dict_for_template(stat_dict):
	table_json_list = []
	stat_dict = dict(sorted(stat_dict.items(), key=lambda x: x[1]["time_sum"], reverse=True)[:config["REPORT_SIZE"]])
	for k, v in stat_dict.items():
		v["url"] = k
		table_json_list.append(v)
	return {"table_json": table_json_list}


def render_template(stat_dict):
	template_str = get_template_str()
	table_json = prepare_dict_for_template(stat_dict)
	return Template(template_str).safe_substitute(table_json)


def main():
	recent_log = find_recent_log_file()
	result = parse_file_info(recent_log.log_path)
	report_str = render_template(result[0])
	save_report(report_str, f"report-{datetime.strftime(recent_log.date, '%Y.%m.%d')}.html")


if __name__ == "__main__":
    main()
