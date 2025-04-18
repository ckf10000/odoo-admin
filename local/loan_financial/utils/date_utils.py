def compute_timestamp_duration(start_date: int, end_date: int):
    """
    Compute the  duration between two timestamp.
    """
    mins = round((end_date - start_date) / 60, 2)

    if mins < 60:
        return mins, 'min'
    else:
        hours = round(mins / 60, 2)
        return hours, 'hour'