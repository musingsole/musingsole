import re
import base64
from functools import partial
from PIL import Image
import content
import asset


class Parser:
    patterns = {
        "header": r"^(#+) (.*)",
        "link": r"\[(.*)\]\((.*)\)",
        "image_asset": r"!\[(.*)\]\(\{asset.(.*)\}\)",
        "image": r"!\[(.*)\]\((.*)\)",
        "paragraph": r".*"
    }

    def __init__(self, pattern, func):
        self.pattern = pattern
        self.func = func

    def parse(self, chunk):
        return re.search(self.pattern, chunk)

    def __call__(self, chunk):
        match = self.parse(chunk)
        if match:
            return self.func(chunk, match)
        else:
            return None, None


def template_keyword_replace(template, **kwargs):
    filled_template = template
    for key, value in kwargs.items():
        filled_template = filled_template.replace(f"{{{key}}}", str(value))
    return filled_template


def header(chunk, match):
    # header_level = len(match.group(1))
    print(f"HEADER CHUNK: {chunk}")
    header_level = len(match.group(1))
    wrap_count = 25 + header_level * 10
    height = 1.7 - 0.2 * header_level
    header_content = match.group(2)

    entity = """
    <a-entity position="{position}" class="header_{header_level}">
        <a-text value="{content}" color="green" align="center" width=10 wrap-count={wrap_count}></a-text>
        <a-entity geometry="primitive:box;width:10;height:{height};depth:0.1" material="color: yellow" position="0 0 -0.1"></a-entity>
    </a-entity>"""
    entity = partial(template_keyword_replace, template=entity, content=header_content,
                     header_level=header_level, wrap_count=wrap_count, height=height)

    return entity, (1, height, 0.1)


def parse_asset_link(chunk, match):
    print(f"IMAGE ASSET CHUNK: {chunk}")
    asset_name = match.group(2)
    asset_bytes = asset.retrieve_asset(asset_name)
    im = Image.open(asset_bytes)
    height = im.size[1] / 100
    width = im.size[0] / 100
    print(f"Height: {height}, Width: {width}")
    asset_bytes.seek(0)
    asset_b64 = base64.b64encode(asset_bytes.read())
    entity = """
    <a-entity position="{position}" class="image">
        <a-image position="0 -{hl2} 0" src="data:image/jpeg;base64,{asset_b64}", height={height} width={width}>
        <a-entity geometry="primitive:box;width:{width};height:{height};depth:0.1"
         material="color: navy" position="0 0 -0.1"></a-entity>
    </a-entity>"""
    geo = (width, height + 1, 0.1)
    print(geo)
    return partial(template_keyword_replace, template=entity,
                   asset_b64=asset_b64.decode("utf-8"),
                   height=height, width=width, hl2=height / 2), geo


def image(chunk, match):
    print(f"IMAGE CHUNK: {chunk}")
    image_url = match.group(2)
    entity = """
    <a-entity position="{position}" class="image">
        <a-image position="0 -50 0" src="{image_url}", height=100 width=100>
        <a-entity geometry="primitive:box;width:100;height:100;depth:0.1"
         material="color: navy" position="0 0 -0.1"></a-entity>
    </a-entity>"""
    geo = (100, 100 + 1, 0.1)
    print(geo)
    return partial(template_keyword_replace, template=entity,
                   image_url=image_url), geo


def paragraph(chunk, match):
    print(f"PARAGRAPH CHUNK: {chunk}")
    height = max(len(chunk) / 580, 1)
    entity = """
    <a-entity position="{position}" class="paragraph">
        <a-text position="-4.6 0 0" value="{chunk}" color="white" align="left"
         width=9.2 wrap-count=100></a-text>
        <a-entity geometry="primitive:box;width:9.6;height:{height};depth:0.1"
         material="color: navy" position="0 0 -0.1"></a-entity>
    </a-entity>"""
    return partial(template_keyword_replace, template=entity,
                   chunk=chunk, height=height), (1, 1.25, 0.1)


dispatch = [
    Parser(Parser.patterns['image_asset'], parse_asset_link),
    Parser(Parser.patterns['image'], image),
    Parser(Parser.patterns['header'], header),
    Parser(Parser.patterns['paragraph'], paragraph)
]


def parse(chunk):
    for parser in dispatch:
        parsed, geo = parser(chunk)
        if parsed is not None:
            return parsed, geo


def parse_md(md, initial_position=None, hbuff=0.1):
    position = initial_position if initial_position is not None else [0, 0, 0]
    for chunk in md.split("\n"):
        if chunk == "":
            continue
        parsed, geo = parse(chunk)
        aframe_entity = parsed(position=", ".join([str(p) for p in position]))
        position[1] -= (geo[1] + hbuff)
        yield aframe_entity


def entry_to_scene(entry):
    scene = list(parse_md(entry.body))
    scene = "\n".join(scene)
    scene = f"<a-entity id='md' position='0 3 -3'>{scene}</a-entity>"
    return scene


setattr(content.Entry, 'to_scene', entry_to_scene)


# def link(chunk):
#     pass


# def bullet(chunk):
#     pass


# def ordered_list(chunk):
#     pass


# def checkbox(chunk):
#     pass


# def horizontal_rule(chunk):
#     pass
