#!/bin/bash
export FLASK_APP=run.py
flask crontab add
gunicorn --bind 0.0.0.0:5000 src:app
