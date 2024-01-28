from typing import Tuple, Any
import requests
import logging

class OpenWeatherMap(object):
    """
    API Link:
    https://openweathermap.org/api
    """
    def __init__(self, api_key: str):
        self._api_key = api_key

    def get_coordinates(self, location: str) -> Tuple[float, float]:
        geocoding_base_url = "https://api.openweathermap.org/geo/1.0/direct"
        query = "%20".join(location.split())

        coordinates = (
            f"{geocoding_base_url}"
            f"?q={query}"
            "&limit=1"
            f"&appid={self._api_key}"
        )

        try:
            response = requests.get(coordinates)
            response.raise_for_status()

            logging.debug(f"Time elapsed: {response.elapsed}")

            coords = response.json()
        except requests.exceptions.HTTPError as http_error:
            raise http_error from None
        except requests.RequestException as error:
            raise error from None

        return coords
    
    def get_current_weather(self, location: str) -> Any:
        try:
            coords = self.get_coordinates(location)
        except requests.RequestException as error:
            raise error from None

        latitude, longitude = (coords[0]["lat"], coords[0]["lon"])

        base_url = "https://api.openweathermap.org/data/2.5/weather"
        current_weather = (
            f"{base_url}"
            f"?lat={latitude}&lon={longitude}"
            "&units=imperial"   
            f"&appid={self._api_key}"
        )

        try:
            response = requests.get(current_weather)
            response.raise_for_status()
            
            logging.debug(f"Time elapsed: {response.elapsed}")

            current_weather = response.json()
        except requests.exceptions.HTTPError as http_error:
            raise http_error from None
        except requests.RequestException as error:
            raise error from None

        return current_weather

    