import base64
import os
import io
import uuid
import shutil
import pathlib
import streamlit as st
from PIL import Image
import gemini_experimental  # Import our Gemini module
import utils  # Import our utility module
import video_generation  # Import our video generation module

# Load environment variables - make it optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    # If dotenv fails or .env doesn't exist, that's okay
    pass

gemini_api_key = os.environ.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("GEMINI_API_KEY environment variable is not set!")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Gemini Image Chat",
    page_icon="🖼️",
    layout="wide"
)

# Create temp directory in the root folder for storing generated files
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = utils.ensure_temp_dir()

# Initialize session state for chat history and images
if "messages" not in st.session_state:
    st.session_state.messages = []

if "images" not in st.session_state:
    st.session_state.images = []

if "generated_images" not in st.session_state:
    st.session_state.generated_images = []

if "video_generation_state" not in st.session_state:
    st.session_state.video_generation_state = video_generation.reset_video_state()

def save_binary_file(data, mime_type):
    """Save binary data to a file with a unique name based on mime type in the temp directory"""
    return utils.save_binary_file(data, mime_type, st.session_state.temp_dir)

def generate_response(prompt):
    """Generate a response from Gemini model using our module"""
    # Call the function from our module
    return gemini_experimental.generate_response(
        gemini_api_key=gemini_api_key,
        prompt=prompt,
        messages=st.session_state.messages,
        images=st.session_state.images
    )


# App UI
st.title("Gemini Image Chat")
st.markdown("Upload images and chat with Gemini about them. Gemini can generate both text and images in response.")

# Sidebar for image upload and management
with st.sidebar:
    st.header("Upload & Manage Images")
    
    # Image uploader - with multiple file support
    uploaded_files = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        # Process all uploaded images
        for uploaded_file in uploaded_files:
            # Check if image with same name already exists to prevent duplicates
            if not utils.is_duplicate_image(uploaded_file.name, st.session_state.images):
                img_data = utils.process_uploaded_image(uploaded_file)
                st.session_state.images.append(img_data)
    
    # Display and manage uploaded images
    if st.session_state.images:
        st.subheader(f"Your Images ({len(st.session_state.images)})")
        
        # Create columns for the gallery
        cols = st.columns(2)
        
        for i, img_data in enumerate(st.session_state.images):
            col_idx = i % 2
            with cols[col_idx]:
                # Load image from bytes
                img = Image.open(io.BytesIO(img_data["data"]))
                
                # Display image with caption
                st.image(img, caption=f"{i+1}. {img_data['name']}", use_container_width=True, width=300)
                
                # Remove button
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.images.pop(i)
                    # No need to reset images_sent flag anymore
                    st.rerun()
                
    # Clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            # No need to reset images_sent flag anymore
            st.session_state.generated_images = []  # Also clear generated images
            st.rerun()
            

# Main content area with tabs
tab1, tab2 = st.tabs(["Image Chat", "Video Generation"])

with tab1:
    # Display chat messages
    st.header("Chat")
    
    # Create a container for the chat messages
    chat_container = st.container()
    
    # Create a container for the input at the bottom
    input_container = st.container()
    
    # Display chat messages in the chat container first
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # If message has images and we want to show them
                if "images" in message and message["images"]:
                    # Create a horizontal layout for images
                    image_cols = st.columns(min(len(message["images"]), 4))
                    
                    for idx, img_idx in enumerate(message["images"]):
                        col_idx = idx % min(len(message["images"]), 4)
                        with image_cols[col_idx]:
                            img_data = st.session_state.images[img_idx]
                            img = Image.open(io.BytesIO(img_data["data"]))
                            st.image(img, caption=f"{img_data['name']}", width=150)
                    
                    # Add a note about the images
                    st.caption(f"Message included {len(message['images'])} images")
                elif "images" in message and message["images"]:
                    # Just show a note about the images
                    st.caption(f"Message included {len(message['images'])} images")
                
                # Display text content
                if isinstance(message["content"], str):
                    # Text message
                    st.markdown(message["content"])
                else:
                    # Image message from model - use stored file path if available
                    if "file_path" not in message:
                        # Only save the file if we haven't saved it before
                        message["file_path"] = save_binary_file(message["content"], message["mime_type"])
                    
                    st.image(message["file_path"], caption="Generated Image", width=300)
                    
                    # Store the generated image for video generation (only if not already stored)
                    if message["role"] == "assistant" and not isinstance(message["content"], str):
                        # Add to generated images if not already there
                        if not utils.is_duplicate_generated_image(message["content"], st.session_state.generated_images):
                            st.session_state.generated_images.append({
                                "name": os.path.basename(message["file_path"]),
                                "data": message["content"],
                                "mime_type": message["mime_type"],
                                "file_path": message["file_path"]
                            })
    
    # Handle chat input (placed at the bottom but processed after displaying messages)
    with input_container:
        if prompt := st.chat_input("Message Gemini..."):
            # Create a list of image indices to include with the message
            image_indices = list(range(len(st.session_state.images)))
            
            # Add user message to chat history with all images (for display purposes)
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "images": image_indices if image_indices else None
            })
            
            # Get response from Gemini
            with st.spinner("Gemini is thinking..."):
                # Send images only if this is the first message
                response_text, response_image, response_mime_type = generate_response(
                    prompt
                )
                
                # Add text response to chat history if there is one
                if response_text:
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Add image response to chat history if there is one
                if response_image:
                    # Save the image immediately and store the path
                    file_name = save_binary_file(response_image, response_mime_type)
                    
                    # Add to chat history with file path stored
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response_image,
                        "mime_type": response_mime_type,
                        "file_path": file_name
                    })
                    
                    # Store the generated image for video generation
                    st.session_state.generated_images.append({
                        "name": os.path.basename(file_name),
                        "data": response_image,
                        "mime_type": response_mime_type,
                        "file_path": file_name
                    })
            
            # Rerun the app to display the new messages
            st.rerun()

