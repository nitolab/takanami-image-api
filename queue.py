from logging import getLogger, StreamHandler, INFO
import boto3
import json
import uuid
import os

FUNCTION = os.environ['ASYNC_FUNCTION']

def lambda_handler(event, context):
    return queue(**event)

def queue(bucket, key, sizes, typ=None, id=None):
    outputkey = uuid.uuid1().hex

    Payload = json.dumps({
        "bucket": bucket,
        "key": key,
        "sizes": sizes,
        "id": id,
        "typ": typ,
        "outputkey": uuid.uuid1().hex
    })

    boto3.client('lambda').invoke(
        FunctionName=FUNCTION,
        InvocationType='Event',
        Payload=Payload
    )

    return {
        "key": outputkey
    }

