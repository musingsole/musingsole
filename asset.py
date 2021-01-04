import base64
from urllib.parse import unquote as url_decode

import s3


def list_assets():
    print("Retrieving available assets")
    return [asset for asset in s3.list_contents("asset/")]


def retrieve_asset(asset_name):
    print(f"Retrieving {asset_name}")
    return s3.retrieve(f"asset/{asset_name}")


def delete_asset(asset):
    print(f"Deleting asset {asset.name}")
    s3_path = f"asset/{asset.name}"
    s3.delete(s3_path)


template = """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://igoradamenko.github.io/awsm.css/css/awsm.min.css">
<script
  src="https://code.jquery.com/jquery-3.1.1.min.js"
  integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8="
  crossorigin="anonymous">
</script>
</style>
<title>{title}</title>
</head>
<body
>{body}
</body>
</html>
"""


def get_asset(event):
    print("Getting asset")
    try:
        asset_name = url_decode(event['pathParameters']['asset_name'])
        content_type = event['queryStringParameters'].get('content_type', 'image/png')
        get_asset.headers['content-type'] = content_type
        asset = retrieve_asset(asset_name)
        asset.seek(0)
        return 200, base64.b64encode(asset.read())
    except Exception:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve asset"
