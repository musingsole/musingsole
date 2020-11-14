from functools import partial


def header(chunk):
    pass


def link(chunk):
    pass


def image(chunk):
    pass


def bullet(chunk):
    pass


def ordered_list(chunk):
    pass


def checkbox(chunk):
    pass


def horizontal_rule(chunk):
    pass


def text(chunk):
    pass


dispatch = {
    r"^#+ ": header,
    r"\[.*\]\(.*\)": link,
    r"!\[.*\]\(.*)": image,
    r"\s*[\*, \+, -] ": bullet,
    r"\s*\d\. ": ordered_list,
    r"\s*[\*, \+, -] \[[\s, X, x]\]": checkbox,
    r"^[\*, -]{3}": horizontal_rule,
    "default": text
}


def compile_md_to_aframe(md_string):
    scene = []
    for chunk in md_string.split("\n\n"):
        for pattern, handler in dispatch.items():
            if re.search(pattern, chunk):
                scene.append(handler(chunk))
