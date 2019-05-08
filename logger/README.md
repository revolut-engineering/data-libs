# Logger

Base logging configuration. Includes the following out of the box:

- writing to stderr (from INFO level). Highlights the log level with color.
- writing to file, rotated every hour
- writing to Google StackDriver, all fields, in json format

## Install

Install basic logger without additional handlers

```
pip install revlibs-logger
```

## Usage

```python
from revlibs.logger import get_logger

log = get_logger()

# We can also override some variable
log.debug("Debug message")
log.info("Info message")
log.warning("Warning message")
log.error("Error message")
log.critical("Critical message ")

# time.sleep(1)
try:
    0 / 0
except Exception as e:
    log.exception(e)
```

## Overrides

By default, `logging.yaml` that can be found in this package is used to configure logging. Stackdriver capabilities are added on initialization.
This yaml file is a template and can contain references to environment variables, such as `{HOME}`, etc
It is possible to use your own `logging.yaml` with _LOG_CONFIG_PATH_ environment variable.
You can also override those variables via _params_ variable:

```python
# This will make sure that only ERROR messages get written to console, and everything else is written to "some_other_file.log"
log = get_logger(params={"LOG_FILE_LOCATION": "some_other_file.log",  "LOG_LEVEL_CONSOLE": "ERROR"})
```

## Handlers

Additional handlers can be specified when installing or as dependencies:

```bash
revlibs-logger[stackdriver,slack]==0.3.0
```

These handlers may be included when instantiating your application's logger

```
logger = get_logger(add_handlers=['console', 'file', 'slack', 'stackdriver'])
```

For more details on specific handlers see:

- [Stackdriver logging](./README.md#stackdriver-logging)
- [Slack logging](./README.md#slack-logging)

### Console

Log levels are displayed colored. Default level is INFO.

Variables to override:

- **LOG_LEVEL_CONSOLE**: - default to INFO

### File logging

- **LOG_FILE_LOCATION**: - location of the file to write. Default is `/tmp/python-app.log`.
- **LOG_ROTATING_INTERVAL**: - how often to rotate the log file. Default is `h`. Valid values for the rotation schedule are here https://docs.python.org/3/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler
- **LOG_LEVEL_FILE**: - defaults to DEBUG

## Stackdriver logging

If **STACKDRIVER_LOGGING_ENABLE** environment is set to _TRUE_, logs are also written to Stackdriver

## Slack logging

**Warning**: sending Slack messages can be slow. Use only when reasonable.
It is also possible to write to slack, using logger called slack.
You need to set **LOG_SLACK_TOKEN** and **DEFAULT_SLACK_CHANNEL** variables via _params_ or environment:

```python
log = get_logger("slack", params={"DEFAULT_SLACK_CHANNEL": "errors", "LOG_SLACK_TOKEN": "<xxxxxxx>"}, add_handlers=['console', 'file', 'slack'])
```

Additional properties:

- **LOG_SLACK_USER**: - Defaults to _Logger_,
- **LOG_SLACK_TOKEN**: - is specified incorrectly, handler fails silently, no message is written. You just won't get any slack messages.
- **DEFAULT_SLACK_CHANNEL**: - Where to write the messages. Mandatory to specify.
