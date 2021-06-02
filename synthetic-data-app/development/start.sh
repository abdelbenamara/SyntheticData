#!/bin/bash
echo "start.sh"
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
