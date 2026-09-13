import json
import xml.etree.ElementTree as ET

from parsers import json_parser
from parsers import csv_parser
from parsers import xml_parser

from classification.classifier import classify_event
from mapping.ocsf_mapper import to_ocsf
from validation.ocsf_validator import validate_ocsf

# Later:
# from mapping.ocsf_mapper import to_ocsf


# ============================================================
# FORMAT DETECTION
# ============================================================

def detect_format(log):

    log = log.strip()

    # JSON
    if log.startswith("{") or log.startswith("["):
        try:
            json.loads(log)
            return "json"
        except json.JSONDecodeError:
            pass

    # XML
    if log.startswith("<"):
        try:
            ET.fromstring(log)
            return "xml"
        except ET.ParseError:
            pass

    # CSV
    if "," in log:
        return "csv"

    return "unknown"


# ============================================================
# MAIN PIPELINE
# ============================================================

def process_log(log):

    # 1. Detect format
    format_type = detect_format(log)

    print("Detected format:", format_type)

    if format_type == "unknown":
        print("Unknown log format")
        return None

    # 2. Send to appropriate parser
    if format_type == "json":
        event = json_parser.parse(log)

    elif format_type == "csv":
        event = csv_parser.parse(log)

    elif format_type == "xml":
        event = xml_parser.parse(log)

    # 3. Semantic classification
    event.event_type = classify_event(event)

    # 4. Display normalized/classified event
    print("\nNormalized Event:")
    print(event.to_dict())

    ocsf_event = to_ocsf(event)

    print("\nOCSF Event:")
    print(ocsf_event)

    # Validate
    valid, errors = validate_ocsf(ocsf_event)

    print("\n========== OCSF VALIDATION ==========")

    if valid:
        print("Status: VALID")

    else:
        print("Status: INVALID")

        for error in errors:
            print(" -", error)

    return ocsf_event


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # JSON
    json_log = '''
    {
        "timestamp": "2026-09-13T19:30:21Z",
        "event": "login_failed",
        "user": "admin",
        "src_ip": "10.0.0.5",
        "action": "login",
        "status": "failed"
    }
    '''

    # CSV
    csv_log = '''timestamp,event,user,src_ip,dst_ip,action,status
2026-09-13T19:30:21Z,login_failed,admin,10.0.0.5,,login,failed
'''

    # XML
    xml_log = '''
    <event>
        <timestamp>2026-09-13T19:30:21Z</timestamp>
        <type>login_failed</type>
        <user>admin</user>
        <src_ip>10.0.0.5</src_ip>
        <action>login</action>
        <status>failed</status>
    </event>
    '''

    print("\n========== JSON ==========")
    process_log(json_log)

    print("\n========== CSV ==========")
    process_log(csv_log)

    print("\n========== XML ==========")
    process_log(xml_log)