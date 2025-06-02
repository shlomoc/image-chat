import os
import uuid
import io
from PIL import Image

def ensure_temp_dir(base_dir=None):
    """Create a temp directory if it doesn't exist
    
    Args:
        base_dir (str, optional): Base directory path. If None, uses current working directory.
        
    Returns:
        str: Path to the temp directory
    """
    if base_dir is None:
        base_dir = os.getcwd()
        
    temp_dir = os.path.join(base_dir, "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    return temp_dir

def save_binary_file(data, mime_type, temp_dir):
    """Save binary data to a file with a unique name based on mime type
    
    Args:
        data (bytes): Binary data to save
        mime_type (str): MIME type of the data (e.g., 'image/jpeg')
        temp_dir (str): Directory to save the file in
        
    Returns:
        str: Path to the saved file
    """
    extension = mime_type.split("/")[1]
    file_name = f"generated_{uuid.uuid4()}.{extension}"
    file_path = os.path.join(temp_dir, file_name)
    
    with open(file_path, "wb") as f:
        f.write(data)
    
    return file_path

def process_uploaded_image(uploaded_file):
    """Process an uploaded image file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: Dictionary with image data
    """
    image = Image.open(uploaded_file)
    
    # Convert to bytes for Gemini API
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=image.format or "JPEG")
    img_bytes = img_byte_arr.getvalue()
    
    return {
        "name": uploaded_file.name,
        "data": img_bytes,
        "format": image.format or "JPEG"
    }

def is_duplicate_image(image_name, existing_images):
    """Check if an image with the same name already exists
    
    Args:
        image_name (str): Name of the image to check
        existing_images (list): List of existing image dictionaries
        
    Returns:
        bool: True if the image already exists, False otherwise
    """
    for existing_img in existing_images:
        if existing_img["name"] == image_name:
            return True
    return False

def is_duplicate_generated_image(image_data, generated_images):
    """Check if an image with the same data already exists in generated images
    
    Args:
        image_data (bytes): Binary image data to check
        generated_images (list): List of existing generated image dictionaries
        
    Returns:
        bool: True if the image already exists, False otherwise
    """
    for img in generated_images:
        if img["data"] == image_data:
            return True
    return False


