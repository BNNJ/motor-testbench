#!/bin/bash

/home/pi/.local/bin/gunicorn --bind 0.0.0.0:8080 testbench:app
