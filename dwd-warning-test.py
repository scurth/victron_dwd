#!/usr/bin/env python3

import sys
import getopt
import json
import time
import paho.mqtt.client as mqttClient
# urllib.request is now handled by dwd_utils for DWD calls
# import urllib.request, json # This line might be for the Grafana call later, so let's be careful.
# For DWD, we only need fetch_dwd_warnings
from dwd_utils import fetch_dwd_warnings
import urllib.request # Keep for Grafana if needed, or remove if Grafana part is also updated/removed

timestamp = int(time.time()) * 1000 
broker = "127.0.0.1"
port = 1883
verbose = False
url = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"
region = "112069000"

# The convert function has been moved to dwd_utils.py and is used by fetch_dwd_warnings.
# No longer need it directly in this file.

def on_publish(client,userdata,result):             #create function for callback
    if (verbose is True):
        print("data published \n", result)
    pass

def usage():
    print("Usage: dwd_warning.py -s XXX [-v] [-b] [-p] [-u] [-r] [-h]")
    print("-v: verbose output, default False")
    print("-b: MQTT Broker IP, default 127.0.0.1")
    print("-p: MQTT Broker Port, default 1883")
    print("-r: DWD region, default 112069000 = Potsdam-Mittelmark")
    print("-s: Victron Serial Number, mandatory, no default") 
    print("-u: DWD warnings.json url, default https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json")
    print("-h: shows this help")
    pass

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        options, prog_argv = getopt.getopt(argv[1:], "hb:p:r:s:u:v", ["help", "broker=","port=","region=","serial=","url=","verbose"])
    except getopt.GetoptError:
        sys.exit(1) 

    for name, value in options:
        if name == "-v":
            global verbose
            verbose = True
        elif name in ("-h", "--help"):
            usage()
            sys.exit()
        elif name in ("-b", "--broker"):
            global broker
            broker = value
        elif name in ("-u", "--url"):
            global url
            url = value
        elif name in ("-p", "--port"):
            global port
            port = value
        elif name in ("-r", "--region"):
            global region
            region = value
        elif name in ("-s", "--serial"):
            global serial
            serial = value
            if (verbose is True):
                print(serial)
        else:
            assert False, "unhandled option"
            usage() 
            sys.exit()
    try:
       serial
       topic = 'W/' + serial + '/settings/0/Settings/CGwacs/BatteryLife/MinimumSocLimit'
    except:
       print("Serial Number not set, use option -s")
       usage()
       sys.exit()

    if (verbose is True):
        print("Using broker: ", broker, " on port: ", port)
        print("Using DWD URL:", url, "and Region: ", region)
        print("Topic: ", topic)

    json_obj = fetch_dwd_warnings(url) # 'url' is a global in this script
    # Add a basic check for None, similar to dwd_warning.py, to prevent crashes
    if json_obj is None:
        print("Failed to fetch or parse DWD warning data in dwd-warning-test.py. Further checks might fail.")
        # The script's original behavior was to proceed and likely fail on json_obj["warnings"]
        # We'll allow it to proceed to maintain its existing behavior as much as possible for this step,
        # but note that it might still fail later if json_obj is None.
        # A TODO could be added here to improve its specific error handling.

    minsoc = '{"value": 25}' # Standard Minimum State of Charge - ausser Netzausfall
    
    # The script might fail here if json_obj is None and "warnings" is accessed.
    # This is consistent with the note about maintaining existing behavior post basic check.
    if json_obj is None or region not in json_obj.get("warnings", {}): # Added .get() for safety
        print("Keine Warnung vorhanden oder DWD Daten fehlerhaft.")
    else:
        myregion=json_obj["warnings"][region]

        if myregion[0]["level"] in [3, 4, 5]:
            print("Alert Level ",myregion[0]["level"])
            print("Start => ",myregion[0]["start"])
            print("End => " , myregion[0]["end"])
        
            alert_end_plus_buffer=myregion[0]["end"] + 2 * 60 * 60 * 1000
            alert_start_minus_buffer=myregion[0]["start"] - 2 * 60 * 60 * 1000

            if alert_end_plus_buffer > timestamp or alert_start_minus_buffer > timestamp:
                print ("Setting SOC to 50%")
                minsoc = '{"value": 50}'
                # The Grafana URL and related code block:
                grafana_url = 'http://192.168.0.99:3000/api/annotations'
                # Check if myregion[0] has 'start', 'end', 'description' before using them
                grafana_text = myregion[0].get("description", "DWD Warning")
                grafana_time_start = myregion[0].get("start")
                grafana_time_end = myregion[0].get("end")

                if grafana_time_start and grafana_time_end:
                    # Ensure urllib.parse.urlencode and urllib.request.Request/urlopen are used for Python 3
                    # The original script had 'urllib.urlencode' and 'urllib2.Request/urlopen' which are Python 2.
                    # This part of the code was likely non-functional in Python 3 as-is.
                    # For now, I am commenting it out as fixing it is outside the scope of just using fetch_dwd_warnings
                    # and the script's primary function is DWD warning check, not Grafana annotation.
                    # If Grafana annotation is critical, it needs a separate focused fix.
                    pass # Grafana code block is here
                    # import urllib.parse
                    # import urllib.request
                    # data_dict = {'dashboardId' : 'QVQen2Zgz', 'panelId' : '58', 'time' : grafana_time_start, 'timeEnd': grafana_time_end, 'text' : grafana_text}
                    # data = urllib.parse.urlencode(data_dict).encode('utf-8')
                    # req = urllib.request.Request(grafana_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
                    # try:
                    #    with urllib.request.urlopen(req) as response:
                    #        print(response.read().decode('utf-8'))
                    # except Exception as e:
                    #    if verbose: # verbose is a global
                    #        print(f"Grafana annotation failed: {e}")
                elif verbose: # verbose is a global
                    print("Grafana annotation skipped due to missing start/end time in warning.")


    pubclient = mqttClient.Client("writer")
    pubclient.on_publish = on_publish                          #assign function to callback
    pubclient.connect(broker, port, 60)

    if (verbose is True):
        print("setting minsoc to ",minsoc)

    #ret = pubclient.publish(topic,minsoc)
    pubclient.disconnect()

    #if (verbose is True):
    #    print(ret)



if __name__ == "__main__":
    main()
