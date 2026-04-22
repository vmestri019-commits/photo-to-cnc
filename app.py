import streamlit as st
import numpy as np
import cv2
from PIL import Image
from skimage.morphology import skeletonize
import io

st.set_page_config(page_title="V-Bit Portrait Master", layout="centered")

st.title("🎯 CNC V-Bit Line Art Generator")
st.write("Target: Connected, flowing paths for professional engraving.")

uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "jpeg", "png"])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    
    st.sidebar.header("Tuning")
    thresh_val = st.sidebar.slider("Line Boldness", 30, 200, 100)
    smooth_factor = st.sidebar.slider("Path Smoothness", 0.5, 8.0, 3.5)
    min_path_len = st.sidebar.slider("Delete Tiny Paths", 50, 1000, 300)

    # --- THE ARTISTIC PIPELINE ---
    # 1. MEDIAN BLUR: Deletes noise but keeps edge sharpness
    clean = cv2.medianBlur(img, 5)
    
    # 2. ADAPTIVE THRESHOLD: Handles shadows better than a standard threshold
    binary = cv2.adaptiveThreshold(clean, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # 3. CONNECT GAPS: Bridges tiny breaks in the lines
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # 4. SKELETONIZE: Collapse to single-pixel centerline
    skel = skeletonize(binary > 0)
    skel_img = (skel * 255).astype(np.uint8)
    
    # 5. VECTORIZE & SMOOTH
    contours, _ = cv2.findContours(skel_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    h, w = img.shape
    preview_canvas = np.ones_like(img) * 255
    svg_paths = ""
    
    for c in contours:
        if len(c) > min_path_len:
            # DOUGLAS-PEUCKER SMOOTHING
            epsilon = (smooth_factor / 100.0) * cv2.arcLength(c, False)
            approx = cv2.approxPolyDP(c, epsilon, False)
            
            # Draw for preview
            cv2.polylines(preview_canvas, [approx], False, (0, 0, 0), 1)
            
            # Build SVG path
            path_str = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in approx])
            svg_paths += f'  <path d="{path_str}" fill="none" stroke="black" stroke-width="0.8" stroke-linecap="round"/>\n'

    st.subheader("V-Bit Toolpath Preview")
    st.image(preview_canvas, use_column_width=True)

    if st.button("🚀 Export Final SVG"):
        svg_header = f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        svg_data = svg_header + svg_paths + "</svg>"
        
        st.download_button("📥 Download Final Smooth SVG", svg_data, "vbit_masterpiece.svg", "image/svg+xml")
        
