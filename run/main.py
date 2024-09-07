import boto3
import json

lambda_client = boto3.client("lambda")


def invoke_lambda_with_artists(artists_payload):
    print(f"Invoking for {artists_payload['artist']['s']}")
    response = lambda_client.invoke(
        FunctionName="spotify-store-turn",
        InvocationType="Event",
        Payload=json.dumps(artists_payload).encode("utf-8"),
    )
    return response


def lambda_handler(event, context):
    artists_payload = {
        "tracks": [
            {
                "artist": {"s": "Dave Blunts", "am": "Dave Blunts"},
                "genres": {"s": ["0JQ5DAqbMKFQ00XGBls6ym"]},
            },
            {
                "artist": {"s": "Cochise", "am": "Cochise"},
                "genres": {"s": ["0JQ5DAqbMKFQ00XGBls6ym"]},
            },
        ]
    }

    for p in artists_payload["tracks"]:
        response = invoke_lambda_with_artists(p)
        print(response)

    return {"statusCode": 200, "body": "Lambdas invoked"}
