def classify_event(event):

    event_name = (event.event_type or "").lower()

    if event_name in [
        "login_failed",
        "authentication_failure",
        "auth_failure",
        "login_denied"
    ]:
        return "authentication_failure"

    if event_name in [
        "login_success",
        "authentication_success",
        "auth_success"
    ]:
        return "authentication_success"

    return "unknown"