#!/bin/bash
flask crontab add
gunicorn --bind 0.0.0.0:5000 src:app
