processed_total = 0
failed_total = 0


def record_success(fmt, source, elapsed):
    global processed_total
    processed_total += 1


def record_failure(fmt, reason):
    global failed_total
    failed_total += 1
