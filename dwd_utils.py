import json
import urllib.request

def convert(jsonp_text: str):
    """Converts a JSONP string to a JSON string by stripping the function call wrapper."""
    if not isinstance(jsonp_text, str):
        print("Error: Input to convert must be a string.")
        return None
    try:
        l_index = jsonp_text.index('(') + 1
        r_index = jsonp_text.rindex(')')
        return jsonp_text[l_index:r_index]
    except ValueError:
        print("Error: Input is not in a valid JSONP format (missing '(' or ')').")
        return None

def fetch_dwd_warnings(dwd_url: str):
    """
    Fetches warning data from the DWD JSONP URL, converts it to JSON, and parses it.
    Returns the parsed JSON object (typically a dict) or None on error.
    """
    print(f"Fetching DWD warnings from: {dwd_url}") # Added for verbosity, can be conditional later
    try:
        with urllib.request.urlopen(dwd_url) as response:
            source_bytes = response.read()
    except urllib.error.URLError as e:
        print(f"Error fetching DWD data (URLError): {e.reason}")
        return None
    except urllib.error.HTTPError as e:
        print(f"Error fetching DWD data (HTTPError): {e.code} {e.reason}")
        return None
    except Exception as e: # Catch any other potential errors during urlopen/read
        print(f"An unexpected error occurred during data fetch: {e}")
        return None

    try:
        source_str = source_bytes.decode('utf-8')
    except UnicodeDecodeError as e:
        print(f"Error decoding DWD data: {e}")
        return None

    json_data_str = convert(source_str)
    if json_data_str is None:
        # Error message already printed by convert()
        return None

    try:
        json_obj = json.loads(json_data_str)
        return json_obj
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e.msg} at line {e.lineno} column {e.colno}")
        return None
