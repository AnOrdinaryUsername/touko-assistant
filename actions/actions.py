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
        
        user_ask = next(tracker.get_latest_entity_values("is_daytime"), None)

        if not user_ask:
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
            if user_ask == 'day':
                dispatcher.utter_message(text=f"Correct, it's daytime in the {location} area.")
            else:
                dispatcher.utter_message(text=f"No, it's daytime in the {location} area.")
        else:
            if user_ask == 'night':
                dispatcher.utter_message(text=f"Correct, it's nighttime as of the moment in {location}.")
            else:
                dispatcher.utter_message(text=f"No, it's nighttime as of the moment in {location}.")

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

        chapter_count = next(tracker.get_latest_entity_values("number"), 5)

        followed_manga = user.get_chapter_feed(
            content_rating=["safe", "suggestive", "erotica"],
            limit=chapter_count
        )

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

class ActionTellMangaDetails(Action):

    def name(self) -> Text:
        return "action_tell_manga_details"

    def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
                ) -> List[Dict[Text, Any]]:
        
        index = next(tracker.get_latest_entity_values("number"), None)
        manga_history = tracker.get_slot("manga_history")

        if not index:
            dispatcher.utter_message(
                "Unable to extract details due to the lack of a value in the 'number' entity."
            )
            return []

        if not manga_history:
            dispatcher.utter_message(
                "Unable to get details due to a lack of a manga history. "
                "Ask for 'manga updates' to update the history."    
            )
            return []

        if index > len(manga_history) or index < 1:
            dispatcher.utter_message(
                f"Sorry, but {index} is out of the history range. "
                f"There are only {len(manga_history)} in my memory."
            )
            return []
        
        relationships = list(
                filter(
                    lambda relation: relation['type'] == 'manga', 
                    manga_history[index - 1]["relationships"]
                )
            )
        
        manga_info = relationships[0]['attributes']

        ro_title = manga_info['title']['en']
        description = manga_info['description']['en'] or "No description provided"

        UNKNOWN = "Unknown"

        publication_year = manga_info['year'] or UNKNOWN
        status = manga_info['status'].capitalize() or UNKNOWN
        content_rating = manga_info['contentRating'].capitalize() or UNKNOWN

        series_id = relationships[0]['id']
        link = f"https://mangadex.org/title/{series_id}"

        dispatcher.utter_message(text=ro_title)
        dispatcher.utter_message(text=f"PUBLICATION: {publication_year}, {status}")
        dispatcher.utter_message(text=f"RATING: {content_rating}")
        dispatcher.utter_message(text="\n\n")
        dispatcher.utter_message(text=link)
        dispatcher.utter_message(text="\n\n")
        dispatcher.utter_message(text=description)

        return []

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
        shelly_ip = os.environ['SHELLY_PLUG_IP']

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

import aiohttp
import asyncio

class ActionCheckTempAndStuff(Action):
    """
    Uses Shelly Gen 3 H&T. Measures temperature, humidity, and device power.
    See: https://shelly-api-docs.shelly.cloud/gen2/Devices/Gen2/ShellyPlusHT

    NOTE: It says it has a REST API, but due to being battery-powered you can't
    actually use it since it's in sleep mode for energy conservation reasons. REST
    API only works for like 3 minutes after you press the reset button until it hibernates.

    https://shelly-api-docs.shelly.cloud/gen2/General/SleepManagementForBatteryDevices
    """
    def name(self) -> Text:
        return "action_check_temp_and_stuff"

    async def fetch_data(self, session, url):
        response = await session.request(method="GET", url=url)
        response.raise_for_status()
        data = await response.json()
        return data

    async def report_results(self):
        shelly_ip = os.environ['SHELLY_HT_IP']

        urls = [
            f"http://{shelly_ip}/rpc/Temperature.GetStatus?id=0",
            f"http://{shelly_ip}/rpc/Humidity.GetStatus?id=0",
            f"http://{shelly_ip}/rpc/DevicePower.GetStatus?id=0",
        ]
        
        async with aiohttp.ClientSession() as session:
            try:
                tasks = [self.fetch_data(session, url) for url in urls]
                results = await asyncio.gather(*tasks)
            except Exception:
                return []

        return results

    async def run(self, 
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]
            ) -> List[Dict[Text, Any]]:
        
        results = await self.report_results()

        logging.debug(results)

        if not results:
            # Read previous reading data if API not available 
            json_file = os.path.join(os.getcwd(), "actions", "api", "shelly", "gen3_ht_data.json")

            with open(json_file) as file:
                json_data = json.load(file)
            
            dispatcher.utter_message(
                "Unable to fetch REST API. Using previous readings instead "
                f"(last updated {arrow.get(json_data['updatedAt']).humanize()})."
            )

            temp = f"The current indoor temp is {json_data.get('tF')}°F."
            dispatcher.utter_message(text=temp)

            humidity = f"Indoor humidity is at {json_data.get('rh')}%."
            dispatcher.utter_message(text=humidity)

            battery_percent = json_data['battery']
            is_charging = json_data['isCharging']

            if battery_percent <= 25 and not is_charging:
                dispatcher.utter_message(
                    text=(
                        f"Keep in mind your battery is low ({battery_percent}%). "
                        "Replace them soon!"
                    )
                )
            else:
                dispatcher.utter_message(text=f"Device battery is at {battery_percent}%.")

        else:
            for result in results:
                if result.get('tF', None):
                    temp = f"The current indoor temp is {result.get('tF')}°F."
                    dispatcher.utter_message(text=temp)

                elif result.get('rh', None):
                    humidity = f"Indoor humidity is at {result.get('rh')}%."
                    dispatcher.utter_message(text=humidity)

                elif result.get('battery', None):
                    battery_percent = result['battery']['percent']
                    is_charging = result['external']['present']

                    if battery_percent <= 25 and not is_charging:
                        dispatcher.utter_message(
                            text=(
                                f"Keep in mind your battery is low ({battery_percent}%). "
                                "Replace them soon!"
                            )
                        )
                    else:
                        dispatcher.utter_message(text=f"Device battery is at {battery_percent}%.")

        return []