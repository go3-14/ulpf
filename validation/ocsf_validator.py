def validate_ocsf(event):

    errors = []

    # Required base fields
    required_fields = [
        "class_uid",
        "category_uid",
        "activity_id",
        "severity_id"
    ]

    for field in required_fields:

        if field not in event:
            errors.append(
                f"Missing required field: {field}"
            )


    # Check Authentication class
    if event.get("class_uid") != 3002:

        errors.append(
            "Invalid class_uid for Authentication"
        )


    # Check category
    if event.get("category_uid") != 3:

        errors.append(
            "Invalid category_uid"
        )


    # Check activity
    if event.get("activity_id") != 1:

        errors.append(
            "Invalid activity_id for Logon"
        )


    # Check user
    if "user" not in event:

        errors.append(
            "Missing user object"
        )

    else:

        if not event["user"].get("name"):

            errors.append(
                "Missing user.name"
            )


    # Check source endpoint
    if "src_endpoint" not in event:

        errors.append(
            "Missing src_endpoint"
        )

    else:

        if not event["src_endpoint"].get("ip"):

            errors.append(
                "Missing src_endpoint.ip"
            )


    # Check status
    if "status_id" not in event:

        errors.append(
            "Missing status_id"
        )


    # Result
    if len(errors) == 0:

        return True, []

    return False, errors