import os
import pathlib
from google import genai
from google.genai import types

def generate_response(gemini_api_key, prompt, messages=None, images=None):
    """Generate a response from Gemini model
    
    Args:
        gemini_api_key (str): The API key for Gemini
        prompt (str): The text prompt to send to Gemini
        messages (list, optional): Previous chat history
        images (list, optional): List of image data dictionaries
        helicone_api_key (str, optional): API key for Helicone monitoring
        
    Returns:
        tuple: (response_text, response_image, response_mime_type)
    """
    client = genai.Client(api_key=gemini_api_key)
    model = "gemini-2.0-flash-preview-image-generation"
    
    # Prepare content parts
    parts = []
    
    # Add images to every message if we have images
    if images and len(messages) == 1:
        for img_data in images:
            parts.append(
                types.Part.from_bytes(
                    data=img_data["data"],
                    mime_type="image/jpeg"
                )
            )
    
    # Add text prompt
    parts.append(types.Part.from_text(text=prompt))
    
    # Create content
    contents = [
        types.Content(
            role="user",
            parts=parts,
        )
    ]
    
    # Add chat history if provided
    if messages:
        for message in messages:
            if message["role"] == "user":
                # For user messages, we only include text after the first message
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=message["content"])]
                    )
                )
            else:
                # For model responses, we need to handle both text and images
                if isinstance(message["content"], str):
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=message["content"])]
                        )
                    )
                else:
                    # This is an image response
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part.from_bytes(
                                    data=message["content"],
                                    mime_type=message["mime_type"]
                                )
                            ]
                        )
                    )
    
    # Configure generation
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=[
            "text",
            "image",
        ],
        response_mime_type="text/plain",
    )
    
    # Stream response
    response_text = ""
    response_image = None
    response_mime_type = None
    
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
            
        if chunk.candidates[0].content.parts[0].inline_data:
            # This is an image response
            response_image = chunk.candidates[0].content.parts[0].inline_data.data
            response_mime_type = chunk.candidates[0].content.parts[0].inline_data.mime_type
        else:
            # This is a text response
            response_text += chunk.text
    
    return response_text, response_image, response_mime_type 