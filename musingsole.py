from LambdaPage import LambdaPage
from markdown import markdown as md_to_html
from urllib.parse import unquote as url_decode

from content import get_entry as get_md_entry
from aframe import get_aframe_client


def build_page():
    page = LambdaPage()
    page.add_endpoint(method='get', path='/entry', func=get_md_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/entry/{entry_title}', func=get_md_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/', func=get_md_entry, content_type="text/html")
    page.add_endpoint(method='get', path='/aframe', func=get_aframe_client, content_type="text/html")
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
