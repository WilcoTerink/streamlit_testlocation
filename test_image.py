from PIL import Image
import io
import json
# import base64

"""
Example of how to convert/decode an image stored in a JSON as latin1 back to a visible image
"""

f = open('mytext.json', 'r')

d = json.load(f)

imstring = d['features'][0]['properties']['picture']

#b = base64.b64decode(imstring)
i = imstring.encode('latin1')

img = Image.open(io.BytesIO(i))
img.show()