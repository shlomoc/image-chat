import os
import uuid
import streamlit as st
import replicate
import tempfile
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_video(image_data, prompt, temp_dir):
    """Generate a video from an image using the WAN-2 model via Replicate
    
    Args:
        image_data (bytes): Binary image data
        prompt (str): Text prompt describing the desired video
        temp_dir (str): Directory to save the video in
        
    Returns:
        str: Path to the generated video file
        
    Raises:
        Exception: If video generation fails
    """
    # Get the API key
    replicate_api_key = os.environ.get("REPLICATE_API_KEY")
    if not replicate_api_key:
        raise Exception("REPLICATE_API_KEY not found in environment variables")
    
    # Generate a unique filename for the video
    video_filename = f"video_{uuid.uuid4()}.mp4"
    video_path = os.path.join(temp_dir, video_filename)
    
    try:
        # Convert image data to base64 for API consumption
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Create authenticated client
        client = replicate.Client(api_token=replicate_api_key)
        
        # Call Replicate API to generate the video
        output = client.run(
            "wavespeedai/wan-2.1-i2v-480p",
            input={
                "image": f"data:image/jpeg;base64,{image_base64}",
                "prompt": prompt
            }
        )
        
        # Download the video from the output URL
        with open(video_path, "wb") as file:
            file.write(output.read())
            
        return video_path
    
    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")

def generate_video_from_text(prompt, temp_dir):
    """Generate a video from a text prompt using the Google Veo-3 model via Replicate.

    Args:
        prompt (str): Text prompt describing the desired video.
        temp_dir (str): Directory to save the video in.

    Returns:
        str: Path to the generated video file.

    Raises:
        Exception: If video generation fails.
    """
    replicate_api_key = os.environ.get("REPLICATE_API_KEY")
    if not replicate_api_key:
        raise Exception("REPLICATE_API_KEY not found in environment variables")

    video_filename = f"video_text_{uuid.uuid4()}.mp4"
    video_path = os.path.join(temp_dir, video_filename)

    try:
        client = replicate.Client(api_token=replicate_api_key)

        # Call Replicate API to generate the video using google/veo-3
        # This model is expected to return a file-like object directly
        output = client.run(
            "google/veo-3",
            input={"prompt": prompt}
        )

        # Write the video content to the file
        # Ensure 'output' has a 'read' method as expected for file-like objects from Replicate
        if not hasattr(output, 'read'):
            raise Exception(f"Replicate API for google/veo-3 did not return a readable object. Received: {type(output)}")

        with open(video_path, "wb") as file:
            file.write(output.read())
            
        return video_path

    # Removed requests.exceptions.RequestException as we are no longer making a separate HTTP request for download
    except Exception as e:
        error_message = str(e)
        # Avoid re-wrapping common or specific errors
        if "REPLICATE_API_KEY not found" in error_message or \
           error_message.lower().startswith("video generation failed:") or \
           error_message.lower().startswith("replicate api error:") or \
           error_message.lower().startswith("replicate api did not return a valid video url") or \
           error_message.lower().startswith("failed to download video from"):
            raise
        else:
            raise Exception(f"Text-to-video generation failed: {error_message}")


def reset_video_state():
    """Reset the video generation state
    
    Returns:
        dict: Reset video generation state
    """
    return {
        "selected_image_idx": None,
        "prompt": "",
        "generating": False,
        "video_path": None
    } 

