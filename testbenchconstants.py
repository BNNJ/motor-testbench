BASE_DIR = "/home/pfragnou/"

PID_FILE = BASE_DIR + "test.pid"
STD_OUT = BASE_DIR + "stdout.log"
STD_ERR = BASE_DIR + "stderr.log"
CMD_FILE = BASE_DIR + "command.json"
LOG_FILE = BASE_DIR + "test.log"
INFLUXDB_CFG = BASE_DIR + "influxdb.ini"

token = "9Hh0tI2oZQUxuzD5qjNoEAyjW9q6Uo7QqwtAUl0FTm-eT3fWcKt-9Ul05M_YMZUwb7F6zxXw-yDTcfsHQ1yuZQ=="
token_test = "8iRF6DgsYqRTXvCKVapPDXTGlr8e-T7vtiUkGpXzOpCvxbOiuv7HCVdbxRHxrD4bAFFwO6LEdHz8_aJ0Wii0TQ=="

CMD_START	= 1
CMD_STOP	= 2
CMD_PAUSE	= 3
CMD_RESUME	= 4
CMD_INFO	= 5
CMD_BRAKE 	= 6