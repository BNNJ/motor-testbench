#!/usr/bin/env python3

import argparse
import json
import testbenchconstants as tbc

from sys import exit

def parse_args():
	argp = argparse.ArgumentParser(
		description=("Motor testbench utility.")
	)

	argp.add_argument(
		"--start",
		action="store_const",
		const=tbc.CMD_START,
		dest="cmd",
		help="Start cycling"
	)
	argp.add_argument(
		"--stop",
		action="store_const",
		const=tbc.CMD_STOP,
		dest="cmd",
		help="Stop cycling"
	)
	argp.add_argument(
		"--pause",
		action="store_const",
		const=tbc.CMD_PAUSE,
		dest="cmd",
		help="Pause cycling"
	)
	argp.add_argument(
		"--resume",
		action="store_const",
		const=tbc.CMD_RESUME,
		dest="cmd",
		help="Resume cycling"
	)
	argp.add_argument(
		"--info",
		action="store_const",
		const=tbc.CMD_INFO,
		dest="cmd",
		help="Display test information"
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
		help="Powder brake current change. Requires a non-zero value between -100 and 100."
	)

	args = argp.parse_args()
	if args.cmd is not None and args.brake is not None:
		argp.print_help()

	return argp.parse_args()

if __name__ == "__main__":
	args = parse_args()


	# try:
	# 	with open(tbc.PID_FILE, 'r') as f:
	# 		pid = int(f.read())
	# except IOError:
	# 	print("Daemon is not running")
	# 	exit(1)
	# except:
	# 	print("Error")
	# 	exit(1)
	if args.brake is not None:
		data = {
			'cmd': tbc.CMD_BRAKE,
			'value': args.brake
		}
	else:
		data = {'cmd': args.cmd}
	print(data)
	# with open(tbc.CMD_FILE, 'w') as f:
	# 	f.write(json.dumps(data))
	# os.kill(pid, signal.SIGHUP)
