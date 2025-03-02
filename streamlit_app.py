import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="90s Etch A Sketch", layout="centered")
st.title("90s Etch A Sketch")

# Custom CSS for improved performance
st.markdown("""
<style>
    .stButton button {
        min-height: 50px;
    }
    .etch-a-sketch-container {
        background-color: #ff0000;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    /* Improve rendering performance */
    .stImage img {
        image-rendering: optimizeSpeed;
        image-rendering: -moz-crisp-edges;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: optimize-contrast;
        image-rendering: pixelated;
    }
</style>
""", unsafe_allow_html=True)

# Add key handler component
import streamlit.components.v1 as components

components.html(
    """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const doc = window.parent.document;
        const buttons = Array.from(doc.querySelectorAll('button[kind=secondary]'));
        
        const up_button = buttons.find(el => el.innerText === "⬆️");
        const down_button = buttons.find(el => el.innerText === "⬇️");
        const left_button = buttons.find(el => el.innerText === "⬅️");
        const right_button = buttons.find(el => el.innerText === "➡️");
        
        window.parent.addEventListener('keydown', function(e) {
            switch (e.key) {
                case "ArrowLeft":
                    e.preventDefault();
                    left_button.click();
                    break;
                case "ArrowUp":
                    e.preventDefault();
                    up_button.click();
                    break;
                case "ArrowRight":
                    e.preventDefault();
                    right_button.click();
                    break;
                case "ArrowDown":
                    e.preventDefault();
                    down_button.click();
                    break;
            }
        }, true);
    }, 1000);
});
</script>
""",
    height=0,
    width=0,
)

# Initialize session state variables if they don't exist
if 'initialized' not in st.session_state:
    # Canvas dimensions
    canvas_width, canvas_height = 600, 400
    
    # Create a blank canvas with a light gray background
    st.session_state.canvas = Image.new('RGB', (canvas_width, canvas_height), (230, 230, 230))
    st.session_state.draw = ImageDraw.Draw(st.session_state.canvas)
    st.session_state.cursor_x = canvas_width // 2
    st.session_state.cursor_y = canvas_height // 2
    st.session_state.is_drawing = False
    st.session_state.was_drawing = False  # Track if we were drawing before
    st.session_state.initialized = True
    st.session_state.move_queue = []  # Queue of moves to process
    st.session_state.action_performed = False  # Flag to detect if action was performed
    st.session_state.last_update = 0
    st.session_state.display_buffer = st.session_state.canvas.copy()  # For smoother rendering

# Create a single placeholder for the canvas
canvas_placeholder = st.empty()

# Display the canvas - use the cached display_buffer for improved performance
canvas_placeholder.image(st.session_state.display_buffer, use_container_width=True)

# Create the UI container with red border
st.markdown('<div class="etch-a-sketch-container">', unsafe_allow_html=True)

# Create two columns for our directional buttons
col1, col2, col3 = st.columns([1, 3, 1])

# Process movement button states using a stateful approach
move_state = {"x": 0, "y": 0, "action": None}

# Up button in middle column
with col2:
    if st.button("⬆️", help="Move Up", use_container_width=True, key="up"):
        move_state["y"] = -1
        move_state["action"] = "move"

# Left, center and right buttons in a row
left, center, right = st.columns(3)
with left:
    if st.button("⬅️", help="Move Left", use_container_width=True, key="left"):
        move_state["x"] = -1
        move_state["action"] = "move"
with center:
    if st.button("⚪", help="Center/Stop", use_container_width=True, key="center"):
        move_state["action"] = "center"
with right:
    if st.button("➡️", help="Move Right", use_container_width=True, key="right"):
        move_state["x"] = 1
        move_state["action"] = "move"

# Down button in middle column
with col2:
    if st.button("⬇️", help="Move Down", use_container_width=True, key="down"):
        move_state["y"] = 1
        move_state["action"] = "move"

# Speed control - use a more responsive element
move_speed = st.slider("Drawing Speed", 1, 10, 3, help="Adjust how far each movement goes")

st.markdown("</div>", unsafe_allow_html=True)

# Create radio selector for mode - add key to prevent reinitialization
drawing_mode = st.radio(
    "Select Mode:",
    ["Drawing Mode", "Eraser Mode", "No Drawing (Move Only)"],
    horizontal=True,
    key="drawing_mode"
)

# Set the appropriate flags based on the radio selection
drawing_enabled = drawing_mode == "Drawing Mode"
eraser_mode = drawing_mode == "Eraser Mode"

