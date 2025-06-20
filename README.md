# Gemini Image Chat

A Streamlit-based web application that enables interactive conversations with Google's Gemini AI model, featuring image upload capabilities, image generation, and video creation from generated images.

## Features

- **Multi-modal Chat**: Upload multiple images and have conversations with Gemini about them. (uses `gemini-2.0-flash-preview-image-generation` model)
- **Image Generation**: Ask Gemini to generate images based on your prompts.
- **Image-to-Video Generation**: Create videos from uploaded or AI-generated images using additional prompts (uses `wavespeedai/wan-2.1-i2v-480p` model via Replicate).
- **Text-to-Video Generation**: Generate videos directly from text prompts (e.g., using `google/veo-3` model or similar via Replicate).
- **Image Management**: Upload, view, and remove images through an intuitive sidebar interface.
- **Persistent Chat History**: Maintain conversation context throughout your session.
- **Modular UI**: User interface components are refactored into a dedicated `ui_components.py` for better maintainability and clarity.

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Google Gemini API key
- Replicate API key

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd image-chat
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   REPLICATE_API_KEY=your_replicate_api_key_here
   ```

## Usage

1. **Start the application:**
   ```bash
   streamlit run app.py
   ```

2. **Upload Images:**
   - Use the sidebar to upload one or multiple images
   - Supported formats: JPG, JPEG, PNG
   - Manage uploaded images through the gallery interface

3. **Chat with Gemini:**
   - Type your questions or requests in the chat input
   - Gemini can analyze uploaded images and generate responses
   - Ask for image generation by describing what you want to see

4. **Generate Videos:**
   - Switch to the "Video Generation" tab.
   - **Image-to-Video:**
     - Select an uploaded or previously generated image.
     - Provide a prompt describing desired video movement or action (e.g., "make the cat dance").
     - Click "Generate Video from Image".
     - Model used: `wavespeedai/wan-2.1-i2v-480p` (via Replicate).
   - **Text-to-Video:**
     - Enter a text prompt describing the desired video content (e.g., "a futuristic cityscape").
     - Click "Generate Video from Text".
     - Model used: (e.g., `google/veo-3` or similar, via Replicate - specify the actual model if known, otherwise keep general).
   - Wait for video generation (may take 1-2 minutes).

## Project Structure

```
image-chat/
├── app.py                 # Main Streamlit application orchestrator
├── ui_components.py       # Defines reusable Streamlit UI components (sidebar, tabs)
├── gemini_experimental.py # Gemini AI integration module
├── utils.py              # Utility functions for file handling, image processing
├── video_generation.py   # Video generation functionality using Replicate API
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore patterns
├── temp/                # Temporary files directory
├── experiment/          # Experimental and backup files
│   ├── test_gem.py
│   ├── wan_21.py
│   └── *.png, *.mp4    # Generated files from testing
└── venv/               # Virtual environment
```

## Core Modules

### `app.py`
Orchestrates the main Streamlit application. It initializes session state, sets up the page layout (sidebar and tabs), and calls UI rendering functions from `ui_components.py`.

### `gemini_experimental.py`
Handles all Gemini AI interactions:
- Text and image response generation.
- Image generation capabilities.

### `ui_components.py`
Contains functions that render distinct parts of the Streamlit user interface:
- `render_sidebar`: Manages image uploads and display in the sidebar.
- `render_chat_tab`: Handles the "Image Chat" tab UI and logic.
- `render_video_generation_tab`: Manages the "Video Generation" tab UI and logic for both image-to-video and text-to-video.
- API communication

### `utils.py`
Utility functions for:
- File handling and storage
- Image processing
- Duplicate detection
- Temporary directory management

### `video_generation.py`
Video creation functionality:
- Generate videos from static images
- Prompt-based video generation
- File management for video outputs

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `REPLICATE_API_KEY` | Replicate API key  | Yes |

## Dependencies

Key dependencies include:
- `streamlit` - Web application framework
- `google-genai` - Google Gemini AI client
- `pillow` - Image processing
- `python-dotenv` - Environment variable management

See `requirements.txt` for complete list.

## Tips for Best Results

1. **Image Quality**: Upload clear, well-lit images for better AI analysis
2. **Specific Prompts**: Be descriptive when requesting image generation
3. **Video Prompts**: Describe movement, action, or transitions for video generation
4. **Context**: Maintain conversation context for better responses



## Development

### Running in Development Mode
```bash
streamlit run app.py --server.runOnSave true
```

### Testing
The `experiment/` folder contains test files and examples:
- `test_gem.py` - API testing scripts

