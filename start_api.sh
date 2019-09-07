#!/bin/sh
kill -9 `ps -ef | grep 8010 | grep tripitaka_ocr_web.py | awk -F" " {'print $2'}` 2>/dev/null
cd `dirname $0`
nohup python3 tripitaka_ocr_web.py --port=8010 >> tripitaka_ocr.log 2>&1 &
