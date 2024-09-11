import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from spotify.package.main import SpotifyAPI
from spotify.package.main import StoreTurn
from spotify.package.main import lambda_handler


@pytest.fixture
def spotify_api():
    """Fixture for SpotifyAPI instance"""
    client_id = "test_client_id"
    client_secret = "test_client_secret"
    artist_name = "test_artist"
    return SpotifyAPI(client_id, client_secret, artist_name)


def test_get_client_credentials(spotify_api):
    """Test client credentials encoding"""
    encoded_creds = spotify_api.get_client_credentials()
    assert isinstance(encoded_creds, str)
    assert len(encoded_creds) > 0


@patch("requests.post")
def test_perform_auth(mock_post, spotify_api):
    """Test successful authentication"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "expires_in": 3600,
    }
    mock_post.return_value = mock_response

    assert spotify_api.perform_auth() == True
    assert spotify_api.access_token == "test_access_token"
    assert spotify_api.access_token_expires > datetime.now()


@patch.object(SpotifyAPI, "perform_auth")
def test_get_access_token_expired(mock_perform_auth, spotify_api):
    """Test case where the access token has expired"""
    spotify_api.access_token = "expired_token"
    spotify_api.access_token_did_expire = True

    def set_valid_token():
        spotify_api.access_token = "new_valid_token"
        spotify_api.access_token_did_expire = False

    mock_perform_auth.side_effect = set_valid_token
    token = spotify_api.get_access_token()
    mock_perform_auth.assert_called_once()
    assert token == "new_valid_token"


@patch.object(SpotifyAPI, "get_access_token")
def test_get_access_token_valid(mock_get_access_token, spotify_api):
    spotify_api.access_token = "valid_token"
    spotify_api.access_token_did_expire = False
    mock_get_access_token.return_value = spotify_api.access_token

    token = mock_get_access_token()

    assert token == "valid_token"
    assert mock_get_access_token() == token


@patch("requests.get")
@patch.object(SpotifyAPI, "get_access_token", return_value="valid_token")
def test_get_playlists_from_category(mock_get_access_token, mock_get, spotify_api):
    """Test playlist retrieval from category"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "playlists": {
            "items": [{"id": "1", "name": "Test Playlist"}],
            "total": 1,
            "limit": 1,
            "next": None,
        }
    }
    mock_get.return_value = mock_response

    spotify_api.get_playlists_from_category("test_category", "US")
    assert len(spotify_api.playlists) == 1
    assert spotify_api.playlists[0]["id"] == "1"
    assert spotify_api.playlists[0]["name"] == "Test Playlist"
    mock_get_access_token.assert_called_once()


@patch("requests.get")
@patch.object(SpotifyAPI, "get_access_token", return_value="valid_token")
def test_find_artist_in_playlist(mock_get_access_token, mock_get, spotify_api):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "track": {
                    "name": "test_track",
                    "album": {"artists": [{"name": "test_artist"}]},
                },
                "added_at": "2024-09-06T04:00:00Z",
            }
        ]
    }
    mock_get.return_value = mock_response

    spotify_api.playlists = [{"id": "test_playlist_id", "name": "test_playlist"}]

    artist_name = "test_artist"
    result = spotify_api.find_artist_in_playlists(artist_name)

    assert len(result) == 1
    assert result[0][0] == "test_track"
    assert result[0][1] == "test_playlist"
    assert "1/1" in result[0][2]

    mock_get.assert_called_once_with(
        "https://api.spotify.com/v1/playlists/test_playlist_id/tracks",
        headers={"Authorization": "Bearer valid_token"},
    )
    mock_get_access_token.assert_called_once()


@patch("spotify.package.main.email_error")
def test_find_artist_in_playlist(mock_email_error, spotify_api):

    spotify_api.playlists = []
    with pytest.raises(Exception) as exc_info:
        spotify_api.find_artist_in_playlists("test_artist")
    assert mock_email_error.called
    assert str(exc_info.value) == "There are no playlists to search!"


@pytest.fixture
def store_turn():
    artist = {
        "artist": "test-artist",
        "genres": {
            "s": [
                "test-genre",
            ],
        },
    }

    spotify_client = SpotifyAPI("test_client_id", "test_client_secret", artist)
    return StoreTurn(artist=artist)


@patch.object(SpotifyAPI, "get_playlists_from_category")
@patch.object(SpotifyAPI, "find_artist_in_playlists")
def test_find_artist(
    mock_find_artist_in_playlists, mock_get_playlists_from_category, store_turn
):
    store_turn.spotify_client.playlists = [
        {"id": "test_playlist_id", "name": "test_playlist"}
    ]
    mock_find_artist_in_playlists.return_value = [
        ("test_track", "test_playlist", "1/1")
    ]
    result = store_turn.find_artist()
    result_artists = result[store_turn.artist["artist"]]
    assert len(result_artists) == 1
    assert result_artists[0]["track"] == "test_track"
    assert result_artists[0]["playlist"] == "test_playlist"
    assert result_artists[0]["position"] == "1/1"
    mock_get_playlists_from_category.assert_called_once()
    mock_find_artist_in_playlists.assert_called_once()


@patch("spotify.package.main.boto3.client")
@patch("spotify.package.main.send_email_aws")
@patch.object(StoreTurn, "find_artist")
def test_lambda_handler_found(mock_find_artist, mock_send_email_aws, mock_boto_client):
    mock_boto_client.return_value.send_email_aws.return_value = {
        "MessageId": "mock_message_id"
    }
    event = {
        "artist": "test-artist",
        "genres": {
            "s": [
                "test-genre",
            ],
        },
    }
    mock_find_artist.return_value = {
        "test-artist": [
            {
                "track": "test_track",
                "playlist": "test_playlist",
                "position": "1/1",
            }
        ]
    }

    result = lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert result["body"] == "Execution completed successfully"
    mock_find_artist.assert_called_once()
    mock_send_email_aws.assert_called_once()


@patch("spotify.package.main.boto3.client")
@patch("spotify.package.main.send_email_aws")
@patch.object(StoreTurn, "find_artist")
def test_lambda_handler_not_found(
    mock_find_artist, mock_send_email_aws, mock_boto_client
):
    mock_boto_client.return_value.send_email.return_value = {
        "MessageId": "mock_message_id"
    }
    event = {
        "artist": "test-artist",
        "genres": {
            "s": [
                "test-genre",
            ],
        },
    }
    mock_find_artist.return_value = {"test-artist": []}

    result = lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert result["body"] == "No tracks found"
    mock_find_artist.assert_called_once()
    mock_send_email_aws.assert_called_once()
