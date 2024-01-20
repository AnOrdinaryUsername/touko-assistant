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
        
        location = next(tracker.get_latest_entity_values("location"), 
                        os.environ["DEFAULT_LOCATION"])

        api_key = os.environ["OPENWEATHER_API_KEY"]
        geocoding_base_url = "http://api.openweathermap.org/geo/1.0/direct"
        query = "%20".join(location.split())

        coordinates = (
            f"{geocoding_base_url}"
            f"?q={query}"
            f"&limit=1"
            f"&appid={api_key}"
        )
        coords_response = requests.get(coordinates)
        coords = coords_response.json()
        unable_to_fetch = "Sorry, I can't get the weather at the moment."

        if coords_response.status_code != 200:
            dispatcher.utter_message(text=unable_to_fetch)
            return []

        latitude, longitude = (coords[0]["lat"], coords[0]["lon"])

        base_url = "https://api.openweathermap.org/data/2.5/weather"
        current_weather = (
            f"{base_url}"
            f"?lat={latitude}&lon={longitude}"
            f"&units=imperial"
            f"&appid={api_key}"
        )

        current_weather = requests.get(current_weather)
        current = current_weather.json()

        print(current)

        if current_weather.status_code == 200:
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
                f"The temperature is {temp}°F, with a low of {min_temp}°F "
                f"and a high of {max_temp}°F."
                "\n\n\n"
                f"Cloudiness is at {cloud_percent}%."
                "\n"
                f"Current visibility is {visibility}m."
            )

            dispatcher.utter_message(image=icon_url, text=weather_report)
        else:
            dispatcher.utter_message(text=unable_to_fetch)

        return []
