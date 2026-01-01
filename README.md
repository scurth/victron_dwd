# About
This script is used to set Victron System minimum battery state of charge (MinimumSocLimit) to a higher level if a storm warning for as specific region is published by DWD.

# Installation

```console
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

# Development

## Code Quality

This project uses `ruff` for linting and formatting:

```console
# Check for issues
ruff check .

# Auto-fix what can be fixed
ruff check --fix .

# Format code
ruff format .

# Run both check and format
ruff check --fix . && ruff format .
```
# Find your Area ID

[Google Earth KML File](https://maps.dwd.de/geoserver/dwd/wms?service=WMS&version=1.1.0&request=GetMap&layers=dwd:Warngebiete_Kreise&styles=&bbox=5.86625035072566,47.2701236047002,15.0418156516163,55.0583836008072&width=768&height=651&srs=EPSG:4326&format=application%2Fvnd.google-earth.kml%2Bxml) 
Each Area details contain a unique WARNCELLID. This WARNCELLID is the value you should use for the `-r` option when running the script.

# Help

```console
./dwd-warning.py -h
Usage: dwd_warning.py -s SERIAL_NUMBER [-v] [-b BROKER_IP] [-p PORT] [-u DWD_URL] [-r REGION_ID] [-h] [-n]
-v: verbose output, default False
-b: MQTT Broker IP, default 127.0.0.1
-n: dry run, no MQTT message sent, default False
-p: MQTT Broker Port, default 1883
-r: DWD region/WARNCELLID, default 112069000
-s: Victron Serial Number (mandatory)
-u: DWD warnings.json URL, default https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json
-h: shows this help
```

# Project Documentation

[IoT Rebell Blog](https://www.sascha-curth.de/projekte/007_VRM_victronenergy_DWD.html)
