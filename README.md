# log_analyzer
Analizer of nginx server logs.

## How to

Script requires python >= 3.7.

Example on Linux (for Windows - the same):

```bash
$ python log_analyzer.py --config <path_to_config_file>
```

The config should be provided as json file:

```bash
{
	"REPORT_SIZE": <count of top urls with maximum sum of request time>,
	"REPORT_DIR": "<directory for the reports>",
	"LOG_DIR": "<directory with nginx logs>",
	"SCRIPT_LOGS_FILE": "<file for script logs>"
}
```

## Tests

Run script tests with the following command:

```bash
$ python -m unittest tests/test.py
```