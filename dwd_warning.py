#!/usr/bin/env python3

import sys
import getopt
import json
import time
import paho.mqtt.client as mqttClient
import urllib.request

TIMESTAMP = int(time.time()) * 1000
BROKER = "127.0.0.1"
PORT = 1883
VERBOSE = False
DRYRUN = False
URL = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"
REGION = "112069000"

def convert(jsonp):
    try:
        l_index = jsonp.index('(') + 1
        r_index = jsonp.rindex(')')
    except ValueError:
        print("Input is not in a jsonp format.")
        return

    res = jsonp[l_index:r_index]
    return res

def on_publish(client, userdata, result):             #create function for callback
    if VERBOSE is True:
        print("data published \n", result)

def usage():
    print("Usage: dwd_warning.py -s XXX [-v] [-b] [-p] [-u] [-r] [-h] [-n]")
    print("-v: VERBOSE output, default False")
    print("-b: MQTT Broker IP, default 127.0.0.1")
    print("-n: dry run, no MQTT message sent")
    print("-p: MQTT Broker Port, default 1883")
    print("-r: DWD region, default 112069000 = Potsdam-Mittelmark")
    print("-s: Victron Serial Number, mandatory, no default")
    print("-u: DWD warnings.json URL, default https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json")
    print("-h: shows this help")

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        options, prog_argv = getopt.getopt(
            argv[1:],
            "hnb:p:r:s:u:v",
            ["help", "broker=", "dry-run", "PORT=", "region=", "SERIAL=", "URL=", "VERBOSE"]
        )
    except getopt.GetoptError:
        sys.exit(1)

    for name, value in options:
        if name == "-v":
            global VERBOSE
            VERBOSE = True
        elif name in ("-h", "--help"):
            usage()
            sys.exit()
        elif name in ("-b", "--broker"):
            global BROKER
            BROKER = value
        elif name in ("-n", "--dry-run"):
            global DRYRUN
            DRYRUN = True
        elif name in ("-u", "--URL"):
            global URL
            URL = value
        elif name in ("-p", "--PORT"):
            global PORT
            PORT = value
        elif name in ("-r", "--region"):
            global REGION
            REGION = value
        elif name in ("-s", "--SERIAL"):
            global SERIAL
            SERIAL = value
            if VERBOSE is True:
                print(SERIAL)
        else:
            assert False, "unhandled option"
            usage
            sys.exit()
    try:
        topic = 'W/' + SERIAL + '/settings/0/Settings/CGwacs/BatteryLife/MinimumSocLimit'
    except NameError:
        print("Serial Number not set, use option -s")
        usage()
        sys.exit()

    if VERBOSE is True:
        print("Using broker: ", BROKER, "  at PORT: ", PORT)
        print("Using DWD URL:", URL, "and Region: ", REGION)
        print("Topic: ", topic)


#    with open('warnings.jsonp', encoding='utf-8') as fh:
    with urllib.request.urlopen(URL) as response:
        source = response.read().decode('utf-8')
        jsondata = convert(source)
        json_obj = json.loads(jsondata)

    minsoc = '{"value": 25}' # Standard Minimum State of Charge - ausser Netzausfall
    if REGION not in json_obj["warnings"]:
        print("Keine Warnung vorhanden")
    else:
        myregion = json_obj["warnings"][REGION]

        if myregion[0]["type"] in [0, 2] and myregion[0]["level"] in [4, 5]:
            print("Alert Level ", myregion[0]["level"])
            print("Start => ", myregion[0]["start"])
            print("End => ", myregion[0]["end"])

            alert_end_plus_buffer = myregion[0]["end"] + 2 * 60 * 60 * 1000
            alert_start_minus_buffer = myregion[0]["start"] - 2 * 60 * 60 * 1000

            if alert_end_plus_buffer > TIMESTAMP or alert_start_minus_buffer > TIMESTAMP:
                print("Setting SOC to 50%")
                minsoc = '{"value": 50}'

    pubclient = mqttClient.Client("writer")
    pubclient.on_publish = on_publish                          #assign function to callback
    pubclient.connect(BROKER, PORT, 60)

    if VERBOSE is True:
        print("setting minsoc to ", minsoc)

    if DRYRUN is True:
        print("MQTT Broker: ", BROKER, " at PORT ", PORT)
        print("Topic: ", topic)
        print("Message: ", minsoc)
    else:
        ret = pubclient.publish(topic, minsoc)
        pubclient.disconnect()

        if VERBOSE is True:
            print(ret)

if __name__ == "__main__":
    main()
