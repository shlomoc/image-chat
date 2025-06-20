import os
import streamlit as st
import gemini_experimental  # Import our Gemini module
import utils  # Import our utility module
import video_generation  # Import our video generation module
import ui_components      # Import our new UI components module

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

# Session state for text-to-video generation
if "text_video_prompt" not in st.session_state:
    st.session_state.text_video_prompt = ""
if "text_video_path" not in st.session_state:
    st.session_state.text_video_path = None
if "text_video_error" not in st.session_state:
    st.session_state.text_video_error = None
if "text_video_generating" not in st.session_state:
    st.session_state.text_video_generating = False

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
st.title("Image Chat")

# Sidebar for image upload and management
with st.sidebar:
    ui_components.render_sidebar(st.session_state)
            

# Main content area with tabs
tab1, tab2 = st.tabs(["Image Chat", "Video Generation"])

with tab1:
    st.header("Chat")
    chat_container = st.container()
    input_container = st.container()
    ui_components.render_chat_tab(
        st_session_state=st.session_state,
        gemini_api_key_param=gemini_api_key, 
        save_binary_file_func=save_binary_file, 
        generate_response_func=generate_response, 
        chat_container=chat_container,
        input_container=input_container
    )

with tab2:
    ui_components.render_video_generation_tab(
        st_session_state=st.session_state, 
        video_gen_module=video_generation, 
        temp_dir=st.session_state.temp_dir
    )