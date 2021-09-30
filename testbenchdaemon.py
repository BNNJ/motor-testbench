#!/usr/bin/env python3

import logging
import time
import json
import atexit

# import rpibenchio
import testio as rpibenchio
import testbenchconstants as tbc

from datetime import datetime
from signal import signal, SIGHUP
from timeit import default_timer as timer
from threading import Thread
from queue import Queue

from daemonclass import Daemon

class TestBenchDaemon(Daemon):

	def __init__(self, cmdfile, influxcfgfile, bucket, logfile=None, **kwargs):
		self.test_on = False
		self.paused = True
		self.bus, self.motor, self.brake = rpibenchio.setup()
		self.motor_pwm = 0
		self.pbrake_pwm = 100
		self.queue = Queue()
		self.cmdfile = cmdfile
		self.influxcfgfile = influxcfgfile
		self.bucket = bucket

		signal(SIGHUP, self.handle_signal)

		atexit.register(rpibenchio.cleanup)
		super().__init__(**kwargs)

	def handle_signal(self, signum, stack_frame):
		with open(self.cmdfile, 'r+') as f:
			data = json.load(f)
			# f.write("")
		if data['cmd'] == tbc.CMD_START:
			self.test_on = True
			self.paused = False
			self.queue.put({'test_status': "started"})
		elif data['cmd'] == tbc.CMD_STOP:
			self.test_on = False
			self.paused = True
			self.queue.put({'test_status': "stopped"})
		elif data['cmd'] == tbc.CMD_PAUSE:
			self.paused = True
			self.queue.put({'test_status': "paused"})
			self.queue.put({'test_pause_date': self.timestamp()})
		elif data['cmd'] == tbc.CMD_RESUME:
			self.paused = False
			self.queue.put({'test_status': "resumed"})
			self.queue.put({'test_pause_date': None})
		elif data['cmd'] == tbc.CMD_BRAKE:
			self.pbrake_pwm += data['value']
			if self.pbrake_pwm < 0: self.pbrake_pwm = 0
			elif self.pbrake_pwm > 100: self.pbrake_pwm = 100
			rpibenchio.change_duty_cycle(self.brake, self.pbrake_pwm)
			self.queue.put(
				{
					'event': f"powder brake pwm changed by {data['value']}%",
					'test_powder_brake_pwm': self.pbrake_pwm
				}
			)

	def timestamp(self):
		return datetime.timestamp(datetime.today())

	def db_log(self, config_file):
		while True:
			with open("/home/pfragnou/test.log", 'a') as f:
				data = self.queue.get()
				f.write(json.dumps(data) + '\n')

	# def db_log(self, config_file):
	# 	with InfluxDBClient.from_config_file(config_file) as client:
	# 		with client.write_api() as wapi:
	# 			while True:
	# 				data = self.queue.get()
	# 				points = [
	# 					Point("motorbench").field(k, v)
	# 					for k, v in data.items()
	# 				]
	# 				wapi.write(bucket=self.bucket, record=points)

	def data_acquisition(self):
		i = 0
		while True:
			s = timer()
			data = rpibenchio.get_data(self.bus)
			data['test_powder_brake_pwm'] = self.pbrake_pwm
			data['test_motor_pwm'] = self.motor_pwm
			if not self.paused:
				self.queue.put(data)
			e = timer()
			time.sleep(1 - (e-s))

	def move(self):
		for pwm in range(20, 100, 10):
			self.motor_pwm = pwm
			rpibenchio.change_duty_cycle(self.motor, pwm)
			time.sleep(0.2)
		self.motor_pwm = 100
		rpibenchio.change_duty_cycle(self.motor, 100)
		time.sleep(14)
		for pwm in range(100, 20, -10):
			self.motor_pwm = pwm
			rpibenchio.change_duty_cycle(self.motor, pwm)
			time.sleep(0.2)
		rpibenchio.change_duty_cycle(self.motor, 20)
		time.sleep(1)

	def start_cycle(self):
		self.queue.put({'cycle_start_date': self.timestamp()})
		for move in range(150):
			while self.paused:
				time.sleep(0.5)
			if not self.test_on:
				break
			self.move()
			self.queue.put({'test_moves_cnt': move})
		rpibenchio.change_duty_cycle(self.motor, 0)
		time.sleep(2)
		rpibenchio.inverse_motor_dir()
		for move in range(150):
			while self.paused:
				time.sleep(0.5)
			if not self.test_on:
				break
			self.cycle()
			self.queue.put({'test_moves_cnt': move + 150})

	def run(self):
		# initial move to shuffle powder
		self.move()
		rpibenchio.change_duty_cycle(self.brake, 50)

		Thread(target=self.db_log, args=(self.influxcfgfile, )).start()
		Thread(target=self.data_acquisition).start()

		self.queue.put({'test_start_date': self.timestamp()})
		cycle_count = 0
		while True:
			cycle_count += 1
			if self.test_on:
				self.start_cycle()
				self.queue.put({'test_cycles_cnt': cycle_count})
			time.sleep(1)
