import json
import requests
import boto3
from io import BytesIO
from LambdaPage import LambdaPage
from mistune import markdown


template = """
<html>
<head>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


class Node:
    def __init__(self, **kwargs):
        self.__dict__ = {**self.__dict__, **kwargs}
        self.__kwargs__ = list(kwargs.keys())

    @property
    def defn(self):
        return {kw: self.__dict__[kw] for kw in self.__kwargs__}


class Entry(Node):
    def __init__(self, title, body):
        super().__init__(title=title, body=body)


class Asset(Node):
    def __init__(self, name, content_type, file_type):
        super().__init__(name=name, content_type=content_type,
                         file_type=file_type)


def retrieve_s3(s3_path):
    s3b = boto3.resource("s3").Bucket("musingsole")
    contents = BytesIO()
    s3b.download_fileobj(s3_path, contents)
    return contents


def retrieve_entry(entry_title):
    s3_path = f"entries/{entry_title}"
    content = retrieve_s3(s3_path)
    content.seek(0)
    return Entry(**json.loads(content.read()))


def retrieve_asset_defn(asset_name):
    s3_path = f"assets/{asset_name}.defn"
    content = retrieve_s3(s3_path)
    content.seek(0)
    return Asset(**json.loads(content.read()))


def get_entry(event):
    try:
        entry = retrieve_entry(event['pathParameters']['entry_title'])
        entry.body = markdown(entry.body)
        entry_page = template.format(**entry.defn)
        return 200, entry_page
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve entry"


def write_s3(s3_path, content):
    s3b = boto3.resource("s3").Bucket("musingsole")
    content_bytes = BytesIO(content.encode("utf-8"))
    s3b.upload_fileobj(content_bytes, s3_path)


def write_json(s3_path, content):
    write_s3(s3_path, json.dumps(content))


def write_entry(entry):
    s3_path = f"entries/{entry.title}"
    write_json(s3_path, entry.defn)


def write_asset(asset):
    s3_path = f"assets/{asset.name}.defn"
    write_json(s3_path, asset.defn)


def put_entry(event):
    print(event)


def retrieve_asset(asset_name):
    asset_defn = retrieve_s3(f"assets/{asset_name}.defn")
    asset_defn = retrieve_asset_defn(asset_name)
    content = retrieve_s3(f"assets/{asset_name}")
    content.seek(0)
    return asset_defn, content


def get_asset(event):
    try:
        asset_defn, content = retrieve_asset(event['pathParameters']['asset_name'])
        get_asset.content_type = asset_defn.content_type
        return 200, content.read()
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve asset"


def build_page():
    page = LambdaPage()
    page.add_endpoint(method='get', path='/assets/{asset_name}', func=get_asset, content_type="text/html")
    page.add_endpoint(method='get', path='/entry/{entry_title}', func=get_entry, content_type="text/html")
    page.add_endpoint(method='put', path='/entry/{entry_title}', func=put_entry)
    return page
    

def lambda_handler(event, context):
    print(f"Handling event: {event}")
    page = build_page()
    page.handle_request(event)


if __name__ == "__main__":
    page = build_page()
    page.start_local()
