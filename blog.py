import re
import json
import requests
import boto3
from io import BytesIO
from LambdaPage import LambdaPage
from mistune import markdown
import base64


template = """
<html>
<head>
<title>{title}</title>
</head>
<body>
<a href="/">Return to Root</a><br>
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
    print(f"Retrieving {s3_path}")
    s3b = boto3.resource("s3").Bucket("musingsole")
    contents = BytesIO()
    s3b.download_fileobj(s3_path, contents)
    return contents


def list_entries():
    print("Retrieving available entries")
    s3c = boto3.client("s3")
    resp = s3c.list_objects_v2(
        Bucket='musingsole',
        Prefix='entry/')
    assert resp['IsTruncated'] == False
    return [entry['Key'][len("entry/"):] for entry in resp['Contents']]


def retrieve_entry(entry_title):
    print(f"Retrieving {entry_title}")
    s3_path = f"entry/{entry_title}"
    content = retrieve_s3(s3_path)
    content.seek(0)
    return Entry(**json.loads(content.read()))


def retrieve_asset_defn(asset_name):
    print(f"Retrieving {asset_name}")
    s3_path = f"asset/{asset_name}.defn"
    content = retrieve_s3(s3_path)
    content.seek(0)
    return Asset(**json.loads(content.read()))


def retrieve_asset_link(asset_name):
    print("Retrieving Asset Link")
    s3_path = f"asset/{asset_name}"
    s3c = boto3.client("s3")
    url = s3c.generate_presigned_url('get_object',
                                     ExpiresIn=1800,
                                     Params={'Bucket': 'musingsole',
                                             'Key': s3_path})
    return url


def replace_asset_links(body):
    pattern = "{asset\.([\w\.]*)}"
    for asset in set(re.findall(pattern, body)):
        asset_link = retrieve_asset_link(asset)
        body = body.replace(f"{{asset.{asset}}}", asset_link)
    return body


def get_entry(event):
    print("Getting entry")
    try:
        try:
            entry_title = event['pathParameters']['entry_title']
        except Exception:
            entry_title = 'root'
        entry = retrieve_entry(entry_title)        
        entry.body = replace_asset_links(entry.body)
        print(entry.body)
        entry.body = markdown(entry.body).replace("\n", "<br>")
        entry_page = template.format(**entry.defn)
        return 200, entry_page
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve entry"


def write_s3(s3_path, content):
    print(f"Writting {s3_path}")
    s3b = boto3.resource("s3").Bucket("musingsole")
    content_bytes = BytesIO(content.encode("utf-8"))
    s3b.upload_fileobj(content_bytes, s3_path)


def write_json(s3_path, content):
    print("Writing JSON at {s3_path}")
    write_s3(s3_path, json.dumps(content))


def write_entry(entry):
    print(f"Writing entry {entry.title}")
    s3_path = f"entry/{entry.title}"
    write_json(s3_path, entry.defn)


def build_root():
    print("Building root")
    template = "# Welcome to the Project Root\n![logo]({{asset.logo.png}})\n{body}"
    body = ""
    for entry in [entry for entry in list_entries()
                  if entry not in ['', 'root']]:
        body += f"[{entry}](entry/{entry})"
    write_entry(Entry("root", template.format(body=body)))


def write_asset(asset):
    print(f"Writing asset {asset.name} definition")
    s3_path = f"asset/{asset.name}.defn"
    write_json(s3_path, asset.defn)


def retrieve_asset(asset_name):
    print("Retrieving {asset_name}")
    asset_defn = retrieve_s3(f"asset/{asset_name}.defn")
    asset_defn = retrieve_asset_defn(asset_name)
    content = retrieve_s3(f"asset/{asset_name}")
    content.seek(0)
    return asset_defn, content


def get_asset(event):
    print("Getting asset")
    try:
        asset_defn, content = retrieve_asset(event['pathParameters']['asset_name'])
        get_asset.content_type = asset_defn.content_type
        content = content.read()
        content = f"data:image/png;base64,{base64.b64encode(content).decode('utf-8')}"
        print(content)
        return 200, content
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve asset"


def build_page():
    page = LambdaPage()
    page.add_endpoint(method='get', path='/asset/{asset_name}', func=get_asset, content_type="text/html")
    page.add_endpoint(method='get', path='/entry/{entry_title}', func=get_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/', func=get_entry, content_type="text/html")
    return page


def put_entry():
    pass
    

def lambda_handler(event, context):
    print(f"Handling event: {event}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
