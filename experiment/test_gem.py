from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import pathlib
from dotenv import load_dotenv
import os

load_dotenv()
gemini_api_key = os.environ.get("GEMINI_API_KEY")

client =genai.Client(
    api_key=gemini_api_key
)

contents = [
    types.Content(
        role="user",
        parts=[
            types.Part.from_text(text="""Generate an image of cat"""),
    ])
]

response = client.models.generate_content(
    model="models/gemini-2.0-flash-preview-image-generation",
    contents=contents,
    config=types.GenerateContentConfig(response_modalities=['Text', 'Image'])
)

for part in response.candidates[0].content.parts:
  if part.text is not None:
    print(part.text)
  elif part.inline_data is not None:
    image = Image.open(BytesIO(part.inline_data.data))
    image.save('generated_image.png') 

contents = [
    types.Content(
        role="user",
        parts=[
            types.Part.from_bytes(
                data=pathlib.Path("generated_image.png").read_bytes(),
                mime_type="image/png"
            ),
            types.Part.from_text(text="""Make this cat hair orange"""),
    ])
]

response = client.models.generate_content(
    model="models/gemini-2.0-flash-preview-image-generation",
    contents=contents,
    config=types.GenerateContentConfig(response_modalities=['Text', 'Image'])
)

for part in response.candidates[0].content.parts:
  if part.text is not None:
    print(part.text)
  elif part.inline_data is not None:
    image = Image.open(BytesIO(part.inline_data.data))
    image.save('generated_image_2.png') 
