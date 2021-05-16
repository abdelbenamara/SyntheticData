#!/bin/bash
echo "pip install -r requirements.txt"
pip install -r requirements.txt

echo "pip install dpwgan/ --use-feature=in-tree-build"
pip install dpwgan/ --use-feature=in-tree-build
