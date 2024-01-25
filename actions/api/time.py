from typing import Tuple
from datetime import datetime, timezone
from time import mktime
import requests

class TimeAPI(object):
    """
    API Link:
    https://timeapi.io/
    """
    def __init__(self):
        self.data = None

    def get_time(self, coords: Tuple[float, float]) -> any:
        base_url = "https://timeapi.io/api/Time/current/coordinate"
        current_time = (
            f"{base_url}"
            f"?latitude={coords[0]}&longitude={coords[1]}"
        )

        try:
            response = requests.get(current_time)
            response.raise_for_status()
            time = response.json()
        except requests.exceptions.HTTPError as http_error:
            raise http_error from None
        except requests.RequestException as error:
            raise error from None
        
        self.data = time

        return time
    
    def get_unix_time(self, coords: Tuple[float, float]) -> str:
        if not self.data:
            self.get_time(coords)

        date_time = " ".join(self.data["dateTime"].split("T"))
        parsed_time = datetime.strptime(date_time[:-1], '%Y-%m-%d %H:%M:%S.%f')
        parsed_time = parsed_time.replace(tzinfo=timezone.utc)

        unix_time = int(parsed_time.timestamp())

        return unix_time

    def get_twelve_hour_clock(self, coords: Tuple[float, float]) -> str:
        if not self.data:
            self.get_time(coords)

        """
        From the Time API, under GET /api/Time/current/coordinate.
        The dateTime is structured as follows:

        dateTime: "2024-01-24T11:27:22.5910482"

        The microseconds (5910482) has 7 digits of precision. Python's
        datetime library's functions strftime()/strptime() only supports up
        to 6 digits in %f.

        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

        We remove the last 5 digits (but it could have been 1) so that strptime() can work.
        """

        date_time = " ".join(self.data["dateTime"].split("T"))
        parsed_time = datetime.strptime(date_time[:-5], '%Y-%m-%d %H:%M:%S.%f')

        twelver_hour_format = parsed_time.strftime('%I:%M %p')

        return twelver_hour_format
