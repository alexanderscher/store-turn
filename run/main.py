import boto3
import json

lambda_client = boto3.client("lambda")


def invoke_lambda_with_artists(artists_payload, function_name):
    print(f"Invoking {function_name} for {artists_payload['artist']['s']}")
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
                    "am": ["993297962"],
                },
            },
            {
                "artist": "Cochise",
                "genres": {
                    "s": ["0JQ5DAqbMKFQ00XGBls6ym"],
                    "am": ["993297962"],
                },
            },
        ]
    }
    lambda_functions = ["spotify-store-turn", "apple-store-turn"]

    for p in artists_payload["tracks"]:
        for function_name in lambda_functions:
            response = invoke_lambda_with_artists(p, function_name)
            print(response)

    return {"statusCode": 200, "body": "Lambdas invoked"}
