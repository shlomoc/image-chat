import streamlit as st
import io
from PIL import Image
import utils # Assuming utils.py is in the same directory
import os # For os.path.basename if used within moved code, though not directly in sidebar snippet

def render_sidebar(st_session_state):
    """Renders the sidebar UI for image upload and management."""
    st.header("Upload & Manage Images")
    
    # Image uploader - with multiple file support
    uploaded_files = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        # Process all uploaded images
        for uploaded_file in uploaded_files:
            # Check if image with same name already exists to prevent duplicates
            if not utils.is_duplicate_image(uploaded_file.name, st_session_state.images):
                img_data = utils.process_uploaded_image(uploaded_file)
                st_session_state.images.append(img_data)
    
    # Display and manage uploaded images
    if st_session_state.images:
        st.subheader(f"Your Images ({len(st_session_state.images)})")
        
        # Create columns for the gallery
        cols = st.columns(2)
        
        for i, img_data in enumerate(st_session_state.images):
            col_idx = i % 2
            with cols[col_idx]:
                # Load image from bytes
                img = Image.open(io.BytesIO(img_data["data"]))
                
                # Display image with caption
                st.image(img, caption=f"{i+1}. {img_data['name']}", use_container_width=True, width=300)
                
                # Remove button
                if st.button("Remove", key=f"remove_sidebar_{i}"): # Added _sidebar_ to key for uniqueness
                    st_session_state.images.pop(i)
                    st.rerun()
                
    # Clear chat button
    if st_session_state.messages:
        if st.button("Clear Chat"):
            st_session_state.messages = []
            st_session_state.generated_images = []  # Also clear generated images
            st.rerun()

def render_chat_tab(st_session_state, gemini_api_key_param, save_binary_file_func, generate_response_func, chat_container, input_container):
    """Renders the 'Image Chat' tab UI and handles its logic."""
    # Display chat messages in the chat container first
    with chat_container:
        for message in st_session_state.messages:
            with st.chat_message(message["role"]):
                if "images" in message and message["images"]:
                    image_cols = st.columns(min(len(message["images"]), 4))
                    for idx, img_idx in enumerate(message["images"]):
                        with image_cols[idx % min(len(message["images"]), 4)]:
                            img_data = st_session_state.images[img_idx]
                            img = Image.open(io.BytesIO(img_data["data"]))
                            st.image(img, caption=f"{img_data['name']}", width=150)
                    st.caption(f"Message included {len(message['images'])} images")
                
                if isinstance(message["content"], str):
                    st.markdown(message["content"])
                else:
                    if "file_path" not in message:
                        message["file_path"] = save_binary_file_func(message["content"], message["mime_type"])
                    st.image(message["file_path"], caption="Generated Image", width=300)
                    
                    if message["role"] == "assistant" and not isinstance(message["content"], str):
                        if not utils.is_duplicate_generated_image(message["content"], st_session_state.generated_images):
                            st_session_state.generated_images.append({
                                "name": os.path.basename(message["file_path"]),
                                "data": message["content"],
                                "mime_type": message["mime_type"],
                                "file_path": message["file_path"]
                            })
    
    with input_container:
        if prompt := st.chat_input("Message Gemini..."):
            image_indices = list(range(len(st_session_state.images)))
            st_session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "images": image_indices if image_indices else None
            })
            
            with st.spinner("Gemini is thinking..."):
                response_text, response_image, response_mime_type = generate_response_func(prompt)
                
                if response_text:
                    st_session_state.messages.append({"role": "assistant", "content": response_text})
                
                if response_image:
                    file_name = save_binary_file_func(response_image, response_mime_type)
                    st_session_state.messages.append({
                        "role": "assistant", 
                        "content": response_image,
                        "mime_type": response_mime_type,
                        "file_path": file_name
                    })
                    if not utils.is_duplicate_generated_image(response_image, st_session_state.generated_images):
                        st_session_state.generated_images.append({
                            "name": os.path.basename(file_name),
                            "data": response_image,
                            "mime_type": response_mime_type,
                            "file_path": file_name
                        })
            st.rerun() # Rerun to display new messages and potentially clear input

