#!/usr/bin/env python3

import sys
import os
import time
import atexit
import signal

class Daemon:

	def __init__(self, *, pidfile=None, std_in=os.devnull, std_out=os.devnull, std_err=os.devnull):
		self.pidfile = pidfile
		self.std_in = open(std_in, 'r')
		self.std_out = open(std_out, 'a+')
		self.std_err = open(std_err, 'a+')

	def daemonize(self):
		"""Deamonize class. UNIX double fork mechanism."""

		try:
			pid = os.fork()
			if pid > 0:
				# exit first parent
				sys.exit(0)
		except OSError as err:
			sys.stderr.write('fork #1 failed: {0}\n'.format(err))
			sys.exit(1)

		# decouple from parent environment
		os.chdir('/')
		os.setsid()
		os.umask(0)

		# do second fork
		try: 
			pid = os.fork()
			if pid > 0:
				# exit from second parent
				sys.exit(0)
		except OSError as err:
			sys.stderr.write('fork #2 failed: {0}\n'.format(err))
			sys.exit(1)

		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		# si = open(self.std_in, 'r')
		# so = open(self.std_out, 'a+')
		# se = open(self.std_err, 'a+')

		os.dup2(self.std_in.fileno(), sys.stdin.fileno())
		os.dup2(self.std_out.fileno(), sys.stdout.fileno())
		os.dup2(self.std_err.fileno(), sys.stderr.fileno())

		# write pidfile

		pid = str(os.getpid())
		with open(self.pidfile,'w+') as f:
			f.write(pid + '\n')
		atexit.register(self.del_pid)

	def del_pid(self):
		os.remove(self.pidfile)

	def get_pid(self):
		with open(self.pidfile,'r') as pf:
			pid = int(pf.read().strip())
		return pid

	def start(self):
		"""Start the daemon."""

		# Check for a pidfile to see if the daemon already runs
		try:
			pid = self.get_pid()
		except IOError:
			pid = None

		if pid:
			message = "pidfile {0} already exist. " + \
					"Daemon already running?\n"
			sys.stderr.write(message.format(self.pidfile))
			sys.exit(1)
		
		# Start the daemon
		self.daemonize()
		self.run()

	def stop(self):
		"""Stop the daemon."""

		# Get the pid from the pidfile
		try:
			pid = self.get_pid()
		except IOError:
			pid = None

		if not pid:
			message = "pidfile {0} does not exist. " + \
					"Daemon not running?\n"
			sys.stderr.write(message.format(self.pidfile))
			return # not an error in a restart

		# Try killing the daemon process
		try:
			while 1:
				os.kill(pid, signal.SIGTERM)
				time.sleep(0.1)
		except OSError as err:
			e = str(err.args)
			if e.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print(str(err.args))
				sys.exit(1)

	def restart(self):
		"""Restart the daemon."""
		self.stop()
		self.start()

	def run(self):
		pass
