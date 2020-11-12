import json
import re
import s3


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


def list_entries():
    print("Retrieving available entries")
    resp = s3.list_contents("entry/")
    assert resp['IsTruncated'] == False
    return [entry['Key'][len("entry/"):] for entry in resp['Contents']]


def retrieve_entry(entry_title):
    print(f"Retrieving {entry_title}")
    return Entry(**s3.retrieve_json(f"entry/{entry_title}"))


def retrieve_asset_link(asset_name):
    print("Retrieving Asset Link")
    return s3.retrieve_presigned_url(f"asset/{asset_name}")


def replace_s3_urls(body):
    url = "https://musingsole.s3.amazonaws.com/asset/"
    pattern = f"{url}(.*(\.png|\.jpg))"
    for asset_name, asset_file_type in set(re.findall(pattern, body)):
        body = body.replace(f"{url}{asset_name}", f"{{{{asset.{asset_name}}}}}")  
    return body


def replace_asset_links(body):
    pattern = "{asset\.([\w\.]*)}"
    for asset in set(re.findall(pattern, body)):
        asset_link = retrieve_asset_link(asset)
        body = body.replace(f"{{asset.{asset}}}", asset_link)
    return body


def build_root():
    print("Building root")
    template = "# Welcome to the Project Root\n##![logo]({{asset.logo.png}})\n{body}"
    body = ""
    for entry in [entry for entry in list_entries()
                  if entry not in ['', 'root']]:
        body += f"* [{entry}](entry/{entry})\n"
    write_entry(Entry("root", template.format(body=body)))
