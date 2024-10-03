# import pytest
# from unittest.mock import patch, MagicMock
# from main import AppleMusicAPI
# from unittest import mock
# from requests.exceptions import HTTPError
# from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


# APPLE_TEAM_ID = "test_team_id"
# APPLE_KEY_ID = "test_key_id"
# APPLE_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
# MIIBVwIBADANBgkqhkiG9w0BAQEFAASCATwwggE4AgEAAkEAn1e1IjZjszXVc1nd
# W+vGAKwp0TqLBPCsoE/kH/W5z9J+4FL1ilnHpHIG2U0X1/kQH/zz+yC/L1DzJPLG
# Wlh9vQIDAQABAkEAgtB6gHe1FR5TPJl4Y8KoDbhO+RoWdB6e1KOlgJ8UczYrTGAz
# qZgBjdMTccWjOjEc7bZdJdpQ1+wsyMG88n2PwQIhAPa9bk/tqlQEDkEsUosEU1OC
# Y7vQeAJXrJLMfnLJ9P9jAiEAqZNVmy7UdNdPl09BZHtvTrYeY+QEgAUkNlhNNGTr
# GbcCIQD5vXGiQjbHCytKNpgU5J4LDNYA9LTibEYUNlnOsMf60wIgYtC/kGTxgncq
# P4BXtVq8mQ4ysEbPhChWxV8Z8rPcn5UCICruxCNlR4mjlvOn42Xlfdd0ABGvgCVR
# JP5ZtBspP1VB
# -----END PRIVATE KEY-----
# """


# @pytest.fixture
# @patch.object(AppleMusicAPI, "generate_token", return_value="mocked_token_string")
# def apple_api(mock_generate_token):
#     mock_artist = {"artist": "test_artist"}
#     mock_driver = mock.Mock()
#     return AppleMusicAPI(
#         APPLE_PRIVATE_KEY, APPLE_KEY_ID, APPLE_TEAM_ID, mock_driver, mock_artist
#     )


# @patch("jwt.encode", return_value="mocked_token_string")
# def test_generate_token(mock_jwt_encode, apple_api):
#     apple_api.generate_token(1)
#     assert isinstance(apple_api.token_str, str)
#     assert apple_api.token_str == "mocked_token_string"

#     mock_jwt_encode.assert_called_once()


# @patch("requests.Session")
# @patch.object(AppleMusicAPI, "generate_token", return_value="mocked_token_string")
# @patch.object(AppleMusicAPI, "token_is_valid", return_value=True)
# @patch.object(
#     AppleMusicAPI,
#     "_auth_headers",
#     return_value={"Authorization": "Bearer mocked_token_string"},
# )
# def test_call(
#     mock_auth_headers, mock_token_is_valid, mock_generate_token, mock_session_class
# ):
#     mock_session_instance = MagicMock()
#     mock_session_class.return_value = mock_session_instance

#     mock_response = MagicMock()
#     mock_response.status_code = 200
#     mock_response.json.return_value = {"key": "value"}
#     mock_response.raise_for_status = MagicMock()

#     mock_session_instance.request.return_value = mock_response

#     mock_driver = MagicMock()
#     apple_api = AppleMusicAPI(
#         secret_key=APPLE_PRIVATE_KEY,
#         key_id="test_key_id",
#         team_id="test_team_id",
#         driver=mock_driver,
#         artist="test_artist",
#     )

#     result = apple_api._call(
#         "GET",
#         "https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5",
#         params=None,
#     )

#     mock_session_instance.request.assert_called_once_with(
#         "GET",
#         "https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5",
#         headers={
#             "Authorization": "Bearer mocked_token_string",
#             "Content-Type": "application/json",
#         },
#         proxies=None,
#         params=None,
#         timeout=None,
#     )

#     assert result == {"key": "value"}


# @patch.object(AppleMusicAPI, "_call", return_value={"key": "value"})
# def test_successful_get(mock_call, apple_api):
#     result = apple_api._get(
#         "https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5"
#     )

#     mock_call.assert_called_once_with(
#         "GET",
#         "https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5",
#         {},
#     )

#     assert result == {"key": "value"}


# @patch("main.email_error")
# @patch("time.sleep")
# @patch.object(AppleMusicAPI, "_call")
# def test_get_retries_429_logic(mock_call, mock_sleep, mock_email_error, apple_api):
#     error_429 = HTTPError("Too Many Requests")
#     error_429.response = MagicMock(status_code=429)
#     mock_call.side_effect = error_429

#     apple_api.max_retries = 1

#     url = "https://api.music.apple.com/v1/catalog/us/playlists/pl.2b0e6e332fdf4b7a91164da3162127b5"

#     with pytest.raises(HTTPError, match="Too Many Requests"):
#         apple_api._get(url)

#     mock_email_error.assert_called_once_with(apple_api.artist)


# def test_get_playlist_ids_success(apple_api):
#     apple_api.driver.current_url = "https://music.apple.com/us/room/test_genre"

#     mock_card_1 = MagicMock()
#     mock_card_1.find_element.return_value.get_attribute.return_value = (
#         "https://music.apple.com/us/room/pl.test_playlist_1"
#     )

#     mock_card_2 = MagicMock()
#     mock_card_2.find_element.return_value.get_attribute.return_value = (
#         "https://music.apple.com/us/room/pl.test_playlist_2"
#     )

#     apple_api.driver.find_elements.return_value = [mock_card_1, mock_card_2]

#     apple_api.get_playlist_ids("test_genre")

#     assert apple_api.playlist_ids == ["pl.test_playlist_1", "pl.test_playlist_2"]
