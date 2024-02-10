# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import ActionExecuted, SlotSet

class ActionSessionStart(Action):
    """
    Bot introduction before first user message

    See:
    https://rasa.com/docs/rasa/default-actions/#action_session_start
    """
    def name(self) -> Text:
        return "action_session_start"

    async def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_iamabot")
        dispatcher.utter_message(response="utter_need_help")

        # Listen for user messages after bot introduction.
        # If left out, it will skip the next user input.
        return [ActionExecuted("action_listen")]

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

        logging.debug(category)

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
        twelve_hour_format = time_api.get_twelve_hour_clock(coords)

        message = (
            f"Right now in {location}, it's {day_of_week} ({date}), {twelve_hour_format}."
        )

        dispatcher.utter_message(text=message)
        return []
    
class ActionTellDayState(Action):

    def name(self) -> Text:
        return "action_tell_day_state"

    def run(self, 
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

        logging.debug(
                f"Sunset: {sunset}\n"
                f"Sunrise: {sunrise}\n"
                f"location: {location_time}\n"
            )
        
        if location_time >= sunrise and location_time <= sunset:
            dispatcher.utter_message(text=f"As of right now, it is daytime in the {location} area.")
        else:
            dispatcher.utter_message(text=f"It's nighttime as of the moment in {location}.")

        return []
    
from actions.api.mistral import conversate_with_user

class ActionMakeConversation(Action):

    def name(self) -> Text:
        return "action_make_conversation"

    def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        messages = []
       
        for event in tracker.events:
            if event.get("event") == "user":
                data = {
                    "role": "user",
                    "content": f"{event.get('text')}"
                }
                messages.append(data)
            elif event.get("event") == "bot":
                data = {
                    "role": "assistant",
                    "content": f"{event.get('text')}"
                }
                messages.append(data)

        llm_response = conversate_with_user(messages)
        dispatcher.utter_message(text=llm_response)

        return []

from actions.api.mangadex import MangaDex
import arrow

class ActionCheckMangaUpdates(Action):

    def name(self) -> Text:
        return "action_check_manga_updates"

    def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        username = os.environ["MANGADEX_USERNAME"]
        password = os.environ["MANGADEX_PASSWORD"]
        client_id = os.environ["MANGADEX_CLIENT_ID"]
        client_secret = os.environ["MANGADEX_CLIENT_SECRET"]

        dispatcher.utter_message(text="Okay, let me check right now.")

        user = MangaDex(username, password, client_id, client_secret)
        followed_manga = user.get_chapter_feed(content_rating=["safe", "suggestive", "erotica"])

        if not followed_manga:
            bad_response = (
                "Unfortunately, there seems to be an issue when ",
                "connecting to the MangaDex servers."
            )
            dispatcher.utter_message(text=bad_response)
            return []

        dispatcher.utter_message(text="Here are the most recent chapters:")

        for i in range(len(followed_manga["data"])):
            manga = followed_manga['data'][i]

            relationships = list(
                filter(
                    lambda relation: relation['type'] == 'manga', 
                    manga["relationships"]
                )
            )
            manga_info = relationships[0]['attributes']

            # Romanized title (e.g. Ogami Tsumiki to Kinichijou.)
            ro_title = manga_info['title']['en']

            # English alt title (e.g. Tsumiki Ogami & the Strange Everyday Life.)
            alt_title = list(
                filter(
                    lambda titles: titles.get('en', []), 
                    manga_info['altTitles']
                )
            )
            en_title = alt_title[0]['en'] if alt_title else None
            en_title = f"({en_title})" if en_title else ""

            series = f"{i + 1}) {ro_title} {en_title}"

            page_count = manga['attributes']['pages']
            page_count = f"{page_count} pages" if page_count > 1 else f"{page_count} page" 

            chapter_title = manga['attributes']['title'] or "No title"
            elapsed_time = arrow.get(manga['attributes']['publishAt']).humanize()

            chapter = f"{chapter_title} - {page_count} ({elapsed_time})"

            dispatcher.utter_message(text=series)
            dispatcher.utter_message(text=chapter)
            dispatcher.utter_message(text="\n\n")
        
        return [SlotSet("manga_history", followed_manga['data'])]

import json

class ActionSetLightState(Action):
    """
    Uses Shelly Plug Plus US
    See: https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch
    """
    def name(self) -> Text:
        return "action_set_light_state"

    def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:

        is_on = next(tracker.get_latest_entity_values("is_on"), "false")
        shelly_ip = os.environ['SHELLY_IP']

        params = {
            "id": 0,
            "on": is_on
        }

        try:
            url = f"http://{shelly_ip}/rpc/Switch.Set"
            response = requests.get(url, params=params)
            response.raise_for_status()

            logging.debug(f"Time elapsed: {response.elapsed}")
            logging.debug(json.dumps(response.json(), indent=2))

        except requests.exceptions.HTTPError as error:
            logging.error(error.strerror)
            dispatcher.utter_message("Sorry, but I can't connect to the Shelly Device.") 

        # This looks silly but you can't set boolean slots in intents
        light_state = "on" if is_on == "true" else "off"
        dispatcher.utter_message(f"Turning lights {light_state}.") 

        return []