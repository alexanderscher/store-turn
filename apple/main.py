from datetime import datetime, timedelta
import jwt
import requests
from requests.exceptions import HTTPError
import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from typing import List
import os
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
import boto3
from botocore.exceptions import ClientError
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


class AppleMusicAPI:
    """
    This class is used to connect to the Apple Music API and make requests for catalog resources
    """

    def __init__(
        self,
        secret_key,
        key_id,
        team_id,
        driver,
        proxies=None,
        requests_session=True,
        max_retries=10,
        requests_timeout=None,
        session_length=12,
    ):
        self.proxies = proxies
        self._secret_key = secret_key
        self._key_id = key_id
        self._team_id = team_id
        self._alg = "ES256"
        self.token_str = ""
        self.session_length = session_length
        self.token_valid_until = None
        self.generate_token(session_length)
        self.root = "https://api.music.apple.com/v1/"
        self.max_retries = max_retries
        self.requests_timeout = requests_timeout
        if requests_session:
            self._session = requests.Session()
        else:
            self._session = requests.api
        self.playlist_ids = None
        self.driver: WebDriver = driver
        self.res = []

    def token_is_valid(self):
        return (
            datetime.now() <= self.token_valid_until
            if self.token_valid_until is not None
            else False
        )

    def generate_token(self, session_length):
        """
        Generate encrypted token to be used by in API requests.
        Set the class token parameter.
        :param session_length: Length Apple Music token is valid, in hours
        """
        token_exp_time = datetime.now() + timedelta(hours=session_length)
        headers = {"alg": self._alg, "kid": self._key_id}
        payload = {
            "iss": self._team_id,  # issuer
            "iat": int(datetime.now().timestamp()),  # issued at
            "exp": int(token_exp_time.timestamp()),  # expiration time
        }
        self.token_valid_until = token_exp_time
        token = jwt.encode(
            payload, self._secret_key, algorithm=self._alg, headers=headers
        )
        self.token_str = token if type(token) is not bytes else token.decode()

    def _auth_headers(self):
        """
        Get header for API request
        :return: header in dictionary format
        """
        if self.token_str:
            return {"Authorization": "Bearer {}".format(self.token_str)}
        else:
            return {}

    def _call(self, method, url, params):
        """
        Make a call to the API
        :param method: 'GET', 'POST', 'DELETE', or 'PUT'
        :param url: URL of API endpoint
        :param params: API paramaters
        :return: JSON data from the API
        """
        if not url.startswith("http"):
            url = self.root + url

        if not self.token_is_valid():
            self.generate_token(self.session_length)

        headers = self._auth_headers()
        headers["Content-Type"] = "application/json"
        r = self._session.request(
            method,
            url,
            headers=headers,
            proxies=self.proxies,
            params=params,
            timeout=self.requests_timeout,
        )
        r.raise_for_status()  # Check for error
        return r.json()

    def _get(self, url, **kwargs):
        """
        GET request from the API
        :param url: URL for API endpoint
        :return: JSON data from the API
        """
        retries = self.max_retries
        delay = 1
        while retries > 0:
            try:
                return self._call("GET", url, kwargs)
            except HTTPError as e:
                retries -= 1
                status = e.response.status_code
                if status == 429 or (500 <= status < 600):
                    if retries < 0:
                        raise
                    else:
                        print("retrying ..." + str(delay) + " secs")
                        time.sleep(delay + 1)
                        delay += 1
                else:
                    raise
            except Exception as e:
                print("exception", str(e))
                retries -= 1
                if retries >= 0:
                    print("retrying ..." + str(delay) + "secs")
                    time.sleep(delay + 1)
                    delay += 1
                else:
                    raise

    def get_genre(self, genre: str) -> None:
        self.driver.get("https://music.apple.com/us/search")
        time.sleep(2)
        genres = self.driver.find_elements(By.CLASS_NAME, "grid-item")
        print("https://music.apple.com/us/search")
        for g in genres:
            if g.text == genre:
                g.click()
                print(f"clicked {genre}")
                break

    # def get_room(self, genre):
    #     self.get_genre(genre)
    #     print(f"getting room for {genre}")
    #     if genre == "Chill":
    #         time.sleep(10)
    #         if not self.driver.current_url.__contains__(
    #             "https://music.apple.com/us/curator/"
    #         ):
    #             MyException = "You are not on a genre page!"
    #             raise MyException("You are not on a genre page!")
    #         else:
    #             options = self.driver.find_elements(By.CLASS_NAME, "title__button")
    #             # time.sleep(2)
    #             for o in options:
    #                 if o.text == "Study Time":
    #                     #         # o.find_element(By.CLASS_NAME, "see-all").click()
    #                     o.click()

    #     else:
    #         time.sleep(10)
    #         if not self.driver.current_url.__contains__(
    #             "https://music.apple.com/us/curator/"
    #         ):
    #             MyException = "You are not on a genre page!"
    #             raise MyException("You are not on a genre page!")
    #         else:
    #             print(self.driver.current_url)
    #             options = self.driver.find_elements(By.CLASS_NAME, "title__button")
    #             time.sleep(5)
    #             for o in options:
    #                 if o.text == "Playlists" or o.text == "Popular Playlists":
    #                     o.click()
    #                     print("clicked playlists")

    def get_playlist_ids(self, genre):
        self.driver.get(f"https://music.apple.com/us/room/{genre}")

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.url_contains("https://music.apple.com/us/room/"))

        ids: List[str] = []

        if not self.driver.current_url.__contains__("https://music.apple.com/us/room/"):
            self.driver.refresh()
            wait.until(EC.url_contains("https://music.apple.com/us/room/"))

            if not self.driver.current_url.__contains__(
                "https://music.apple.com/us/room/"
            ):
                raise Exception("You are not on a room page!")

        else:
            print(self.driver.current_url)
            print("on room page getting playlist ids")
            retry_count = 3
            for attempt in range(retry_count):
                try:
                    cards = self.driver.find_elements(By.CLASS_NAME, "grid-item")
                    print("cards", len(cards))
                    for card in cards:
                        a = card.find_element(By.TAG_NAME, "a")
                        href = a.get_attribute("href")
                        id = href[href.find("pl.") : len(href)]
                        ids.append(id)
                    break
                except StaleElementReferenceException:
                    print("Stale element reference, retrying...")
                    time.sleep(2)

        if not ids:
            raise Exception("No playlists found or the page did not load correctly.")

        self.playlist_ids = ids

    def scrape(self, genre):
        try:
            self.get_playlist_ids(genre)
        except Exception as e:
            print("Something went wrong.")
            # print(e)
            raise

    def search_artist(self, track_artist: str):
        if not len(self.playlist_ids):
            MyException = "There are no playlists to search!"
            raise MyException("There are no playlists to search!")
        else:
            for pl in self.playlist_ids:
                pl_info = self._get(
                    f"https://api.music.apple.com/v1/catalog/us/playlists/{pl}"
                )
                pl_name = pl_info["data"][0]["attributes"]["name"]
                pl_tracks = pl_info["data"][0]["relationships"]["tracks"]["data"]
                for i, track in enumerate(pl_tracks):
                    try:
                        if (
                            track_artist.lower()
                            in track["attributes"]["artistName"].lower()
                        ):
                            print(
                                "- ",
                                track["attributes"]["name"],
                                ": ",
                                pl_name,
                                "|",
                                f"{i + 1}/{len(pl_tracks)}",
                            )
                            self.res.append(
                                (
                                    track["attributes"]["name"],
                                    pl_name,
                                    f"{i + 1}/{len(pl_tracks)}",
                                )
                            )

                    except KeyError:
                        pass

    def nmd_a(self, track_artist: str):
        self.driver.get(
            "https://music.apple.com/us/playlist/new-music-daily/pl.2b0e6e332fdf4b7a91164da3162127b5"
        )
        print("checking nmd")
        time.sleep(10)
        row = self.driver.find_elements(By.CLASS_NAME, "songs-list-row")

        for i, song in enumerate(row):
            t = song.find_element(By.XPATH, ".//div[2]").text
            a = song.find_element(By.XPATH, ".//div[3]").text

            if track_artist.lower() in a.lower():
                print(
                    "- ", t, ": New Music Daily", "|", f"{str(i + 1)}/{str(len(row))}"
                )
                self.res.append((t, "New Music Daily", f"{str(i + 1)}/{str(len(row))}"))

    def apple_songs(self, url: str, roster: str, chart: str):
        self.driver.get(url)
        time.sleep(5)
        print("checking", chart)
        row = self.driver.find_elements(By.CLASS_NAME, "songs-list-row")

        for i, song in enumerate(row):
            t = song.find_element(By.XPATH, ".//div[2]").text
            a = song.find_element(By.XPATH, ".//div[3]").text
            if roster.lower() in a.lower():
                print(f" - {t} :", chart, "|", f"{str(i + 1)}/{str(len(row))}")
                self.res.append((t, chart, f"{str(i + 1)}/{str(len(row))}"))

    def apple_albums(self, url: str, roster: str, chart: str):
        self.driver.get(url)
        time.sleep(5)
        print("checking", chart)

        row = self.driver.find_elements(
            By.XPATH, '//*[@id="scrollable-page"]/main/div/div/div/ul/li'
        )

        for i, n in enumerate(row):
            try:

                artist = n.find_element(By.XPATH, ".//div/div[2]/div/p/div/span/a").text
                album = n.find_element(By.CLASS_NAME, "product-lockup__title-link").text
                if roster.lower() in artist.lower():
                    print(f" - {album} :", chart, "|", f"{str(i + 1)}/{str(len(row))}")
                    self.res.append((album, chart, f"{str(i + 1)}/{str(len(row))}"))
            except NoSuchElementException:
                pass

    def check_album(self, artist):

        self.apple_albums(
            "https://music.apple.com/us/room/976405703",
            artist,
            "New Music All Genres - Albums",
        )

        self.apple_albums(
            "https://music.apple.com/us/room/993298537",
            artist,
            "New Release Pop - Albums",
        )

        self.apple_albums(
            "https://music.apple.com/us/room/1532319379",
            artist,
            "New Release Hip Hop - Albums",
        )

        self.apple_albums(
            "https://music.apple.com/us/room/993298342",
            artist,
            "New Release R&B - Albums",
        )

    def check_song(self, artist):

        self.apple_songs(
            "https://music.apple.com/us/room/1457265758",
            artist,
            "Best New Songs All Genres",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/6451822724",
            artist,
            "Emerging R&B Songs",
        )

        self.apple_songs(
            "https://music.apple.com/us/room/1013646917",
            artist,
            "Hot Track R&B",
        )

        self.apple_songs(
            "https://music.apple.com/us/room/993297955",
            artist,
            "Best New Songs Hip Hop",
        )

        self.apple_songs(
            "https://music.apple.com/us/room/993298549",
            artist,
            "Best New Songs Pop",
        )


APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")

if not APPLE_TEAM_ID or not APPLE_KEY_ID or not APPLE_PRIVATE_KEY:
    raise ValueError("Missing required environment variables for Apple Music API")

APPLE_PRIVATE_KEY = (
    f"-----BEGIN PRIVATE KEY-----\n{APPLE_PRIVATE_KEY}\n-----END PRIVATE KEY-----"
)


class StoreTurn:

    def __init__(self, artist, driver):
        self.artist = artist
        self.driver = driver
        self.apple_music_client = AppleMusicAPI(
            APPLE_PRIVATE_KEY, APPLE_KEY_ID, APPLE_TEAM_ID, self.driver
        )

    def find_artist(self):

        res = {}

        print("\n" + self.artist["artist"] + "\n")

        print(f"\nApple Music:")

        self.apple_music_client.nmd_a(self.artist["artist"])
        self.apple_music_client.check_song(self.artist["artist"])
        self.apple_music_client.check_album(self.artist["artist"])
        for genre in self.artist["genres"]["am"]:
            self.apple_music_client.scrape(genre)
            time.sleep(5)
            self.apple_music_client.search_artist(self.artist["artist"])

        res[self.artist["artist"]] = self.apple_music_client.res
        return res


def send_email(subject, body, recipient):
    ses_client = boto3.client(
        "ses",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWD_SECRET_ACCESS_KEY"),
    )
    sender = "alex@listen2thekids.com"

    try:
        response = ses_client.send_email(
            Destination={
                "ToAddresses": [
                    recipient,
                ],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": body,
                    },
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")


def lambda_handler(event, context):
    options = webdriver.ChromeOptions()

    options.binary_location = "/opt/chrome/chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    service = webdriver.ChromeService("/opt/chromedriver")

    # local
    # from selenium.webdriver.chrome.service import Service
    # from webdriver_manager.chrome import ChromeDriverManager

    # service = Service(ChromeDriverManager().install())

    driver: WebDriver = webdriver.Chrome(service=service, options=options)
    print(event)
    store_turn_artist = StoreTurn(event, driver)
    res = store_turn_artist.find_artist()

    print(res)

    body = ""

    for a, tracks in res.items():
        body += f"\n{a}\n"
        for track_info in tracks:
            track, playlist_name, position = track_info
            body += f" - {track}: {playlist_name} | {position}\n"

    subject = f"Apple Store Turn - {datetime.now().strftime('%m/%d/%y')}"
    recipient = "alexcscher@gmail.com"
    print(body)
    send_email(subject, body, recipient)
    driver.quit()
    return {"statusCode": 200, "body": "Execution completed successfully"}
