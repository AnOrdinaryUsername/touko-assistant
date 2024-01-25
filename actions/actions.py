# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from jokeapi import Jokes
from jokeapi.main import CategoryError
import asyncio

class ActionTellJoke(Action):

    def name(self) -> Text:
        return "action_tell_joke"

    async def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        category = next(tracker.get_latest_entity_values("joke_category"), 'Any')
        j = await Jokes()

        print(category)

        try:
            joke = await j.get_joke(category=[category], safe_mode=True)
        except CategoryError:
            error = (
                        f"Sorry, but '{category}' isn't a category I recognize. "
                        "The available categories are Any, Misc, Programming, "
                        "Pun, Spooky, and Christmas."
                    )
            
            dispatcher.utter_message(text=error)
            return []
        

        has_error = joke.get('error')

        if has_error:
            dispatcher.utter_message(text="Apologies, but I can't fulfill that request.")
            return []
        

        if joke["type"] == "single":
            dispatcher.utter_message(text=joke["joke"])
        else:
            dispatcher.utter_message(text=joke["setup"])
            dispatcher.utter_message(text=joke["delivery"])

        return []

import os
import requests
import math
from dotenv import load_dotenv
from actions.api.open_weather import OpenWeatherMap

load_dotenv()

class ActionSayWeather(Action):

    def name(self) -> Text:
        return "action_say_weather"

    def round_float(self, x: float) -> int:
        frac = x - math.floor(x)
        if frac < 0.5: 
            return math.floor(x)
        
        return math.ceil(x)

    def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:
        
        location = next(tracker.get_latest_entity_values("GPE"), 
                        os.environ["DEFAULT_LOCATION"])

        api_key = os.environ["OPENWEATHER_API_KEY"]
        weather_api = OpenWeatherMap(api_key)

        try:
            current = weather_api.get_current_weather(location)
        except IndexError:
            bad_location = f"Are your sure '{location}' exists? It's not fetching any results."
            dispatcher.utter_message(text=bad_location)
            return []
        except requests.RequestException:
            unable_to_fetch = "Sorry, I can't get the weather at the moment."
            dispatcher.utter_message(text=unable_to_fetch)
            return []

        icon = current["weather"][0]["icon"]
        place = current["name"]
        description = current["weather"][0]["description"]

        temp = self.round_float(current["main"]["temp"])
        min_temp = self.round_float(current["main"]["temp_min"])
        max_temp = self.round_float(current["main"]["temp_max"])

        cloud_percent = current["clouds"]["all"]
        visibility = current["visibility"]

        icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"

        weather_report = (
            f"{place} is currently experiencing {description}. "
            f"Right now, the temperature is {temp}°F, "
            f"with a low of {min_temp}°F and a high of {max_temp}°F."
            "\n\n\n"
            f"Cloudiness is at {cloud_percent}%."
            "\n"
            f"Current visibility is {visibility}m."
        )

        dispatcher.utter_message(image=icon_url, text=weather_report)

        return []

from actions.api.time import TimeAPI

class ActionGetTime(Action):

    def name(self) -> Text:
        return "action_get_time"

    async def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:
        
        location = next(tracker.get_latest_entity_values("GPE"), 
                        os.environ["DEFAULT_LOCATION"])

        api_key = os.environ["OPENWEATHER_API_KEY"]
        weather_api = OpenWeatherMap(api_key)

        try:
            location_coords = weather_api.get_coordinates(location)
            lat, lon = (location_coords[0]["lat"], location_coords[0]["lon"])
            coords = (lat, lon)
        except IndexError:
            bad_location = f"Are your sure '{location}' exists? It's not fetching any results."
            dispatcher.utter_message(text=bad_location)
            return []
        except requests.RequestException:
            unable_to_fetch = "Sorry, I can't get the geographic coordinates at the moment."
            dispatcher.utter_message(text=unable_to_fetch)
            return []
        
        time_api = TimeAPI()
        time = time_api.get_time(coords)

        date = time["date"]
        day_of_week = time["dayOfWeek"]
        twelver_hour_format = time_api.get_twelve_hour_clock(coords)

        message = (
            f"Right now in {location}, it's {day_of_week} ({date}), {twelver_hour_format}."
        )

        dispatcher.utter_message(text=message)
        return []
    
class ActionTellDayState(Action):

    def name(self) -> Text:
        return "action_tell_day_state"

    async def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        location = next(tracker.get_latest_entity_values("GPE"), 
                        os.environ["DEFAULT_LOCATION"])
        
        is_daytime = next(tracker.get_latest_entity_values("is_daytime"), None)

        if not is_daytime:
            return []
        
        api_key = os.environ["OPENWEATHER_API_KEY"]
        weather_api = OpenWeatherMap(api_key)
        
        try:
            # Current weather gives us access to sunrise and sunset
            current = weather_api.get_current_weather(location)
        except IndexError:
            bad_location = f"Are your sure '{location}' exists? It's not fetching any results."
            dispatcher.utter_message(text=bad_location)
            return []
        except requests.RequestException:
            unable_to_fetch = "Sorry, I can't get the weather at the moment."
            dispatcher.utter_message(text=unable_to_fetch)
            return []
        
        timezone_offset = current["timezone"]
        coords = (current["coord"]["lat"], current["coord"]["lon"])

        sunset = current["sys"]["sunset"] + timezone_offset
        sunrise = current["sys"]["sunrise"] + timezone_offset

        location_time = TimeAPI().get_unix_time(coords)

        print(
                f"Sunset: {sunset}\n"
                f"Sunrise: {sunrise}\n"
                f"location: {location_time}\n"
            )
        
        if location_time >= sunrise and location_time <= sunset:
            dispatcher.utter_message(text="As of right now, it is daytime in that area.")
        else:
            dispatcher.utter_message(text="It's nighttime as of the moment.")

        return []