#!/usr/bin/env python3

import sys
import getopt
import json
import time
import paho.mqtt.client as mqttClient
# Assuming dwd_utils.py is in the same directory or Python path
from dwd_utils import fetch_dwd_warnings # convert is not directly used by dwd_warning.py anymore

# --- Constants ---
DEFAULT_DWD_URL = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"
DEFAULT_REGION = "112069000" # Potsdam-Mittelmark
DEFAULT_MQTT_BROKER_IP = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883

DEFAULT_MINSOC_PAYLOAD = '{"value": 25}'
ALERT_MINSOC_PAYLOAD = '{"value": 50}'

# Alert criteria (can be moved to config or kept as constants if not user-configurable)
ALERT_LEVELS = [4, 5] # Levels that trigger action
ALERT_TYPES = [0, 2]  # Types that trigger action (e.g., actual warning, update to warning)
ALERT_BUFFER_MS = 2 * 60 * 60 * 1000 # 2 hours in milliseconds

def usage():
    # (usage function remains largely the same, but ensure it reflects any arg changes if any)
    print("Usage: dwd_warning.py -s SERIAL_NUMBER [-v] [-b BROKER_IP] [-p PORT] [-u DWD_URL] [-r REGION_ID] [-h] [-n]")
    print(f"-v: verbose output, default False")
    print(f"-b: MQTT Broker IP, default {DEFAULT_MQTT_BROKER_IP}")
    print(f"-n: dry run, no MQTT message sent, default False")
    print(f"-p: MQTT Broker Port, default {DEFAULT_MQTT_PORT}")
    print(f"-r: DWD region/WARNCELLID, default {DEFAULT_REGION}")
    print(f"-s: Victron Serial Number (mandatory)")
    print(f"-u: DWD warnings.json URL, default {DEFAULT_DWD_URL}")
    print(f"-h: shows this help")

def parse_arguments(argv):
    config = {
        "broker_ip": DEFAULT_MQTT_BROKER_IP,
        "broker_port": DEFAULT_MQTT_PORT,
        "dwd_url": DEFAULT_DWD_URL,
        "region_id": DEFAULT_REGION,
        "serial_number": None,
        "verbose": False,
        "dry_run": False,
    }

    try:
        options, _ = getopt.getopt(
            argv,
            "hnb:p:r:s:u:v",
            ["help", "dry-run", "broker=", "port=", "region=", "serial=", "url=", "verbose"]
        )
    except getopt.GetoptError as e:
        print(f"Error parsing options: {e}", file=sys.stderr)
        usage()
        sys.exit(2)

    for name, value in options:
        if name == "-v" or name == "--verbose":
            config["verbose"] = True
        elif name in ("-h", "--help"):
            usage()
            sys.exit()
        elif name in ("-b", "--broker"):
            config["broker_ip"] = value
        elif name in ("-n", "--dry-run"):
            config["dry_run"] = True
        elif name in ("-u", "--url"):
            config["dwd_url"] = value
        elif name in ("-p", "--port"):
            try:
                config["broker_port"] = int(value)
            except ValueError:
                print(f"Error: Port must be an integer. Got: {value}", file=sys.stderr)
                sys.exit(2)
        elif name in ("-r", "--region"):
            config["region_id"] = value
        elif name in ("-s", "--serial"):
            config["serial_number"] = value
    
    if config["serial_number"] is None:
        print("Error: Victron Serial Number (-s) is mandatory.", file=sys.stderr)
        usage()
        sys.exit(2)
        
    return config

def determine_minsoc(warning_data, region_id, current_timestamp, verbose_output=False):
    if warning_data is None:
        if verbose_output:
            print("No warning data received from DWD or data was invalid.")
        return DEFAULT_MINSOC_PAYLOAD

    warnings_for_region = warning_data.get("warnings", {}).get(region_id)

    if not warnings_for_region:
        if verbose_output:
            print(f"No specific warning found for region {region_id} in the fetched data.")
        return DEFAULT_MINSOC_PAYLOAD

    # Assuming the first warning in the list is the most relevant one
    # (as per original script's logic: myregion[0])
    latest_warning = warnings_for_region[0]

    warn_type = latest_warning.get("type")
    warn_level = latest_warning.get("level")
    warn_start_ms = latest_warning.get("start")
    warn_end_ms = latest_warning.get("end")

    if verbose_output:
        print(f"Processing warning for region {region_id}: Level={warn_level}, Type={warn_type}, Start={warn_start_ms}, End={warn_end_ms}")

    if (warn_type in ALERT_TYPES and
            warn_level in ALERT_LEVELS and
            warn_start_ms is not None and warn_end_ms is not None):
        
        effective_start_ms = warn_start_ms - ALERT_BUFFER_MS
        effective_end_ms = warn_end_ms + ALERT_BUFFER_MS

        # Logic from original script: alert if current time is within buffered window OR buffered start is in future
        # This simplifies to: if the effective end of the warning (including buffer) is after the current time.
        if effective_end_ms > current_timestamp:
            if verbose_output:
                print(f"Alert conditions met for region {region_id}. Setting MinSoc to alert level.")
            return ALERT_MINSOC_PAYLOAD
        else:
            if verbose_output:
                print(f"Warning for region {region_id} is active but its effective end time has passed.")
    else:
        if verbose_output:
            print(f"Warning for region {region_id} (Level: {warn_level}, Type: {warn_type}) does not meet criteria for action.")
            
    return DEFAULT_MINSOC_PAYLOAD

