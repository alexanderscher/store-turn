import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from spotify.package.main import SpotifyAPI


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


def test_get_access_token(spotify_api):
    """Test access token retrieval logic"""
    with patch.object(spotify_api, "perform_auth") as mock_auth:
        spotify_api.access_token_did_expire = True
        spotify_api.get_access_token()
        mock_auth.assert_called_once()


# @patch("requests.get")
# def test_get_playlists_from_category(mock_get, spotify_api):
#     """Test playlist retrieval from category"""
#     mock_response = MagicMock()
#     mock_response.status_code = 200
#     mock_response.json.return_value = {
#         "playlists": {
#             "items": [{"id": "1", "name": "Test Playlist"}],
#             "total": 1,
#             "limit": 1,
#             "next": None,
#         }
#     }
#     mock_get.return_value = mock_response

#     spotify_api.get_playlists_from_category("test_category", "US")
#     assert len(spotify_api.playlists) == 1
#     assert spotify_api.playlists[0]["id"] == "1"
#     assert spotify_api.playlists[0]["name"] == "Test Playlist"
