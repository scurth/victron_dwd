# About
This script is used to set Victron System minimum battery state of charge (MinimumSocLimit) to a higher level if a storm warning for as specific region is published by DWD.

# Installation

```console
pip install -r requirements.txt
```

# Help

```console
./dwd-warning.py -h
Usage: dwd_warning.py -s XXX [-v] [-b] [-p] [-u] [-r] [-h]
-v: verbose output, default False
-b: MQTT Broker IP, default 127.0.0.1
-p: MQTT Broker Port, default 1883
-r: DWD region, default 112069000 = Potsdam-Mittelmark
-s: Victron Serial Number, mandatory, no default
-u: DWD warnings.json url, default https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json
-h: shows this help
```
