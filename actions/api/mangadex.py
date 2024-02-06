from typing import List, Dict
import requests
import logging
import json

class MangaDex(object):
    """
    API Link:
    https://api.mangadex.org/docs/
    """
    def __init__(self, username: str, password: str, client_id: str, client_secret: str):
        self.creds = {
            "grant_type": "password",
            "username": f"{username}",
            "password": f"{password}",
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}"
        }

    def _get_access_tokens(self) -> Dict[str, str]:
        """
        Note: If you see something like "ssl.SSLError: [SSL: WRONG_VERSION_NUMBER]",
        check your antivirus or router security to see if it's flagging MangaDex as dangerous.

        Either whitelist the site or disable router security to get it working. 
        
        Verify if it works by entering the command in your terminal
        (should show a bunch of info).

        `openssl s_client auth.mangadex.org:443`
        """
        response = requests.post(
            "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token",
            data=self.creds
        )
        tokens = response.json()
        return tokens

    def get_chapter_feed(self, 
                            limit: int = 5, 
                            translated_languages: List[str] = ["en"],
                            content_rating: List[str] = ["safe", "suggestive"]
                        ):
        """
        Get followed chapter updates from user feed
        https://api.mangadex.org/docs/swagger.html#/Feed/get-user-follows-manga-feed
        """
        try:
            tokens = self._get_access_tokens()
        except requests.exceptions.HTTPError as error:
            logging.error(error.strerror)
            return []


        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {tokens['access_token']}",
        }

        base_url = "https://api.mangadex.org/user/follows/manga/feed"
        ratings = "".join([f"&contentRating[]={rating}" for rating in content_rating])
        languages = "".join([f"&translatedLanguage[]={lang}" for lang in translated_languages])

        manga_feed= (
            f"{base_url}"
            f"?limit={limit}"
            "&offset=0"
            "&includes[]=manga"
            f"{ratings}"
            f"{languages}"
            "&order[readableAt]=desc"
        )

        try:
            response = requests.get(manga_feed, headers=headers)
            response.raise_for_status()
            chapters = response.json()

            logging.debug(f"Time elapsed: {response.elapsed}")
            logging.debug(json.dumps(chapters, indent=2))

        except requests.exceptions.HTTPError as error:
            logging.error(error.strerror)
            return []

        return chapters
