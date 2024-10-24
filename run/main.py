import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError

lambda_client = boto3.client("lambda")


def invoke_lambda_with_artists(artists_payload, function_name):
    print(f"Invoking {function_name} for {artists_payload['artist']}")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(artists_payload).encode("utf-8"),
    )
    return response


def send_email_ses():
    ses_client = boto3.client(
        "ses",
        region_name="us-east-1",
    )
    sender = os.getenv("ALEX")

    subject = f"Started Store Turn - {datetime.now().strftime('%m/%d/%y')}"
    body = f"Started Store Turn - {datetime.now().strftime('%m/%d/%y')}"
    try:
        response = ses_client.send_email(
            Destination={
                "ToAddresses": [os.getenv("ALEX")],
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
    artists_payload = {
        "tracks": [
            {
                "artist": "Steinza",
                "genres": {
                    "s": [
                        "0JQ5DAqbMKFy78wprEpAjl",
                        "0JQ5DAqbMKFKLfwjuJMoNC",
                        "0JQ5DAqbMKFCWjUTdzaG0e",
                    ],
                    "am": ["993289542", "1528193954", "1223622007", "6723904830"],
                },
            },
            {
                "artist": "Dave Blunts",
                "genres": {
                    "s": [
                        "0JQ5DAqbMKFQIL0AXnG5AK",
                        "0JQ5DAqbMKFQ00XGBls6ym",
                    ],
                    "am": ["1533338569", "993297962"],
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
    send_email_ses()
    return {"statusCode": 200, "body": "Lambdas invoked"}
