#!/bin/bash
source /root/reddit-trends/bin/activate
cd /root/reddit-trends
python report_generation.py --languages zh --skip-mongodb &

