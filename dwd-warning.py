#!/usr/bin/env python3

import sys
import json
import time
import paho.mqtt.client as mqttClient
import urllib.request, json 

broker_address= "192.168.0.201"
#broker_address= "127.0.0.1"
port = 1883

timestamp = int(time.time()) * 1000 

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
    print("data published \n", result)
    pass

def main():
#    with open('warnings.jsonp', encoding='utf-8') as fh:
    with urllib.request.urlopen("https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json") as response:
        source=response.read().decode('utf-8')
        jsondata=convert(source)
        json_obj=json.loads(jsondata)

    minsoc = '{"value": 30}' # Standard Minimum State of Charge - ausser Netzausfall
    if "112069000" not in json_obj["warnings"]:
        print("Keine Warnung vorhanden")
    else:
        myregion=json_obj["warnings"]["112069000"]

        if myregion[0]["level"] in [3, 4, 5]:
            print("Alert Level ",myregion[0]["level"])
            print("Start => ",myregion[0]["start"])
            print("End => " , myregion[0]["end"])
        
            alert_end_plus_buffer=myregion[0]["end"] + 2 * 60 * 60 * 1000

            if alert_end_plus_buffer > timestamp:
                print ("Setting SOC to 50%")
                minsoc = '{"value": 50}'

    pubclient = mqttClient.Client("writer")
    pubclient.on_publish = on_publish                          #assign function to callback
    pubclient.connect(broker_address, port, 60)

    print("setting minsoc to ",minsoc)
    ret = pubclient.publish('W/<placeholder>/settings/0/Settings/CGwacs/BatteryLife/MinimumSocLimit',minsoc)
    pubclient.disconnect()

    print(ret)

#    print("alertbuff", alert_end_plus_buffer)
#    print(json_obj["warnings"]["112069000"])
    
if __name__ == "__main__":
    main()
