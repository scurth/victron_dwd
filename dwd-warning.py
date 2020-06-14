#!/usr/bin/env python3

import sys
import getopt
import json
import time
import paho.mqtt.client as mqttClient
import urllib.request, json 

timestamp = int(time.time()) * 1000 
broker = "127.0.0.1"
port = 1883
verbose = False
url = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"
region = "112069000"

def convert(jsonp):
    try:
        l_index = jsonp.index('(') + 1
        r_index = jsonp.rindex(')')
    except ValueError:
        print("Input is not in a jsonp format.")
        return
    
    res = jsonp[l_index:r_index]
    return res

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


#    with open('warnings.jsonp', encoding='utf-8') as fh:
    with urllib.request.urlopen(url) as response:
        source=response.read().decode('utf-8')
        jsondata=convert(source)
        json_obj=json.loads(jsondata)

    minsoc = '{"value": 25}' # Standard Minimum State of Charge - ausser Netzausfall
    if region not in json_obj["warnings"]:
        print("Keine Warnung vorhanden")
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

    pubclient = mqttClient.Client("writer")
    pubclient.on_publish = on_publish                          #assign function to callback
    pubclient.connect(broker, port, 60)

    if (verbose is True):
        print("setting minsoc to ",minsoc)

    ret = pubclient.publish(topic,minsoc)
    pubclient.disconnect()

    if (verbose is True):
        print(ret)

if __name__ == "__main__":
    main()
