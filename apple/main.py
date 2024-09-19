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
from typing import List, TypedDict, Union, Dict

APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")

if not APPLE_TEAM_ID or not APPLE_KEY_ID or not APPLE_PRIVATE_KEY:
    raise ValueError("Missing required environment variables for Apple Music API")

APPLE_PRIVATE_KEY = (
    f"-----BEGIN PRIVATE KEY-----\n{APPLE_PRIVATE_KEY}\n-----END PRIVATE KEY-----"
)


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
        artist,
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
        self.res: List[str] = []
        self.artist: str = artist

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
                        email_error(self.artist)
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
                    email_error(self.artist)
                    raise

    def get_playlist_ids(self, genre) -> None:
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
                email_error(self.artist)
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

    def scrape(self, genre) -> None:
        try:
            self.get_playlist_ids(genre)
        except Exception as e:
            email_error(self.artist)
            print("Something went wrong.")
            raise

    def search_artist(self, track_artist: str) -> None:
        if not len(self.playlist_ids):
            MyException = "There are no playlists to search!"
            raise MyException("There are no playlists to search!")
        else:
            for pl in self.playlist_ids:
                try:
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
                                    "found in playlist:",
                                    pl_name,
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
                except HTTPError:
                    pass

    def new_music_daily(self, track_artist) -> None:

        pl_info = self._get(
            f"https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5"
        )
        pl_name = pl_info["data"][0]["attributes"]["name"]
        pl_tracks = pl_info["data"][0]["relationships"]["tracks"]["data"]
        for i, track in enumerate(pl_tracks):
            try:
                if track_artist.lower() in track["attributes"]["artistName"].lower():
                    print(
                        "found in playlist:",
                        pl_name,
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

    def apple_songs(self, url: str, roster: str, chart: str) -> None:

        self.driver.get(url)
        time.sleep(5)
        print("checking", chart)

        try:
            row = self.driver.find_elements(By.CLASS_NAME, "songs-list-row")

            for i, song in enumerate(row):
                t = song.find_element(By.XPATH, ".//div[2]").text
                a = song.find_element(By.XPATH, ".//div[3]").text
                if roster.lower() in a.lower():
                    print("found in playlist:", chart)
                    self.res.append((t, chart, f"{str(i + 1)}/{str(len(row))}"))
        except NoSuchElementException:
            email_error(roster)
            raise Exception("No songs found")

    def apple_albums(self, url: str, roster: str, chart: str) -> None:
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
                    print("found in playlist:", chart)
                    self.res.append((album, chart, f"{str(i + 1)}/{str(len(row))}"))
            except NoSuchElementException:
                pass

    def all(self, artist) -> None:
        self.apple_songs(
            "https://music.apple.com/us/room/1457265758",
            artist,
            "Best New Songs All Genres",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/6670727724", artist, "Latest Songs"
        )
        self.apple_songs(
            "https://music.apple.com/us/room/1533338568", artist, "Up Next Hot Tracks"
        )
        self.apple_albums(
            "https://music.apple.com/us/room/976405703",
            artist,
            "New Music All Genres - Albums",
        )

    def hihop(self, artist) -> None:
        self.apple_albums(
            "https://music.apple.com/us/room/1532319379",
            artist,
            "New Release Hip Hop - Albums",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/993297955",
            artist,
            "Best New Songs Hip Hop",
        )

    def pop(self, artist) -> None:
        self.apple_albums(
            "https://music.apple.com/us/room/993298537",
            artist,
            "New Release Pop - Albums",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/993298549",
            artist,
            "Best New Songs Pop",
        )

    def rb(self, artist) -> None:
        self.apple_albums(
            "https://music.apple.com/us/room/993298342",
            artist,
            "New Release R&B - Albums",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/6451822724",
            artist,
            "Emerging R&B Songs",
        )
        self.apple_songs(
            "https://music.apple.com/us/room/6657994054", artist, "Best New Songs R&B"
        )


class Genres(TypedDict):
    s: List[str]
    am: List[str]


class ArtistEvent(TypedDict):
    artist: str
    genres: Genres


class StoreTurn:
    def __init__(self, artist, driver):
        self.artist: ArtistEvent = artist
        self.driver: WebDriver = driver
        self.apple_music_client = AppleMusicAPI(
            APPLE_PRIVATE_KEY,
            APPLE_KEY_ID,
            APPLE_TEAM_ID,
            self.driver,
            self.artist["artist"],
        )

    def find_artist(self) -> Dict[str, List[str]]:
        res = {}

        print("\n" + self.artist["artist"] + "\n")

        print(f"\nApple Music:")

        self.apple_music_client.new_music_daily(self.artist["artist"])
        self.apple_music_client.all(self.artist["artist"])
        genres = self.artist["genres"]["am"]

        for genre in genres:
            print(f"Checking {genre}")
            if genre == "993297962":
                print("checking hiphop scrape")
                self.apple_music_client.hihop(self.artist["artist"])
            if genre == "976439548":
                print("checking pop scrape")
                self.apple_music_client.pop(self.artist["artist"])
            if genre == "6657994053":
                print("checking rb scrape")
                self.apple_music_client.rb(self.artist["artist"])

            time.sleep(5)
            self.apple_music_client.scrape(genre)
            time.sleep(5)
            self.apple_music_client.search_artist(self.artist["artist"])

        res[self.artist["artist"]] = self.apple_music_client.res
        return res


def email_error(artist_name) -> Dict[str, str]:
    subject = (
        f"Apple Store Turn Error: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
    )
    body = f"An error occurred while searching for {artist_name}"
    send_email(subject, body)
    return {
        "statusCode": 500,
        "body": "Error occurred while searching for artist. Error email.",
    }


def send_email(subject, body) -> None:
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
                    "alexcscher@gmail.com",
                    "ari@listen2thekids.com",
                    "laura@listen2thekids.com",
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


def lambda_handler(event, context) -> Dict[str, Union[int, str]]:
    options = webdriver.ChromeOptions()

    options.binary_location = "/opt/chrome/chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1963x1696")
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

    driver = webdriver.Chrome(service=service, options=options)
    print(event)
    store_turn_artist = StoreTurn(event, driver)
    res = store_turn_artist.find_artist()
    artist_name = event["artist"]
    print(res)

    artist_tracks = res.get(artist_name, [])
    if len(artist_tracks) == 0:
        body = f"No tracks found for {artist_name}"
        subject = (
            f"Apple Store Turn: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
        )
        print(body)
        send_email(subject, body)
        return {"statusCode": 200, "body": "No tracks found"}

    body = ""

    for a, tracks in res.items():
        body += f"\n{a}\n"
        for track_info in tracks:
            track, playlist_name, position = track_info
            body += f" - {track}: {playlist_name} | {position}\n"

    subject = f"Apple Store Turn: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
    print(body)
    send_email(subject, body)
    driver.quit()
    return {"statusCode": 200, "body": "Execution completed successfully"}
