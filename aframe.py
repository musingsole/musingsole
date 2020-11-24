import content
import aframe_md_compiler


template = """
<html>
<head>
<script
  src="https://code.jquery.com/jquery-3.1.1.min.js"
  integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8="
  crossorigin="anonymous">
</script>
</style>
<title>Occultronic Provisions</title>
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


def get_aframe_client(event):
    print("Getting AFRAME client")
    try:
        entry = content.retrieve_entry("2020-10-07 Trivialized Nickel and Copper Plating")
        scene = entry.to_scene()
        return 200, template.format(scene=scene)
    except Exception:
        from traceback import format_exc
        print(format_exc())
        return 504, "Failed to retrieve client"
