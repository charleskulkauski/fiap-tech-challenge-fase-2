def convert_hours_to_minutes(hour_str):
    try:
        hours, minutes = map(int, hour_str.lower().split(':'))
        return hours * 60 + minutes
    except ValueError:
        raise ValueError("Invalid time format. Expected 'HHhMM'.")
    