def render_video_generation_tab(st_session_state, video_gen_module, temp_dir):
    """Renders the 'Video Generation' tab UI and handles its logic."""
    st.header("Video Generation")

    # Ensure session state for video generation is initialized robustly
    default_video_state = {
        "prompt": "",
        "selected_image_name": None,
        "video_path": None,
        "error_message": None,
        "generating": False
    }
    if "video_generation_state" not in st_session_state:
        st_session_state.video_generation_state = default_video_state.copy()
    else:
        for key, value in default_video_state.items():
            if key not in st_session_state.video_generation_state:
                st_session_state.video_generation_state[key] = value

    # Robust initialization for text-to-video specific states
    if "text_video_prompt" not in st_session_state:
        st_session_state.text_video_prompt = ""
    if "text_video_path" not in st_session_state:
        st_session_state.text_video_path = None
    if "text_video_error" not in st_session_state:
        st_session_state.text_video_error = None
    if "text_video_generating" not in st_session_state:
        st_session_state.text_video_generating = False

    # --- Helper function to INITIATE Image-to-Video --- 
    def _initiate_image_to_video_generation():
        selected_image_name = st_session_state.video_generation_state["selected_image_name"]
        prompt = st_session_state.video_generation_state["prompt"]
        
        st_session_state.video_generation_state["error_message"] = None # Clear previous errors

        if not selected_image_name:
            st_session_state.video_generation_state["error_message"] = "Please select an image first."
            st_session_state.video_generation_state["generating"] = False
            st.rerun()
            return
        if not prompt:
            st_session_state.video_generation_state["error_message"] = "Please enter a prompt."
            st_session_state.video_generation_state["generating"] = False
            st.rerun()
            return

        st_session_state.video_generation_state["generating"] = True
        st_session_state.video_generation_state["video_path"] = None # Clear previous video path
        st.rerun() # This rerun will allow the main generation block to execute

    # --- Helper function to INITIATE Text-to-Video ---
    def _initiate_text_to_video_generation():
        prompt = st_session_state.text_video_prompt
        
        st_session_state.text_video_error = None # Clear previous errors

        if not prompt:
            st_session_state.text_video_error = "Please enter a prompt for text-to-video generation."
            st_session_state.text_video_generating = False
            st.rerun()
            return

        st_session_state.text_video_generating = True
        st_session_state.text_video_path = None # Clear previous video path
        st.rerun() # This rerun will allow the main generation block to execute

    # --- Image-to-Video Section UI --- (Input fields and Generate Button)
    st.subheader("Image-to-Video Generation")
    available_images = st_session_state.images + st_session_state.generated_images
    image_names = [img["name"] for img in available_images]

    if not image_names:
        st.info("Upload an image or generate one in the 'Image Chat' tab to use this feature.")
    else:
        current_selection_i2v = st_session_state.video_generation_state.get("selected_image_name")
        if current_selection_i2v not in image_names and image_names:
            current_selection_i2v = image_names[0]
        
        st_session_state.video_generation_state["selected_image_name"] = st.selectbox(
            "Select an image for video generation:",
            options=image_names,
            index=image_names.index(current_selection_i2v) if current_selection_i2v in image_names else 0,
            key="i2v_selected_image"
        )
        st_session_state.video_generation_state["prompt"] = st.text_input(
            "Enter a prompt for the video (e.g., 'make the cat dance'):", 
            value=st_session_state.video_generation_state["prompt"],
            key="i2v_prompt"
        )
        if st.button("Generate Video from Image", key="i2v_generate_button"):
            _initiate_image_to_video_generation()

    # --- Actual Image-to-Video Generation Logic & Spinner ---
    if st_session_state.video_generation_state["generating"] and \
       not st_session_state.video_generation_state["video_path"] and \
       not st_session_state.video_generation_state["error_message"]:
        with st.spinner("Generating video from image... This may take a minute or two."):
            try:
                selected_image_name = st_session_state.video_generation_state["selected_image_name"]
                prompt = st_session_state.video_generation_state["prompt"]
                all_images_for_gen = st_session_state.images + st_session_state.generated_images
                image_data_obj = utils.get_image_data_by_name(selected_image_name, all_images_for_gen)

                if not image_data_obj: # Should be caught by selectbox logic, but defensive
                    raise ValueError(f"Image '{selected_image_name}' not found during generation process.")
                if not prompt: # Should be caught by initiator, but defensive
                     raise ValueError("Prompt became empty during generation process.")

                video_path = video_gen_module.generate_video(image_data_obj['data'], prompt, temp_dir)
                st_session_state.video_generation_state["video_path"] = video_path
            except Exception as e:
                st_session_state.video_generation_state["error_message"] = f"Error generating video: {str(e)}"
            finally:
                st_session_state.video_generation_state["generating"] = False
                st.rerun() # Rerun to update UI (remove spinner, show video/error)
    
    # Display Image-to-Video results (error or video) and clear button
    if st_session_state.video_generation_state["error_message"]:
        st.error(st_session_state.video_generation_state["error_message"])
    
    if st_session_state.video_generation_state["video_path"]:
        vid_col1, vid_col2, vid_col3 = st.columns([1, 1.5, 1]) # Adjust ratios as needed for desired width
        with vid_col2:
            st.video(st_session_state.video_generation_state["video_path"])
        if st.button("Clear Image-to-Video Output", key="i2v_clear_button"):
            st_session_state.video_generation_state["video_path"] = None
            st_session_state.video_generation_state["error_message"] = None
            # Optionally reset prompt and selection, or keep them for quick retry
            # st_session_state.video_generation_state["prompt"] = ""
            # st_session_state.video_generation_state["selected_image_name"] = None 
            st.rerun()

    st.divider()

    # --- Text-to-Video Section UI --- (Input field and Generate Button)
    st.subheader("Text-to-Video Generation")
    st_session_state.text_video_prompt = st.text_input(
        "Enter a prompt to generate video from text (e.g., 'a futuristic cityscape'):",
        value=st_session_state.text_video_prompt,
        key="t2v_prompt"
    )
    if st.button("Generate Video from Text", key="t2v_generate_button"):
        _initiate_text_to_video_generation()

    # --- Actual Text-to-Video Generation Logic & Spinner ---
    if st_session_state.text_video_generating and \
       not st_session_state.text_video_path and \
       not st_session_state.text_video_error:
        with st.spinner("Generating video from text... This may take a minute or two."):
            try:
                prompt = st_session_state.text_video_prompt
                if not prompt: # Should be caught by initiator, but defensive
                    raise ValueError("Text prompt became empty during generation process.")
                video_path = video_gen_module.generate_video_from_text(prompt, temp_dir)
                st_session_state.text_video_path = video_path
            except Exception as e:
                st_session_state.text_video_error = f"Error generating video from text: {str(e)}"
            finally:
                st_session_state.text_video_generating = False
                st.rerun() # Rerun to update UI

    # Display Text-to-Video results (error or video) and clear button
    if st_session_state.text_video_error:
        st.error(st_session_state.text_video_error)

    if st_session_state.text_video_path:
        vid_text_col1, vid_text_col2, vid_text_col3 = st.columns([1, 1.5, 1]) # Adjust ratios as needed
        with vid_text_col2:
            st.video(st_session_state.text_video_path)
        if st.button("Clear Text-to-Video Output", key="t2v_clear_button"):
            st_session_state.text_video_path = None
            st_session_state.text_video_error = None
            # Optionally reset prompt
            # st_session_state.text_video_prompt = ""
            st.rerun()
