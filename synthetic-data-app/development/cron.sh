#!/bin/bash
export FLASK_APP=run.py
flask crontab add
flask crontab show