with tab2:
    st.header("Video Generation from Gemini Images")
    st.markdown("Generate videos from images that Gemini has created during your conversation.")
    
    if not st.session_state.generated_images:
        st.info("No images have been generated by Gemini yet. Chat with Gemini and ask it to generate images first.")
    else:
        st.subheader(f"Generated Images ({len(st.session_state.generated_images)})")
        
        # Create a grid for the generated images
        cols = st.columns(3)
        
        for i, img_data in enumerate(st.session_state.generated_images):
            col_idx = i % 3
            with cols[col_idx]:
                # Display image
                st.image(img_data["file_path"], caption=f"Image {i+1}: {img_data['name']}", use_container_width=True)
                
                # Select button
                if st.button("Select for Video", key=f"select_for_video_{i}"):
                    st.session_state.video_generation_state["selected_image_idx"] = i
                    st.rerun()
        
        # Video generation UI
        if st.session_state.video_generation_state["selected_image_idx"] is not None:
            st.divider()
            st.subheader("Generate Video")
            
            # Get the selected image
            img_idx = st.session_state.video_generation_state["selected_image_idx"]
            img_data = st.session_state.generated_images[img_idx]
            
            # Display the selected image
            st.image(img_data["file_path"], caption=f"Selected image: {img_data['name']}", width=300)
            
            # Prompt input
            prompt = st.text_input("Enter a prompt for the video:", 
                                value=st.session_state.video_generation_state["prompt"],
                                key="video_prompt",
                                help="Describe what action or movement you want to see in the video")
            
            # Store the prompt in session state
            st.session_state.video_generation_state["prompt"] = prompt
            
            # Generate button
            generate_col, cancel_col = st.columns([1, 1])
            
            with generate_col:
                if st.button("Generate Video", key="generate_video_btn"):
                    if prompt:
                        with st.spinner("Generating video... This may take a minute or two."):
                            st.session_state.video_generation_state["generating"] = True
                            
                            try:
                                # Generate the video using our module
                                video_path = video_generation.generate_video(
                                    img_data["data"],
                                    prompt,
                                    st.session_state.temp_dir
                                )
                                
                                # Store the video path in session state
                                st.session_state.video_generation_state["video_path"] = video_path
                                st.session_state.video_generation_state["generating"] = False
                                
                                # Force a rerun to display the video
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating video: {str(e)}")
                                st.session_state.video_generation_state["generating"] = False
                    else:
                        st.warning("Please enter a prompt for the video.")
            
            with cancel_col:
                if st.button("Cancel", key="cancel_video_btn"):
                    st.session_state.video_generation_state = video_generation.reset_video_state()
                    st.rerun()
            
            # Display the generated video if available
            if st.session_state.video_generation_state["video_path"]:
                video_path = st.session_state.video_generation_state["video_path"]
                
                st.divider()
                st.subheader("Generated Video")
                
                # Use columns to control video width - height auto-scales to maintain aspect ratio
                col1, col2, col3 = st.columns([1, 1, 3])
                with col2:
                    video_file = open(video_path, 'rb')
                    video_bytes = video_file.read()
                    st.video(video_bytes)