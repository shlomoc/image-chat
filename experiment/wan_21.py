import base64
import os

from dotenv import load_dotenv
import replicate

load_dotenv()
replicate_api_key = os.environ.get("REPLICATE_API_KEY")

# Set the API key for replicate client
replicate.Client(api_token=replicate_api_key)

def generate_video_from_local_image(image_path, prompt, output_path="output.mp4"):
    """
    Generate a video from a local image using Replicate's WAN-2.1 model
    
    Args:
        image_path (str): Path to the local image file
        prompt (str): Text prompt describing the video to generate
        output_path (str): Path where the output video will be saved
        
    Returns:
        str: Path to the generated video file
    """
    # Read the image file and encode it as base64
    with open(image_path, "rb") as image_file:
        # Convert the image to base64 for API consumption
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
    # Prepare the input for the model
    input = {
        "image": f"data:image/jpeg;base64,{image_data}",
        "prompt": prompt
    }
    
    # Run the model with authenticated client
    client = replicate.Client(api_token=replicate_api_key)
    output = client.run(
        "wavespeedai/wan-2.1-i2v-480p",
        input=input
    )
    
    # Save the output video
    with open(output_path, "wb") as file:
        file.write(output.read())
    
    return output_path

generate_video_from_local_image("generated_image.png", "Cat is looking around")