#!/usr/bin/env python3

import time
import atexit
import json
import argparse
import requests

# import testio as gpio
import testbenchgpio as gpio
from threading import Thread
from datetime import datetime
from timeit import default_timer as timer
from queue import Queue
from flask import Flask, request
from influxdb_client import InfluxDBClient, Point

def timestamp():
	return datetime.timestamp(datetime.now())

# Motor control
def change_motor_pwm(value):
	global motor_pwm
	motor_pwm = value
	gpio.change_motor_pwm(value)

def change_brake_pwm(value):
	global brake_pwm
	brake_pwm = value
	gpio.change_brake_pwm(value)

def move():
	for pwm in range(20, 101, 10):
		change_motor_pwm(pwm)
		time.sleep(0.2)
	time.sleep(14)
	for pwm in range(100, 19, -10):
		change_motor_pwm(pwm)
		time.sleep(0.2)
	change_motor_pwm(0)
	time.sleep(1)

def cycle():
	global log_data
	log_data = True
	for move_count in range(150):
		while paused:
			log_data = False
			time.sleep(0.5)
		log_data = True
		if not test_running:
			break
		move()
		queue.put({'test_moves_cnt': move_count})
	change_motor_pwm(0)
	time.sleep(1)
	gpio.inverse_motor_dir()
	for move_count in range(150):
		while paused:
			log_data = False
			time.sleep(0.5)
		log_data = True
		if not test_running:
			break
		move()
		queue.put({'test_moves_cnt': move_count + 150})

# Data and logging
def data_acquisition():
	i = 0
	global motor_driver_error, motor_driver_chop
	while True:
		s = timer()
		data = gpio.get_data()
		data['test_powder_brake_pwm'] = brake_pwm
		data['test_motor_pwm'] = motor_pwm
		drv_error, drv_chop = gpio.test_motor_driver()
		if drv_error != motor_driver_error:
			queue.put({'test_motor_drv_fault': drv_error})
			motor_driver_error = drv_error
		if drv_chop != motor_driver_chop:
			queue.put({'test_motor_drv_chop': drv_chop})
			motor_driver_chop = drv_chop
		if log_data:
			queue.put(data)
		e = timer()
		t = e - s
		if t < 1:
			time.sleep(1 - t)

"""
def db_log():
	while True:
		data = queue.get()
		print(data)
		# with open(logfile, 'a') as f:
		# 	data = queue.get()
		# 	f.write(json.dumps(data) + '\n')
"""
def db_log():
	with InfluxDBClient.from_config_file(influxcfgfile) as client:
		with client.write_api() as wapi:
			while True:
				data = queue.get()
				points = [
					Point("motorbench").field(k, v)
					for k, v in data.items()
				]
				wapi.write(bucket=bucket, record=points)

def main():
	gpio.setup()
	atexit.register(gpio.cleanup)

	Thread(target=db_log).start()
	Thread(target=data_acquisition).start()

	# initial move to shuffle powder
	queue.put({'running_brake_commissioning': "..."})
	move()
	queue.put({'brake_commissioning_finished': "..."})

	change_brake_pwm(50)
	while True:
		cycle_count = 0
		while test_running:
			cycle()
			cycle_count += 1
			queue.put({'test_cycles_cnt': cycle_count})
		while not test_running:
			time.sleep(1)

class TestBenchFlask(Flask):
	def __init__(self, import_name):
		global queue, paused, test_running, motor_pwm, brake_pwm, influxcfgfile, bucket, log_data, motor_driver_error, motor_driver_chop, motor_name

		# base_path = "/home/pi/motor-testbench/V2"
		influxcfgfile = "/home/pi/motor-testbench/V2/static/influxdb.cfg"
		bucket = "rnd-center-test"
		# logfile = f"{base_path}/logfile.log"

		queue = Queue()
		bucket = "rnd-center-test"
		paused = True
		test_running = False
		motor_pwm = 0
		brake_pwm = 100
		log_data = False
		motor_driver_error = False
		motor_driver_chop = False
		motor_name = "robert"

		Thread(target=main).start()

		super().__init__(import_name)

app = TestBenchFlask(__name__)

# Commands / Routes

@app.route("/", methods=['POST'])
def post():
	cmd = request.form.get("cmd", None)
	if isinstance(cmd, str):
		cmd = cmd.lower()
	brake = request.form.get("brake", None)
	name = request.form.get("motor_name", None)
	if isinstance(brake, str):
		brake = brake.lower()
	if cmd == 'start':
		return start_test()
	elif cmd == 'stop':
		return stop_test()
	elif cmd == 'pause':
		return pause_test()
	elif cmd == 'resume':
		return resume_test()
	elif cmd == 'status':
		return status()
	elif brake == 'decrease':
		return decrease_brake(10)
	elif brake == 'increase':
		return increase_brake(10)
	elif brake is not None:
		return set_brake(int(brake))
	elif motor_name is not None:
		return set_motor_name(name)
	else:
		return f"unkown command: {request.form}>"

@app.route("/")
def root():
	return "There's nothing here. Go away."

@app.route("/status")
def status():
	return (
		f"running: {test_running}\n"
		f"paused: {paused}"
	)

@app.route("/motor/<name>")
def set_motor_name(name):
	global motor_name
	motor_name = name
	queue.put({'motor_name': motor_name})
	return f"motor name changed to {motor_name}"

@app.route("/cmd/start")
def start_test():
	global test_running, paused
	if test_running:
		return "test is already running"
	test_running = True
	paused = False
	queue.put({'test_start_date': timestamp()})
	queue.put({'test_status': "started"})
	return "test start command sent..."

@app.route("/cmd/stop")
def stop_test():
	global test_running, paused
	if not test_running:
		return "test is not running"
	test_running = False
	paused = True
	queue.put({'test_status': "stopped"})
	return "test stop command sent..."

@app.route("/cmd/pause")
def pause_test():
	global paused
	if paused:
		return "test is already paused"
	paused = True
	queue.put({'test_status': "paused"})
	queue.put({'test_pause_date': timestamp()})
	return "test pause command sent..."

@app.route("/cmd/resume")
def resume_test():
	global paused
	if not paused:
		return "test is already running"
	paused = False
	queue.put({'test_status': "resumed"})
	queue.put({'test_pause_date': None})
	return "test resume command sent..."

@app.route("/brake/<int:val>")
def set_brake(val=None):
	global brake_pwm
	if val is not None:
		brake_pwm = val
	if brake_pwm < 0: brake_pwm = 0
	elif brake_pwm > 100: brake_pwm = 100
	change_brake_pwm(brake_pwm)
	queue.put({'test_powder_brake_pwm': brake_pwm})
	return f"brake_current changed to {brake_pwm}"

@app.route("/brake-decrease/<int:val>")
def increase_brake(val):
	global brake_pwm
	brake_pwm += val
	return set_brake()

@app.route("/brake-increase/<int:val>")
def decrease_brake(val):
	global brake_pwm
	brake_pwm -= val
	return set_brake()

