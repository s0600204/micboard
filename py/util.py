WIRELESS_QUERY_QUEUE_INTERVAL = 10 # seconds

def TVLookup(frequency):
    frequency = float(frequency)
    return int((frequency - 470) / 6 + 14)
