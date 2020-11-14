from markdown import markdown as md_to_html
from urllib.parse import unquote as url_decode

import s3
import content

template = """
<html>
<head>
<script
  src="https://code.jquery.com/jquery-3.1.1.min.js"
  integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8="
  crossorigin="anonymous">
</script>
</style>
<title>{title}</title>
<script src="https://aframe.io/releases/1.0.4/aframe.min.js"></script>
</head>
<body>
    <a-scene background="color: #0A0A0A">
        <a-plane position="0 0 -4" rotation="-90 0 0" width="4" height="4" color="#7BC8A4" shadow></a-plane>
        <a-box position="-1 0.5 -3" rotation="0 45 0" color="#4CC3D9" shadow></a-box>
        {scene}
    </a-scene>
</body>
</html>
"""


class AframeEntry(content.Node):
    def __init__(self, title, scene, **kwargs):
        super().__init__(title=title, scene=scene, **kwargs)


def retrieve_entry(entry_title):
    print(f"Retrieving {entry_title}")
    return AframeEntry(**s3.retrieve_json(f"aframe/{entry_title}"))


def get_aframe_entry(event):
    print("Getting AFRAME entry")
    try:
        try:
            entry_title = url_decode(event['pathParameters']['entry_title'])
        except Exception:
            entry_title = 'root'

        entry = retrieve_entry(entry_title)

        if 'body' in entry.defn:
            entry.body = content.replace_asset_links(entry.body)
            entry.body = md_to_html(entry.body,
                                    extensions=['extra', 'toc', 'markdown_checklist.extension', 'nl2br'])
        else:
            entry.body = ""

        entry_page = template.format(**entry.defn)
        return 200, entry_page
    except Exception:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve entry"


def write_entry(entry):
    print(f"Writing entry {entry.title}")
    s3_path = f"aframe/{entry.title}"
    s3.write_json(s3_path, entry.defn)


def delete_entry(entry):
    print(f"Deleting entry {entry.title}")
    s3_path = f"aframe/{entry.title}"
    s3.delete(s3_path)


def build_root():
    print("Building root")
    template = "# Welcome to the Project Root\n##![logo]({{asset.logo.png}})\n{body}"
    body = ""
    for entry in [entry for entry in list_entries()
                  if entry not in ['', 'root']]:
        body += f"* [{entry}](aframe/{entry})\n"
    write_entry(AframeEntry("root", template.format(body=body)))
