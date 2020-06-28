# About
This script is used to set Victron System minimum battery state of charge (MinimumSocLimit) to a higher level if a storm warning for as specific region is published by DWD.

# Installation

```console
pip install -r requirements.txt
```
# Find your Area ID

[Google Earth KML File](https://maps.dwd.de/geoserver/dwd/wms?service=WMS&version=1.1.0&request=GetMap&layers=dwd:Warngebiete_Kreise&styles=&bbox=5.86625035072566,47.2701236047002,15.0418156516163,55.0583836008072&width=768&height=651&srs=EPSG:4326&format=application%2Fvnd.google-earth.kml%2Bxml) 
Each Area details contain a unique WARNCELLID 

# Help

```console
./dwd-warning.py -h
Usage: dwd_warning.py -s XXX [-v] [-b] [-p] [-u] [-r] [-h] [-n]
-v: verbose output, default False
-b: MQTT Broker IP, default 127.0.0.1
-n: dry run, no MQTT message sent
-p: MQTT Broker Port, default 1883
-r: DWD region, default 112069000 = Potsdam-Mittelmark
-s: Victron Serial Number, mandatory, no default
-u: DWD warnings.json url, default https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json
-h: shows this help
```

# Project Documentation

[IoT Rebell Blog](https://www.sascha-curth.de/projekte/007_VRM_victronenergy_DWD.html)
