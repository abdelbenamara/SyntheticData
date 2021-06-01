#!/bin/bash
apt-get update
apt-get upgrade
apt-get -y install cron
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
pip install gunicorn
mkdir instance
mkdir instance/resources
mkdir instance/results
