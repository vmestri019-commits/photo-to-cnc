import cv2
import numpy as np
import streamlit as st
from PIL import Image

def generate_cnc_engraving(img_array, line_spacing=10, contrast_boost=1.5):
    # 1. Convert the uploaded PIL image to a Grayscale NumPy array
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # 2. Enhance Contrast
    img = cv2.convertScaleAbs(img, alpha=contrast_boost, beta=0)
    
    height, width = img.shape
    output = np.full((height, width), 255, dtype=np.uint8)

    # 3. Algorithm: Variable-width vertical lines
    for x in range(0, width, line_spacing):
        column_pixels = img[:, x]
        # Darker pixels = thicker lines
        thicknesses = (255 - column_pixels).astype(float) / 255.0
        
        for y in range(height):
            half_w = int((thicknesses[y] * line_spacing) / 2)
            if half_w > 0:
                start_x = max(0, x - half_w)
                end_x = min(width - 1, x + half_w)
                output[y, start_x:end_x] = 0 

    return output

# --- Streamlit UI ---
st.title("CNC Art Generator")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load the image
    image = Image.open(uploaded_file)
    img_array = np.array(image)

    # Sidebar controls for real-time adjustment
    spacing = st.sidebar.slider("Line Spacing (Density)", 2, 20, 8)
    contrast = st.sidebar.slider("Contrast Boost", 1.0, 3.0, 1.8)

    if st.button('Generate CNC Pattern'):
        with st.spinner('Processing...'):
            # Run the processing function
            result_img = generate_cnc_engraving(img_array, spacing, contrast)
            
            # Display the result
            st.image(result_img, caption='Engraving-Ready Image', use_column_width=True)
            
            # Allow user to download the result (instead of saving to server)
            res, im_png = cv2.imencode(".png", result_img)
            st.download_button(
                label="Download PNG for CNC",
                data=im_png.tobytes(),
                file_name="cnc_art.png",
                mime="image/png"
            )
            
