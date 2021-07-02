#!/bin/bash
export FLASK_APP=run.py
export FLASK_ENV=production
flask crontab add
gunicorn --bind 0.0.0.0:5000 src:app
