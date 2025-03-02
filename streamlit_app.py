import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from io import BytesIO

st.title("90s Etch A Sketch")

import streamlit.components.v1 as components

# Replace the existing components.html code block with this:

components.html(
    f"""
<script>
// Wait for the document to be fully loaded
document.addEventListener('DOMContentLoaded', function() {{
    // We need to wait a bit for Streamlit elements to be rendered
    setTimeout(function() {{
        const doc = window.parent.document;
        const buttons = Array.from(doc.querySelectorAll('button[kind=secondary]'));
        
        // Find buttons by their text content
        const up_button = buttons.find(el => el.innerText === "⬆️");
        const down_button = buttons.find(el => el.innerText === "⬇️");
        const left_button = buttons.find(el => el.innerText === "⬅️");
        const right_button = buttons.find(el => el.innerText === "➡️");
        
        // Attach the event listener to the parent document
        window.parent.addEventListener('keydown', function(e) {{
            // Using key instead of keyCode (which is deprecated)
            switch (e.key) {{
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
            }}
        }}, true);  // Use capture phase for better key handling
        
        console.log("Keyboard event handlers initialized");
    }}, 1000);  // Give it a second to ensure elements are loaded
}});
</script>
""",
    height=0,
    width=0,
)
# Initialize session state variables if they don't exist
if 'canvas' not in st.session_state:
    # Create a blank canvas with a light gray background
    canvas_width, canvas_height = 600, 400
    st.session_state.canvas = Image.new('RGB', (canvas_width, canvas_height), (230, 230, 230))
    st.session_state.draw = ImageDraw.Draw(st.session_state.canvas)
    st.session_state.cursor_x = canvas_width // 2
    st.session_state.cursor_y = canvas_height // 2
    st.session_state.history = []  # To track cursor positions for line drawing
    st.session_state.is_drawing = False
    st.session_state.last_move = {"x": 0, "y": 0}

# Display current canvas
canvas_placeholder = st.empty()
canvas_placeholder.image(st.session_state.canvas, use_container_width=True)

# Create a container with a red border to mimic the toy
control_container = st.container()
with control_container:
    st.markdown("""
    <style>
    .etch-a-sketch-container {
        background-color: #ff0000;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    <div class="etch-a-sketch-container">
    """, unsafe_allow_html=True)
    
    # Create two columns for our directional buttons
    col1, col2, col3 = st.columns([1, 3, 1])
    
    # Up button in middle column
    with col2:
        up_button = st.button("⬆️", help="Move Up", use_container_width=True)
    
    # Left, center and right buttons in a row
    left, center, right = st.columns(3)
    with left:
        left_button = st.button("⬅️", help="Move Left", use_container_width=True)
    with center:
        # Optional: center button could be used to lift the pen
        center_button = st.button("⚪", help="Center/Stop", use_container_width=True)
    with right:
        right_button = st.button("➡️", help="Move Right", use_container_width=True)
    
    # Down button in middle column
    with col2:
        down_button = st.button("⬇️", help="Move Down", use_container_width=True)
    
    # Speed control
    move_speed = st.slider("Drawing Speed", 1, 10, 3, help="Adjust how far each movement goes")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Add a shake button to clear the canvas
if st.button("Shake to Erase!", help="Shake the Etch A Sketch to clear your drawing"):
    # Create a new blank canvas
    canvas_width, canvas_height = 600, 400
    st.session_state.canvas = Image.new('RGB', (canvas_width, canvas_height), (230, 230, 230))
    st.session_state.draw = ImageDraw.Draw(st.session_state.canvas)
    st.session_state.cursor_x = canvas_width // 2
    st.session_state.cursor_y = canvas_height // 2
    st.session_state.history = []
    st.session_state.is_drawing = False
    st.success("Canvas cleared!")
    
# Create radio selector for mode
drawing_mode = st.radio(
    "Select Mode:",
    ["Drawing Mode", "Eraser Mode", "No Drawing (Move Only)"],
    horizontal=True
)

# Set the appropriate flags based on the radio selection
drawing_enabled = drawing_mode == "Drawing Mode"
eraser_mode = drawing_mode == "Eraser Mode"
# When "No Drawing" is selected, both will be False

# Process button inputs
horizontal_move = 0
vertical_move = 0

if up_button:
    vertical_move = -move_speed
elif down_button:
    vertical_move = move_speed

if left_button:
    horizontal_move = -move_speed
elif right_button:
    horizontal_move = move_speed

if center_button:
    # Center button stops the drawing temporarily
    st.session_state.is_drawing = False

# Only process moves when there is actual movement
if horizontal_move != 0 or vertical_move != 0:
    # Save a copy of the canvas before adding the cursor
    canvas_without_cursor = st.session_state.canvas.copy()
    
    # Update cursor position
    new_x = max(0, min(st.session_state.canvas.width - 1, 
                      st.session_state.cursor_x + horizontal_move))
    new_y = max(0, min(st.session_state.canvas.height - 1, 
                      st.session_state.cursor_y + vertical_move))
    
    # In drawing or eraser mode, draw a line
    if drawing_enabled or eraser_mode:
        if st.session_state.is_drawing:
            # Choose color based on mode (black for drawing, light gray for erasing)
            line_color = (230, 230, 230) if eraser_mode else (0, 0, 0)
            # Make eraser slightly wider than the pen
            line_width = 6 if eraser_mode else 2
            
            st.session_state.draw.line(
                [st.session_state.cursor_x, st.session_state.cursor_y, new_x, new_y],
                fill=line_color,
                width=line_width
            )
    
    # Update cursor position
    st.session_state.cursor_x = new_x
    st.session_state.cursor_y = new_y
    
    if drawing_enabled or eraser_mode:
        st.session_state.is_drawing = True
    
    # For the no drawing mode, add a visible cursor indicator
    display_canvas = st.session_state.canvas.copy()
    if not drawing_enabled and not eraser_mode:
        cursor_draw = ImageDraw.Draw(display_canvas)
        # Draw a red crosshair cursor
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
    
    # Update the display
    canvas_placeholder.image(display_canvas, use_container_width=True)

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
    
    Just like the original toy, you can only draw continuous lines!
    """)

# Add a download button to save your masterpiece
# Convert the image to bytes for download
img_bytes = BytesIO()
st.session_state.canvas.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

btn = st.download_button(
    label="Download your drawing",
    data=img_bytes,
    file_name="etch_a_sketch_drawing.png",
    mime="image/png")