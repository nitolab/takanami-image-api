from logging import getLogger, StreamHandler, INFO
import boto3
from PIL import Image, ImageFilter
import io
import uuid
import os
import json

logger = getLogger(__name__)
logger.setLevel(INFO)

ContentTypes = {
    'jpeg': "image/jpeg",
    'jpg': "image/jpeg",
    'png': "image/png",
    'gif': "image/gif",
}

s3 = boto3.client('s3')


BASE = 'i'

def resize(original, size=(1024, 1024)):
    s = 't' if original.width <= original.height else 'y'
    if s == 't':
        size = (original.width*1024//original.height, 1024)
    else:
        size = (1024, original.height*1024//original.width)
    return original.resize(size)

def run(bucket, key, sizes, typ=None, id=None, outputkey=None):
    b = s3.get_object(
        Bucket=bucket,
        Key=key
    )
    logger.info("get image s3://%s/%s, %sbytes", bucket, key, b['ContentLength'])

    org = io.BytesIO()
    original = Image.open(b['Body'])
    original.save(org, quality=100, format=original.format)
    org.seek(0)

    if outputkey == None:
        outputkey = uuid.uuid1().hex

    k = os.path.join(BASE, outputkey)
    logger.info("key: %s", outputkey)

    s3.put_object(
        Body=org,
        Bucket=bucket,
        Key=f"{k}/{outputkey}",
        ContentType=ContentTypes[original.format.lower()],
        CacheControl='public, max-age=604800'
    )
    del(org)

    result = {
        "success": False,
        "id": id,
        "key": outputkey,
        "original": key,
        "type": typ,
        "keys": {
        }
    }

    for t in sizes:
        m = resize(original, t['size'])
        output = io.BytesIO()
        m.save(output, quality=100, format=original.format)
        output.seek(0)
        dest = "{base}/{key}_{suffix}".format(base=k, key=outputkey, suffix=t['suffix'])
        s3.put_object(
            Body=output,
            Bucket=bucket,
            Key=dest,
            CacheControl='public, max-age=604800',
            ContentType=ContentTypes[original.format.lower()]
        )
        logger.info("save: %s", dest)
        del(output)
        del(m)
        result['keys'][t['suffix']] = {
            "key": dest
        }

    result['success'] = True

    rs = io.StringIO()
    json.dump(result, fp=rs)
    rs.seek(0)

    s3.put_object(
        Body=rs.read(),
        Bucket=bucket,
        Key="{base}/info.json".format(base=k),
        ContentType="application/json"
    )

    logger.info("done")
    return result

def lambda_handler(event, context):
    return run(**event)
