class NormalizedEvent:

    def __init__(
        self,
        event_type=None,
        timestamp=None,
        username=None,
        source_ip=None,
        destination_ip=None,
        source_port=None,
        destination_port=None,
        action=None,
        status=None,
        raw_data=None
    ):
        self.event_type = event_type
        self.timestamp = timestamp
        self.username = username
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.source_port = source_port
        self.destination_port = destination_port
        self.action = action
        self.status = status
        self.raw_data = raw_data

    def to_dict(self):

        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "username": self.username,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "action": self.action,
            "status": self.status
        }