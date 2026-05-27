import os
from datetime import datetime
import pytz
import re
from uuid import UUID


def local_now():
    """datetime.datetime.now of local timezone

    Returns:
        datetime.datetime:
    """
    timezone = os.environ.get('TIMEZONE', 'America/Bogota')
    now = datetime.now(pytz.timezone(
        timezone
    ))
    return datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=now.second,
        microsecond=now.microsecond
    )


def replace_env_variables(text):
    # find patterns like ${VAR_NAME}
    pattern = r'\$\{(\w+)\}'

    # Replace each match with the value from the environment
    def replace_match(match):
        var_name = match.group(1)
        return os.getenv(var_name, '')

    # Substitute the variables in the text
    return re.sub(pattern, replace_match, text)


def string_to_uuid(value: str) -> UUID:
    """
    Converts a string to a UUID.

    :param value: The string to be converted to a UUID.
    :return: A UUID object.
    :raises ValueError: If the string is not a valid UUID.
    """
    try:
        return UUID(value)
    except ValueError:
        raise ValueError(f"Invalid UUID string: {value}")
