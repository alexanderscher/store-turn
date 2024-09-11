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
    print("Creating SpotifyAPI instance")
    return SpotifyAPI(client_id, client_secret, artist_name)


def test_get_client_credentials(spotify_api):
    """Test client credentials encoding"""
    encoded_creds = spotify_api.get_client_credentials()
    assert isinstance(encoded_creds, str)
    assert len(encoded_creds) > 0
