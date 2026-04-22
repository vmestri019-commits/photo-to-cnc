import streamlit as st
import numpy as np
import cv2
from PIL import Image
from skimage.morphology import skeletonize
import io

st.set_page_config(page_title="V-Bit Portrait Master", layout="centered")

st.title("🎯 CNC V-Bit Line Art Generator")
st.write("Target: Clean, smooth, single-stroke vectors.")

uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "jpeg", "png"])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    
    st.sidebar.header("Tuning")
    # Threshold determines what becomes a line (Lower = more lines)
    thresh_val = st.sidebar.slider("Line Weight (Threshold)", 50, 200, 120)
    # Smoothing determines how "curvy" the lines are
    smooth_factor = st.sidebar.slider("Curve Smoothing", 0.1, 5.0, 2.0)
    # Filter small specs
    min_path = st.sidebar.slider("Remove Small Noise", 20, 500, 100)

    # --- THE CLEANING PIPELINE ---
    # 1. Heavy Blur to merge small details
    inter = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 2. Binary Threshold (Pure Black & White)
    _, binary = cv2.threshold(inter, thresh_val, 255, cv2.THRESH_BINARY_INV)
    
    # 3. Morphological Clean (Connect nearby lines)
    kernel = np.ones((3,3), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=1)
    
    # 4. Skeletonize (Centerline Logic)
    skel = skeletonize(binary > 0)
    skel_img = (skel * 255).astype(np.uint8)
    
    # 5. Find and Smooth Paths
    contours, _ = cv2.findContours(skel_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    h, w = img.shape
    preview_canvas = np.ones_like(img) * 255
    svg_paths = ""
    
    for c in contours:
        if len(c) > min_path:
            # This is the secret for smooth lines:
            epsilon = smooth_factor * cv2.arcLength(c, False) / 100
            approx = cv2.approxPolyDP(c, epsilon, False)
            
            # Draw for preview
            cv2.polylines(preview_canvas, [approx], False, (0, 0, 0), 1)
            
            # Build SVG path
            path_str = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in approx])
            svg_paths += f'  <path d="{path_str}" fill="none" stroke="black" stroke-width="0.8" stroke-linecap="round"/>\n'

    st.subheader("V-Bit Toolpath Preview")
    st.image(preview_canvas, use_column_width=True)

    if st.button("🚀 Download Smooth SVG"):
        svg_data = f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        svg_data += svg_paths
        svg_data += "</svg>"
        
        st.download_button("📥 Download SVG for ArtCAM", svg_data, "smooth_vbit.svg", "image/svg+xml")
     
