#!/bin/bash
echo "setup.sh"
pip install --upgrade pip
pip install -U virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir instance
mkdir instance/resources
mkdir instance/results
