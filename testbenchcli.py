#!/usr/bin/env python3

import argparse
import requests

def parse_args():
	argp = argparse.ArgumentParser(description="Motor testbench utility.")

	argp.add_argument(
		"cmd",
		choices=["start", "stop", "pause", "resume", "status"],
		nargs="?",
		help="Commands to send."
	)

	argp.add_argument(
		"-b", "--brake",
		help="Powder brake current change. Requires a non-zero value between -100 and 100."
	)

	argp.add_argument(
		"-n", "--name",
		help="Change motor name."
	)

	return argp.parse_args()

if __name__ == "__main__":
	args = parse_args()
	if args.cmd:
		req = {'cmd': args.cmd}
	elif args.name:
		req = {'motor_name': args.name}
	elif args.brake:
		req = {'brake': args.brake}
	try:
		r = requests.post("http://192.168.1.115:8080", req)
		if r.status_code == 200:
			print(r.text)
		else:
			print("request failed")
	except Exception as e:
		print("connection failed")
	# print(req)