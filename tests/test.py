import unittest
import sys
from datetime import datetime

from log_analyzer import (
	find_recent_log_file,
	parse_file_info,
	parse_input_args,
	NginxLog
)



class TestFindRecentLogFile(unittest.TestCase):
	config = {
	    "REPORT_SIZE": 1000,
	    "REPORT_DIR": "./reports",
	    "LOG_DIR": "./tests/test_files/log"
	}

	def test_find_recent_log_file(self):
		res = find_recent_log_file(self.config)
		self.assertEqual(res, NginxLog('./tests/test_files/log/nginx-access-ui.log-20170630', datetime(2017, 6, 30, 0, 0)))

	def test_find_recent_log_file_gz(self):
		self.config["LOG_DIR"] = "./tests/test_files/gz_log"
		res = find_recent_log_file(self.config)
		self.assertEqual(res, NginxLog('./tests/test_files/gz_log/nginx-access-ui.log-20170630.gz', datetime(2017, 6, 30, 0, 0)))

	def test_find_recent_log_file_no_logs(self):
		self.config["LOG_DIR"] = "./tests/test_files/no_log"
		res = find_recent_log_file(self.config)
		self.assertEqual(res, NginxLog(None, datetime.min))


class TestParseFileInfo(unittest.TestCase):

	def test_find_recent_log_file(self):
		res = parse_file_info('./tests/test_files/log/nginx-access-ui.log-20170630')
		self.assertEqual(len(res), 1)
		self.assertEqual(len(res["/api/v2/banner/1"]), 7)
		self.assertEqual(res["/api/v2/banner/1"]["count"], 7)
		self.assertEqual(res["/api/v2/banner/1"]["count_perc"], 100)
		self.assertEqual(res["/api/v2/banner/1"]["time_perc"], 100)
		self.assertEqual(res["/api/v2/banner/1"]["time_sum"], 2.267)
		self.assertEqual(res["/api/v2/banner/1"]["time_max"], 0.704)
		self.assertEqual(res["/api/v2/banner/1"]["time_avg"], 0.324)
		self.assertEqual(res["/api/v2/banner/1"]["time_med"], 0.199)

	def test_find_recent_log_file_with_errors(self):
		res = parse_file_info('./tests/test_files/log/nginx-access-ui.log-20170629')
		self.assertEqual(len(res), 1)
		self.assertEqual(len(res["/api/v2/banner/1"]), 7)
		self.assertEqual(res["/api/v2/banner/1"]["count"], 3)
		self.assertEqual(res["/api/v2/banner/1"]["count_perc"], 42.857)
		self.assertEqual(res["/api/v2/banner/1"]["time_perc"], 100)
		self.assertEqual(res["/api/v2/banner/1"]["time_sum"], 0.841)
		self.assertEqual(res["/api/v2/banner/1"]["time_max"], 0.628)
		self.assertEqual(res["/api/v2/banner/1"]["time_avg"], 0.28)
		self.assertEqual(res["/api/v2/banner/1"]["time_med"], 0.146)

	def test_find_recent_log_file_empty(self):
		res = parse_file_info('./tests/test_files/log/empty_file')
		self.assertEqual(len(res), 0)


class TestParseInputArgs(unittest.TestCase):

	def test_parse_input_args(self):
		expected_config = {
			"REPORT_SIZE": 50,
		    "REPORT_DIR": "./new_reports",
		    "LOG_DIR": "./log",
		    "SCRIPT_LOGS_DIR": "./log_dir"
		}
		res = parse_input_args("./tests/test_files/config.json")
		self.assertEqual(res, expected_config)

	def test_parse_input_args_no_arg(self):
		expected_config = {
		    "REPORT_SIZE": 1000,
		    "REPORT_DIR": "./reports",
		    "LOG_DIR": "./log"
		}	
		res = parse_input_args('./default_config.json')
		self.assertEqual(res, expected_config)


	def test_parse_input_args_file_error(self):
		with self.assertRaises(FileNotFoundError):
			parse_input_args('./123')



