import boto3
import json

lambda_client = boto3.client("lambda")


def invoke_lambda_with_artists(artists_payload, function_name):
    print(f"Invoking {function_name} for {artists_payload['artist']}")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(artists_payload).encode("utf-8"),
    )
    return response


def lambda_handler(event, context):
    artists_payload = {
        "tracks": [
            {
                "artist": "Dave Blunts",
                "genres": {
                    "s": ["0JQ5DAqbMKFQ00XGBls6ym"],
                    "am": ["1533338569", "993297962"],
                },
            },
            {
                "artist": "Cash Cobain",
                "genres": {
                    "s": ["0JQ5DAqbMKFQ00XGBls6ym"],
                    "am": ["1533338569", "993297962", "6657994053"],
                },
            },
            {
                "artist": "lilbubblegum",
                "genres": {
                    "s": ["0JQ5DAqbMKFQ00XGBls6ym"],
                    "am": ["993297962"],
                },
            },
        ]
    }
    lambda_functions = ["store-turn-spotify", "store-turn-apple"]
    for p in artists_payload["tracks"]:
        for function_name in lambda_functions:
            print(f"Invoking {function_name} for {p}")
            response = invoke_lambda_with_artists(p, function_name)
            print(response)

    return {"statusCode": 200, "body": "Lambdas invoked"}
