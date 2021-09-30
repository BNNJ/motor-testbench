#!/usr/bin/env python3

import argparse
import json

import testbenchconstants as tbc

from sys import exit
from os import kill
from signal import SIGHUP

from testbenchdaemon import TestBenchDaemon

def parse_args():
	argp = argparse.ArgumentParser(
		description=("Motor testbench utility.")
	)

	argp.add_argument(
		"cmd",
		nargs="?",
		choices=["start", "stop", "restart"],
		help="start/stop/restart the daemon"
	)

	argp.add_argument(
		"--start",
		action="store_const",
		const=tbc.CMD_START,
		dest="cmdnum",
		help="Start cycling"
	)
	argp.add_argument(
		"--stop",
		action="store_const",
		const=tbc.CMD_STOP,
		dest="cmdnum",
		help="Stop cycling"
	)
	argp.add_argument(
		"--pause",
		action="store_const",
		const=tbc.CMD_PAUSE,
		dest="cmdnum",
		help="Pause cycling"
	)
	argp.add_argument(
		"--resume",
		action="store_const",
		const=tbc.CMD_RESUME,
		dest="cmdnum",
		help="Resume cycling"
	)
	argp.add_argument(
		"--info",
		action="store_const",
		const=tbc.CMD_INFO,
		dest="cmdnum",
		help="Display cycle information"
	)

	def percentage(arg):
		x = int(arg)
		if -100 <= x <= 100 and x != 0:
			return x
		else:
			raise ValueError

	argp.add_argument(
		"-b", "--brake",
		type=percentage,
		metavar="X%",
		help="Powder brake current change. Requires a value between -100 and 100."
	)

	return argp.parse_args()

if __name__ == "__main__":
	args = parse_args()

	daemon = TestBenchDaemon(
		pidfile=tbc.PID_FILE,
		cmdfile=tbc.CMD_FILE,
		influxcfgfile=tbc.INFLUXDB_CFG,
		bucket="rnd-center-test",
		logfile=tbc.LOG_FILE,
		std_out=tbc.STD_OUT,
		std_err=tbc.STD_ERR
	)
	if args.cmd is not None:
		if args.cmd == "start":
			daemon.start()
		elif args.cmd == "stop":
			daemon.stop()
		elif args.cmd == "restart":
			daemon.restart()
	else:
		if args.brake:
			data = {
				'cmd': tbc.CMD_BRAKE,
				'value': args.brake
			}
		else:
			data = {'cmd': args.cmdnum}
		try:
			with open(tbc.PID_FILE, 'r') as f:
				pid = int(f.read())
		except IOError:
			print("Daemon is not running")
			exit(1)
		except:
			print("Error")
		with open(tbc.CMD_FILE, 'w') as f:
			f.write(json.dumps(data))
		kill(pid, SIGHUP)