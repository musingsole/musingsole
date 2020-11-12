from LambdaPage import LambdaPage
from markdown import markdown as md_to_html
from urllib.parse import unquote as url_decode

import content
from aframe import get_aframe_entry


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
        entry = content.retrieve_entry(entry_title)        
        entry.body = content.replace_asset_links(entry.body)
        entry.body = md_to_html(entry.body,
            extensions=['extra', 'toc', 'markdown_checklist.extension', 'nl2br'])
        entry_page = template.format(**entry.defn)
        return 200, entry_page
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve entry"



def build_page():
    page = LambdaPage()
    page.add_endpoint(method='get', path='/entry/{entry_title}', func=get_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/', func=get_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/aframe', func=get_aframe_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/aframe/{entry_title}', func=get_aframe_entry, content_type="text/html")
    return page


def lambda_handler(event, context):
    print(f"Handling event: {event}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