# Add a shake button to clear the canvas
if st.button("Shake to Erase!", help="Shake the Etch A Sketch to clear your drawing", key="shake"):
    # Create a new blank canvas
    canvas_width, canvas_height = 600, 400
    st.session_state.canvas = Image.new('RGB', (canvas_width, canvas_height), (230, 230, 230))
    st.session_state.draw = ImageDraw.Draw(st.session_state.canvas)
    st.session_state.cursor_x = canvas_width // 2
    st.session_state.cursor_y = canvas_height // 2
    st.session_state.is_drawing = False
    st.session_state.display_buffer = st.session_state.canvas.copy()
    move_state["action"] = "shake"
    canvas_placeholder.image(st.session_state.display_buffer, use_container_width=True)

# Process moves more efficiently
if move_state["action"] == "move":
    # Calculate new position
    horizontal_move = move_state["x"] * move_speed
    vertical_move = move_state["y"] * move_speed
    
    # Get current canvas dimensions
    canvas_width = st.session_state.canvas.width
    canvas_height = st.session_state.canvas.height
    
    # Calculate new cursor position (with bounds checking)
    new_x = max(0, min(canvas_width - 1, st.session_state.cursor_x + horizontal_move))
    new_y = max(0, min(canvas_height - 1, st.session_state.cursor_y + vertical_move))
    
    # If there's actual movement
    if new_x != st.session_state.cursor_x or new_y != st.session_state.cursor_y:
        # Always draw in drawing mode
        if drawing_enabled:
            # Draw the line in black
            st.session_state.draw.line(
                [st.session_state.cursor_x, st.session_state.cursor_y, new_x, new_y],
                fill=(0, 0, 0),
                width=2
            )
            st.session_state.is_drawing = True
        # Erase in eraser mode   
        elif eraser_mode:
            # Draw the line in the background color (light gray)
            st.session_state.draw.line(
                [st.session_state.cursor_x, st.session_state.cursor_y, new_x, new_y],
                fill=(230, 230, 230),
                width=6
            )
            st.session_state.is_drawing = True
        else:
            # In no drawing mode, don't draw
            st.session_state.is_drawing = False
        
        # Update cursor position
        st.session_state.cursor_x = new_x
        st.session_state.cursor_y = new_y
        
        # Create display buffer with cursor indicator
        st.session_state.display_buffer = st.session_state.canvas.copy()
        
        # For the no drawing mode, add a visible cursor indicator
        if not drawing_enabled and not eraser_mode:
            cursor_draw = ImageDraw.Draw(st.session_state.display_buffer)
            cursor_size = 5
            cursor_draw.line(
                [st.session_state.cursor_x - cursor_size, st.session_state.cursor_y, 
                 st.session_state.cursor_x + cursor_size, st.session_state.cursor_y],
                fill=(255, 0, 0), width=2
            )
            cursor_draw.line(
                [st.session_state.cursor_x, st.session_state.cursor_y - cursor_size, 
                 st.session_state.cursor_x, st.session_state.cursor_y + cursor_size],
                fill=(255, 0, 0), width=2
            )
        
        # Always update the display after any movement
        canvas_placeholder.image(st.session_state.display_buffer, use_container_width=True)

elif move_state["action"] == "center":
    # Stop drawing
    st.session_state.is_drawing = False
    st.session_state.was_drawing = False

# Add some instructions
with st.expander("How to Use Your Etch A Sketch"):
    st.markdown("""
    1. Use the arrow buttons to move in different directions:
       - ⬆️ moves up
       - ⬇️ moves down
       - ⬅️ moves left
       - ➡️ moves right
       - ⚪ center button lifts the pen temporarily
    2. Adjust the drawing speed with the slider
    3. Select one of the three modes:
       - Drawing Mode: draws black lines as you move
       - Eraser Mode: erases lines in the direction you move
       - No Drawing: allows repositioning without drawing or erasing (shows a red crosshair cursor)
    4. Click "Shake to Erase!" to clear your whole canvas and start over
    5. Use keyboard arrow keys for faster control
    
    Just like the original toy, you can only draw continuous lines!
    """)

# Add a download button to save your masterpiece
# Convert the image to bytes for download (don't include cursor overlay)
img_bytes = BytesIO()
st.session_state.canvas.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

btn = st.download_button(
    label="Download your drawing",
    data=img_bytes,
    file_name="etch_a_sketch_drawing.png",
    mime="image/png",
    key="download"
)

# Add a footer with performance tips
st.markdown("""
---
**Performance Tips:**
- Use keyboard arrow keys for smoother drawing
- Reduce drawing speed if experiencing lag
- For complex drawings, make smaller movements
""")