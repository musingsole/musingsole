import re
from urllib.parse import unquote as url_decode
from functools import partial

from markdown import markdown as md_to_html

import s3


class Node:
    def __init__(self, **kwargs):
        assert 'defn' not in kwargs
        self.__kwargs__ = list(kwargs.keys())
        for kw, value in kwargs.items():
            setattr(self, kw, value)

    @property
    def defn(self):
        return {kw: self.__dict__[kw] for kw in self.__kwargs__}


def list_entries():
    print("Retrieving available entries")
    return s3.list_contents("entry/")


def retrieve_entry(entry_title):
    print(f"Retrieving {entry_title}")
    return Entry(**s3.retrieve_json(f"entry/{entry_title}"))


def retrieve_asset_link(asset_name):
    print("Retrieving Asset Link")
    return s3.retrieve_presigned_url(f"asset/{asset_name}")


def replace_s3_urls(body):
    url = "https://musingsole.s3.amazonaws.com/asset/"
    pattern = fr"{url}(.*(\.png|\.jpg))"
    for asset_name, asset_file_type in set(re.findall(pattern, body)):
        body = body.replace(f"{url}{asset_name}", f"{{{{asset.{asset_name}}}}}")
    return body


def replace_asset_links(body):
    pattern = r"{asset\.([\w\.]*)}"
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


def write_entry(entry):
    print(f"Writing entry {entry.title}")
    s3_path = f"entry/{entry.title}"
    s3.write_json(s3_path, entry.defn)


def delete_entry(entry):
    print(f"Deleting entry {entry.title}")
    s3_path = f"entry/{entry.title}"
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
<body>
<a href="/">Return to Root</a><br>
{body}
</body>
</html>
"""


def get_entry(event):
    print("Getting entry")
    try:
        try:
            entry_title = url_decode(event['pathParameters']['entry_title'])
        except Exception:
            entry_title = 'root'
        entry = retrieve_entry(entry_title)
        entry.body = replace_asset_links(entry.body)
        entry.body = md_to_html(entry.body, extensions=['extra', 'toc', 'markdown_checklist.extension', 'nl2br'])
        entry_page = template.format(**entry.defn)
        return 200, entry_page
    except Exception:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve entry"


class Entry(Node):
    retrieve_entry = retrieve_entry
    write_entry = write_entry
    delete_entry = delete_entry

    def __init__(self, title, body):
        super().__init__(title=title, body=body)
        self.retrieve_entry = partial(retrieve_entry, entry_title=self.title)
        self.write_entry = partial(write_entry, entry=self)
        self.delete_entry = partial(delete_entry, entry=self)
