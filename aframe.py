import content
import aframe_md_compiler


with open("aframe.html", "r") as fh:
    template = fh.read()


def get_aframe_client(event):
    print("Getting AFRAME client")
    try:
        entry = content.retrieve_entry("2020-10-07 Trivialized Nickel and Copper Plating")
        scene = entry.to_scene()
        get_aframe_client.headers['Access-Control--Allow-Origin'] = '*'
        get_aframe_client.headers['Access-Control--Allow-Credentials'] = True
        return 200, aframe_md_compiler.template_keyword_replace(template, scene=scene)
    except Exception:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve client"
