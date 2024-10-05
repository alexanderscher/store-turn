from datetime import datetime, timedelta
import requests
from requests.exceptions import HTTPError
import time
from urllib.parse import urlencode
import base64
import os
import boto3
from botocore.exceptions import ClientError
from typing import List, TypedDict, Union, Dict


class SpotifyAPI(object):
    def __init__(
        self,
        client_id,
        client_secret,
        artist_name,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.access_token: str = None
        self.access_token_expires: datetime = datetime.now()
        self.access_token_did_expire: bool = True
        self.token_url: str = "https://accounts.spotify.com/api/token"
        self.playlists: List[str] = []
        self.checked_playlists: List[str] = []
        self.artist_name: str = artist_name

    def get_client_credentials(self) -> str:
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret is None or client_id is None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self) -> Dict[str, str]:
        client_creds_b64 = self.get_client_credentials()
        return {"Authorization": f"Basic {client_creds_b64}"}

    def get_token_data(self) -> Dict[str, str]:
        return {"grant_type": "client_credentials"}

    def perform_auth(self) -> bool:
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        data = r.json()
        now = datetime.now()
        access_token = data["access_token"]
        expires_in = data["expires_in"]
        expires = now + timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self) -> str:
        token = self.access_token
        expired = self.access_token_did_expire
        if token is None or expired:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_playlists_from_category(self, category, country) -> Union[None, list]:
        try:
            access_token = self.get_access_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            endpoint = f"https://api.spotify.com/v1/browse/categories/{category}/playlists?country={country}&offset=0&limit=50"
            playlist_ids_and_names = []
            while True:
                try:
                    r = requests.get(endpoint, headers=headers)
                    resp = r.json()

                    playlists = resp["playlists"]["items"]
                    for i in range(len(playlists)):
                        try:
                            playlist_ids_and_names.append(
                                {"id": playlists[i]["id"], "name": playlists[i]["name"]}
                            )
                        except TypeError:
                            pass

                    items_left = int(resp["playlists"]["total"]) - int(
                        resp["playlists"]["limit"]
                    )
                    if items_left > 0:
                        endpoint = resp["playlists"]["next"]
                    else:
                        break
                except requests.exceptions.MissingSchema:

                    break
            self.playlists = playlist_ids_and_names
        except ConnectionError as e:
            print(e)
            time.sleep(30)
            return self.get_playlists_from_category(category, "US")

    def find_artist_in_playlists(self, artist_name: str) -> List[str]:
        while True:
            res = []
            try:
                if not self.playlists:
                    email_error(self.artist_name)
                    raise Exception("There are no playlists to search!")

                access_token = self.get_access_token()
                headers = {"Authorization": f"Bearer {access_token}"}

                def check_artists(artists: List[Dict[str, str]]) -> bool:

                    for artist in artists:
                        if artist["name"].lower() == artist_name.lower():

                            return True
                    return False

                for idx, pl in enumerate(self.playlists):
                    if pl["name"] in self.checked_playlists:
                        continue

                    self.checked_playlists.append(pl["name"])
                    endpoint = f"https://api.spotify.com/v1/playlists/{pl['id']}/tracks"
                    r = requests.get(endpoint, headers=headers)
                    r.raise_for_status()
                    resp = r.json()

                    for i, track in enumerate(resp.get("items", [])):
                        try:
                            if check_artists(track["track"]["album"]["artists"]):
                                tr = track["track"]["name"]
                                added = track["added_at"]
                                datetime_obj = datetime.fromisoformat(added[:-1])
                                formatted_date = datetime_obj.strftime("%m/%d/%y")
                                print(
                                    "found in playlist",
                                    self.playlists[idx]["name"],
                                )
                                res.append(
                                    (
                                        tr,
                                        self.playlists[idx]["name"],
                                        f"{i + 1}/{len(resp['items'])} ({formatted_date})",
                                    )
                                )
                        except (TypeError, KeyError):
                            pass

                return res

            except (ConnectionError, ConnectionResetError) as e:
                print(f"Connection error occurred: {e}. Retrying in 30 seconds...")
                time.sleep(30)

            except Exception as e:
                email_error(self.artist_name)
                print(f"An unexpected error occurred: {e}")
                raise


client_id = os.getenv("SPOTIFY_CLIENT_ID")
user_id = os.getenv("SPOTIFY_USER_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")


if not client_id or not user_id or not client_secret:
    raise ValueError("Missing required environment variables for Spotify API")


class Genres(TypedDict):
    s: List[str]
    am: List[str]


class ArtistEvent(TypedDict):
    artist: str
    genres: Genres


Playlist = Dict[str, List[Dict[str, str]]]


class StoreTurn:
    def __init__(self, artist):
        self.artist: ArtistEvent = artist
        self.spotify_client = SpotifyAPI(
            client_id, client_secret, self.artist["artist"]
        )

    def find_artist(self) -> Playlist:
        artist = self.artist["artist"]
        playlist: Playlist = {artist: []}

        for genre in self.artist["genres"]["s"]:
            print(f"Getting playlists from {genre}")
            self.spotify_client.get_playlists_from_category(genre, "US")
            print(f"Searching playlists in {genre}")
            try:
                res = self.spotify_client.find_artist_in_playlists(
                    self.artist["artist"]
                )
                if not res:
                    print(f"No tracks found for {artist} in {genre}")
                for r in res:
                    playlist[artist].append(
                        {
                            "track": r[0],
                            "playlist": r[1],
                            "position": r[2],
                        }
                    )
            except Exception as e:
                print(f"Error finding artist in playlists: {e}")
                continue

        return playlist


def email_error(artist_name: str) -> Dict[str, str]:
    subject = f"Spotify Store Turn Error: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
    body = f"An error occurred while searching for {artist_name}"
    send_email_aws(subject, body)
    return {
        "statusCode": 500,
        "body": "Error occurred while searching for artist. Error email.",
    }


def send_email_aws(subject: str, body: str) -> None:
    ses_client = boto3.client(
        "ses",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWD_SECRET_ACCESS_KEY"),
    )
    sender = os.getenv("ALEX")

    try:
        response = ses_client.send_email(
            Destination={
                "ToAddresses": [
                    os.getenv("ALEX"),
                    # os.getenv("ARI"),
                    # os.getenv("LAURA"),
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


def lambda_handler(event: ArtistEvent, context) -> Dict[str, Union[int, str]]:
    artist_name = event["artist"]
    body = ""

    print(f"Starting search for {artist_name}")
    store_turn_artist = StoreTurn(event)
    playlists: Playlist = store_turn_artist.find_artist()
    artist_playlists = playlists.get(artist_name, [])

    if len(artist_playlists) == 0:
        subject = (
            f"Spotify Store Turn: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
        )
        body = f"No tracks found for {artist_name}"
        print(body)
        send_email_aws(subject, body)
        return {"statusCode": 200, "body": "No tracks found"}

    for a, tracks in playlists.items():
        body += f"\n{a}\n"
        for track_info in tracks:
            track = track_info["track"]
            playlist_name = track_info["playlist"]
            position = track_info["position"]
            body += f" - {track}: {playlist_name} | {position}\n"
    print("Finished")

    subject = (
        f"Spotify Store Turn: {artist_name} - {datetime.now().strftime('%m/%d/%y')}"
    )
    print(body)
    send_email_aws(subject, body)

    return {"statusCode": 200, "body": "Execution completed successfully"}
