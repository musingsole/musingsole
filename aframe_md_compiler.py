import re
from functools import partial
from LambdaPage import LambdaPage
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
        <a-entity camera="active: true" look-controls wasd-controls="fly: true; acceleration: 200" position="0 1.6 0"></a-entity>
        {scene}
    </a-scene>
</body>
</html>
"""


class Parser:
    def __init__(self, pattern, func):
        self.pattern = pattern
        self.func = func

    def parse(self, chunk):
        return re.match(self.pattern, chunk)

    def __call__(self, chunk):
        match = re.match(self.pattern, chunk)
        if match:
            return self.func(chunk, match)
        else:
            return None, None


def header(chunk, match):
    # header_level = len(match.group(1))
    print(f"HEADER CHUNK: {chunk}")
    header_level = (1 / len(match.group(1))) * 10
    header_content = match.group(2)

    entity = """
    <a-text position="{position}" value="{content}" color="green" align="center" width=5 height=2 wrap-count=15>
        <a-entity geometry="primitive:box;width:5;height:2;depth:0.1" material="color: yellow" position="0 0 -0.1"></a-entity>
    </a-text>"""
    entity = partial(entity.format, content=header_content, header_level=header_level, hl2=header_level / 2 - 0.5)
    # TODO: calculate height
    return entity, (1, 2, 0.1)


def paragraph(chunk, match):
    print(f"PARAGRAPH CHUNK: {chunk}")
    height = len(chunk) / 40
    entity = """
    <a-text position="{position}" value="{chunk}" color="white" align="left" width=5 height={height} wrap-count=50>
        <a-entity geometry="primitive:box;width:6;height:{height};depth:0.1" material="color: navy" position="2.2 0 -0.05"></a-entity>
        <a-entity geometry="primitive:box;width:5;height:{height};depth:0.1" material="color: yellow" position="0 0 -0.1"></a-entity>
    </a-text>"""
    return partial(entity.format, chunk=chunk, height=height), (1, height, 0.1)


dispatch = [
    Parser(r"^(#+) (.*)", header),
    Parser(r"(.*)", paragraph)
]


def parse(chunk):
    for parser in dispatch:
        parsed, geo = parser(chunk)
        if parsed is not None:
            return parsed, geo


def parse_md(md, initial_position=[0, 0, 0]):
    position = initial_position
    for chunk in md.split("\n"):
        parsed, geo = parse(chunk)
        aframe_entity = parsed(position=", ".join([str(p) for p in position]))
        position[1] -= geo[1]
        yield aframe_entity


def entry_to_scene(entry):
    scene = list(parse_md(entry.body))
    scene = "\n".join(scene)
    scene = f"<a-entity id='md' position='-2 3 -3'>{scene}</a-entity>"
    return scene


setattr(content.Entry, 'to_scene', entry_to_scene)


# def link(chunk):
#     pass


# def image(chunk):
#     pass


# def bullet(chunk):
#     pass


# def ordered_list(chunk):
#     pass


# def checkbox(chunk):
#     pass


# def horizontal_rule(chunk):
#     pass


# def text(chunk):
#     pass


# dispatch = {
#     header.pattern: header,
#     r"\[.*\]\(.*\)": link,
#     r"!\[.*\]\(.*)": image,
#     r"\s*[\*, \+, -] ": bullet,
#     r"\s*\d\. ": ordered_list,
#     r"\s*[\*, \+, -] \[[\s, X, x]\]": checkbox,
#     r"^[\*, -]{3}": horizontal_rule,
#     "default": text
# }


# def match_and_dispatch(chunk):
#     for pattern, func in dispatch.items():
#         if pattern == "default" or re.match(pattern, chunk):
#             return func(chunk)
#     raise Exception("Unmatched")


# def compile_md_to_aframe(md_string):
#     scene = []
#     for chunk in md_string.split("\n\n"):
#         for pattern, handler in dispatch.items():
#             if re.search(pattern, chunk):
#                 scene.append(handler(chunk))
