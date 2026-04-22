 import streamlit as st
import numpy as np
import cv2
from PIL import Image
from skimage.morphology import skeletonize
import io

st.set_page_config(page_title="V-Bit Portrait Master", layout="centered")

st.title("🎯 CNC V-Bit Line Art Generator")
st.write("Generating smooth, single-stroke paths for high-quality engraving.")

uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "jpeg", "png"])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    
    st.sidebar.header("Tuning")
    contrast = st.sidebar.slider("Line Detail", 50, 250, 130)
    smooth_factor = st.sidebar.slider("Curve Smoothing", 0.1, 5.0, 1.5) # New: Controls how smooth curves are
    min_path = st.sidebar.slider("Remove Small Noise", 10, 200, 50)

    # 1. Processing
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(blurred, contrast/2, contrast)
    
    # 2. Skeletonize (Centerline logic)
    skel = skeletonize(edges > 0)
    skel_img = (skel * 255).astype(np.uint8)
    
    # 3. Vector Smoothing Logic
    contours, _ = cv2.findContours(skel_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    st.subheader("V-Bit Engraving Preview")
    # Draw the smooth lines for the preview
    preview_canvas = np.ones_like(img) * 255
    
    h, w = img.shape
    svg_paths = ""
    
    for c in contours:
        if len(c) > min_path:
            # APPROXIMATE POLYGON: This is the secret to smooth lines
            # Higher epsilon = smoother, simpler curves
            epsilon = smooth_factor * cv2.arcLength(c, False) / 100
            approx = cv2.approxPolyDP(c, epsilon, False)
            
            # Draw for preview
            cv2.polylines(preview_canvas, [approx], False, (0, 0, 0), 1)
            
            # Build SVG path
            path_str = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in approx])
            svg_paths += f'  <path d="{path_str}" fill="none" stroke="black" stroke-width="0.5" stroke-linecap="round"/>\n'

    st.image(preview_canvas, use_column_width=True)

    # 4. Final SVG Export
    if st.button("🚀 Download Smooth SVG"):
        svg_data = f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" shape-rendering="geometricPrecision">\n'
        svg_data += svg_paths
        svg_data += "</svg>"
        
        st.download_button(
            label="📥 Download SVG for ArtCAM",
            data=svg_data,
            file_name="smooth_vbit_portrait.svg",
            mime="image/svg+xml"
        )
        
