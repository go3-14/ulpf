def to_ocsf(event):

    # Authentication Failure
    if event.event_type == "authentication_failure":

        return {
            "class_uid": 3002,
            "class_name": "Authentication",

            "category_uid": 3,
            "category_name": "Identity & Access Management",

            "activity_id": 1,
            "activity_name": "Logon",

            "severity_id": 3,
            "severity": "Medium",

            "time": event.timestamp,

            "user": {
                "name": event.username,
                "type_id": 1,
                "type": "User"
            },

            "src_endpoint": {
                "ip": event.source_ip
            },

            "status_id": 2,
            "status": "Failure",

            "message": "Authentication failure"
        }


    # Authentication Success
    elif event.event_type == "authentication_success":

        return {
            "class_uid": 3002,
            "class_name": "Authentication",

            "category_uid": 3,
            "category_name": "Identity & Access Management",

            "activity_id": 1,
            "activity_name": "Logon",

            "severity_id": 1,
            "severity": "Informational",

            "time": event.timestamp,

            "user": {
                "name": event.username,
                "type_id": 1,
                "type": "User"
            },

            "src_endpoint": {
                "ip": event.source_ip
            },

            "status_id": 1,
            "status": "Success",

            "message": "Authentication successful"
        }


    # Unknown event
    else:

        return {
            "error": "No OCSF mapping available",
            "event_type": event.event_type
        }