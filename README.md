Motor Testbench
===============

A tool aimed to power the tracker's motor with start/stop ramps while braking the motoreducer shaft.
Braking is achieved with a powder brake, electrically.
SW is made for linux-based system (Raspberry Pi 3B or 4) and is written in Python 3.
Realtime information as well as the number of cycles done since start of cycling will be published in influx.

Influx data values can then be shown on Grafana dashboard interface, which is convenient to use.

Usage:
--------------------------------

```bash
$ ./testbench.py [start|stop|restart]
```
| arg         | effect |
|-------------|--------|
| start       | start the daemon           |
| stop        | stop the daemon            |
| restart     | stop then start the daemon |
| -h / --help | display help               |

```bash
$ ./testbenchcli.py [--start|--stop|--pause|--resume|--info|--brake X]
```
| arg            | effect |
|----------------|--------|
| --start        | start testing                     |
| --stop         | stop testing                      |
| --pause        | pause the current test            |
| --resume       | resume the previously paused test |
| --info         | display status/info               |
| -b / --brake X | change the brake current by X     |
| -h / --help    | display help                      |
