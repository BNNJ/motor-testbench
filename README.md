# Motor Testbench

A tool aimed to power the tracker's motor with start/stop ramps while braking the motoreducer shaft.
Braking is achieved with a powder brake, electrically.
SW is will run on linux-based system (Raspberry Pi 3B or 4) and will be written in Python 3.
Realtime information as well as the number of cycles done since start of cycling will be published in influx.

Influx data values can then be shown on Grafana dashboard interface, which is convenient to use.

Run this with gunicorn (or uWSGI, or a WSGI server of your choice) as a service with systemd, then use the API with requests.
```bash
gunicorn --workers=X testbench:app
```

## STATUS:

CLI: :heavy_check_mark:  
API: :heavy_check_mark:  
DB logging: :heavy_check_mark:  

Are motor_driver_error and motor_driver_chop right ?  
InfluxDB bucket is still rnd-center-test  
Add a command/tool to query the database ?


## API:

GET:
```
/cmd/<start|stop|pause|resume>
/brake/<absolute value>
/brake-increase/<value>
/brake-decrease/<value>
/motor/<name>
```

The same functionalities are available with a POST request on '/', by passing the appropriate key/value pairs as payload:
```python
{'cmd': "start"}
{'cmd': "stop"}
{'cmd': "pause"}
{'cmd': "resume"}
{'brake': "increase"} # +10
{'brake': "decrease"} # -10
{'brake': value}
{'motor_name': name}
```

## CLI Usage:


```bash
$ ./testbenchcli.py [-n/--name X] [-b/--brake X] [start|stop|pause|resume|status]
```
| arg            | effect |
|----------------|--------|
| start          | start testing                     |
| stop           | stop testing                      |
| pause          | pause the current test            |
| resume         | resume the previously paused test |
| status         | display current test statusstatus |
| -b / --brake X | change the brake current to X     |
| -n / --name X  | change the motor name to X        |
| -h / --help    | display help                      |