def on_mqtt_publish(client, userdata, result):
    # This callback can be enhanced if verbose is passed or a logger is used.
    # For now, keeping it simple as it's mostly for QoS > 0, and default is 0.
    # print(f"MQTT data published with result: {result}") # Example if needed
    pass

def publish_minsoc_to_mqtt(config, topic, minsoc_payload):
    if config["verbose"]:
        print(f"Preparing to publish to MQTT. Dry run: {config['dry_run']}")
        print(f"Broker: {config['broker_ip']}:{config['broker_port']}")
        print(f"Topic: {topic}")
        print(f"Payload: {minsoc_payload}")

    if config["dry_run"]:
        print("Dry run: MQTT message not sent.")
        return True # Indicate success for dry run

    try:
        # Corrected client ID to be a simple string as required by Paho MQTT
        pubclient = mqttClient.Client("dwd_victron_minsoc_setter") 
        pubclient.on_publish = on_mqtt_publish
        pubclient.connect(config["broker_ip"], config["broker_port"], 60)
        
        ret = pubclient.publish(topic, minsoc_payload)
        # pubclient.loop() # loop() is blocking. Use loop_start() and loop_stop() for background thread
                         # or rely on publish() for QoS 0 which is mostly fire-and-forget.
                         # For simple QoS 0, checking ret.rc is often sufficient.
                         # Let's ensure loop is used correctly if needed or rely on ret.rc for now.
                         # The original script didn't have a loop here.
                         # For QoS 0, the message is sent immediately by publish() if the connection is up.

        if ret.rc != mqttClient.MQTT_ERR_SUCCESS:
            print(f"Failed to publish MQTT message. Return code: {ret.rc}", file=sys.stderr)
            # pubclient.disconnect() # Disconnect might not be necessary if connect failed or publish failed severely
            return False
        
        if config["verbose"]:
            print(f"MQTT message published successfully (rc: {ret.rc}). Mid: {ret.mid}") # mid is message id
            
        pubclient.disconnect()
        return True
    except ConnectionRefusedError:
        print(f"MQTT connection refused by broker {config['broker_ip']}:{config['broker_port']}. Check broker status and configuration.", file=sys.stderr)
        return False
    except TimeoutError: # Python's built-in TimeoutError
        print(f"MQTT connection timed out to broker {config['broker_ip']}:{config['broker_port']}.", file=sys.stderr)
        return False
    except mqttClient.WebsocketConnectionError as e: # if using websockets, though not by default
        print(f"MQTT Websocket connection error: {e}", file=sys.stderr)
        return False
    except OSError as e: # Catches socket errors like "Network is unreachable"
        print(f"MQTT OS error (e.g., network issue): {e}", file=sys.stderr)
        return False
    except Exception as e: # Catch other potential errors during connect/publish
        print(f"MQTT publishing error: {e}", file=sys.stderr)
        return False

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    config = parse_arguments(argv)

    if config["verbose"]:
        print("Configuration loaded:")
        for key, value in config.items():
            print(f"  {key}: {value}")

    # Fetch DWD warnings
    # The fetch_dwd_warnings function in dwd_utils now prints its own verbose/error messages.
    warning_data = fetch_dwd_warnings(config["dwd_url"]) # Pass URL from config

    # Determine MinSoc
    current_timestamp = int(time.time()) * 1000
    minsoc_payload = determine_minsoc(warning_data, config["region_id"], current_timestamp, config["verbose"])

    if config["verbose"]:
        print(f"Determined MinSoc payload: {minsoc_payload}")

    # Publish to MQTT
    mqtt_topic = f"W/{config['serial_number']}/settings/0/Settings/CGwacs/BatteryLife/MinimumSocLimit"
    
    success = publish_minsoc_to_mqtt(config, mqtt_topic, minsoc_payload)

    if not success and not config["dry_run"]:
        sys.exit(1) # Exit with error if MQTT publishing failed (and not a dry run)
    elif config["verbose"]:
        print("Script finished.")

if __name__ == "__main__":
    main()
