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

        if joke["type"] == "single":
            dispatcher.utter_message(text=joke["joke"])
        else:
            dispatcher.utter_message(text=joke["setup"])
            dispatcher.utter_message(text=joke["delivery"])

        return []
