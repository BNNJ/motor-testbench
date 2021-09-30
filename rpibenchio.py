import RPi.GPIO as GPIO
import smbus
import time

ADS1115_ADDR = 0x48
## ADS1115 Config  Constants
OS = 0
# Single-ended analog inputs
AIN0 = 0b100
AIN1 = 0b101
AIN2 = 0b110
AIN3 = 0b111

PGA = 0b001 # FSR=+-4.096V
MODE = 0 # Continuous conversion
DR = 0b100 # 128 SPS

COMP_MODE = 0
COMP_POL = 0
COMP_LAT = 0
COMP_QUE = 0b11 # Comparator disabled, alert pin high-z

CONFIG_MASK = OS<<15 | PGA<<9 | MODE<<8 | DR<<5 | COMP_MODE<<4 | COMP_POL<<3 | COMP_LAT<<2 | COMP_QUE<<0


def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)		# brake current = 0A
	GPIO.setup(13, GPIO.OUT, initial=GPIO.LOW)		# motor stopped
	GPIO.setup(4, GPIO.IN)
	GPIO.setup(5, GPIO.IN)
	GPIO.setup(6, GPIO.IN)
	GPIO.setup(19, GPIO.OUT, initial=GPIO.LOW)		# motor direction

	brake = GPIO.PWM(12, 10000)
	brake.start(100)
	motor = GPIO.PWM(13, 10000)
	motor.start(0)

	GPIO.add_event_detect(5, GPIO.FALLING, callback=lambda _: print("Motor driver error !"))
	GPIO.add_event_detect(6, GPIO.FALLING, callback=lambda _: print("Motor driver chopping !"))
	bus = smbus.SMBus(1)
	return bus, motor, brake

def inverse_motor_dir():
	GPIO.output(19, not GPIO.input(19))

def change_duty_cycle(dev, val):
	dev.ChangeDutyCycle(val)

def ADS1115_init(bus, mux):
	mux &= 0b111
	config = CONFIG_MASK | mux<<12
	config = ((config & 0xff) << 8) + (config >> 8)	# Change byte order
	bus.write_word_data(ADS1115_ADDR, 1, config)

def ADS1115_read_blocking(bus, pin):
	ADS1115_init(bus, pin)

	time.sleep(0.05) # give some time to get samples averaged

	bear = bus.read_word_data(ADS1115_ADDR, 0)
	bear = ((bear & 0xff) << 8) + (bear >> 8)	# Change byte order
	# bear = int.from_bytes(bear.to_bytes(2, 'big'), byteorder='little', signed=True)
	bear = bear * 0.000125 # LSB at 125uV at FS=+-4.096V
	return bear

def motor_driver_error():
	return GPIO.input(5) == GPIO.LOW

def motor_driver_chopping():
	return GPIO.input(6) == GPIO.LOW

def motor_current(val):
	# 30mV offset, 10m shunt resistance, 19.8 gain
	return (val - 0.03) / 0.01 / 19.8

def pbrake_current(val):
	# 110mV/A
	return (val - 3.3/2) / 0.110

def motor_rail(val):
	# psu voltage
	return val * 11.0

def get_data(bus):
	data = {}
	# data['pot'] = ADS1115_read_blocking(bus, AIN0)
	data['test_motor_current'] = motor_current(ADS1115_read_blocking(bus, AIN1))
	data['test_powder_brake_current'] = pbrake_current(ADS1115_read_blocking(bus, AIN2))
	data['test_psu_voltage'] = motor_rail(ADS1115_read_blocking(bus, AIN3))
	return data

def cleanup():
	GPIO.cleanup()