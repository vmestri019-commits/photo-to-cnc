 import streamlit as st
import numpy as np
import cv2
from PIL import Image
from skimage.morphology import skeletonize
import io

st.set_page_config(page_title="V-Bit Portrait Master", layout="centered")

st.title("🎯 CNC V-Bit Line Art Generator")
st.write("Upload a portrait to create single-line vector art like your example.")

uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Load image for processing
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    
    # 1. SIDEBAR CONTROLS
    st.sidebar.header("Tuning")
    contrast = st.sidebar.slider("Line Detail", 50, 250, 150)
    smooth = st.sidebar.slider("Smoothness", 1, 11, 3, step=2)
    min_path = st.sidebar.slider("Ignore Small Noise", 10, 100, 30)

    # 2. PROCESSING PIPELINE
    # Blur to remove skin noise
    blurred = cv2.GaussianBlur(img, (smooth, smooth), 0)
    # Detect edges
    edges = cv2.Canny(blurred, contrast/2, contrast)
    # Skeletonize: Shrink thick edges to 1-pixel centerlines
    skel = skeletonize(edges > 0)
    skel_img = (skel * 255).astype(np.uint8)
    
    # 3. VISUAL PREVIEW
    st.subheader("V-Bit Engraving Preview")
    preview = cv2.bitwise_not(skel_img) # Black lines on white
    st.image(preview, use_column_width=True)

    # 4. EXPORT TO SVG (The format you need for ArtCAM)
    if st.button("🚀 Generate V-Bit Vector (SVG)"):
        contours, _ = cv2.findContours(skel_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        h, w = img.shape
        svg_data = f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        
        for c in contours:
            if len(c) > min_path:
                # Build the path string for the V-bit to follow
                path_str = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in c])
                svg_data += f'  <path d="{path_str}" fill="none" stroke="black" stroke-width="1" stroke-linecap="round"/>\n'
        
        svg_data += "</svg>"
        
        st.success("Vector Art Created!")
        st.download_button(
            label="📥 Download SVG for CNC",
            data=svg_data,
            file_name="vbit_portrait_lineart.svg",
            mime="image/svg+xml"
        )
        
