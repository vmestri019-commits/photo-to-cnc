import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageFilter
from skimage.morphology import skeletonize
import io

st.set_page_config(page_title="CNC Master Suite", layout="centered")

# --- NAVIGATION ---
mode = st.sidebar.radio("Project Type:", ["V-Bit Line Art (Centerline)", "Artistic Photo (3D Relief)", "Nameplate Designer"])

st.title(f"🛠 {mode}")

if mode == "V-Bit Line Art (Centerline)":
    st.markdown("### 🎯 Single-Line Portrait Vectorizer")
    st.write("Generates a single-path SVG. No double lines, no 3D mesh.")
    
    uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        # Load image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        
        # SLIDERS FOR FINE-TUNING
        sensitivity = st.sidebar.slider("Edge Detail (Canny)", 50, 300, 150)
        blur_val = st.sidebar.slider("Line Smoothing", 1, 9, 3, step=2)
        min_path = st.sidebar.slider("Remove Small Noise", 5, 50, 20)

        # 1. Pre-process to clean up skin noise
        blurred = cv2.GaussianBlur(img, (blur_val, blur_val), 0)
        
        # 2. Find Edges
        edges = cv2.Canny(blurred, sensitivity/2, sensitivity)
        
        # 3. SKELETONIZE (The most important part)
        # This collapses thick lines into 1-pixel thin centerlines
        skeleton = skeletonize(edges > 0)
        skeleton_img = (skeleton * 255).astype(np.uint8)
        
        # 4. Preview (Simulating a pen plot/engraving)
        st.subheader("V-Bit Path Preview")
        preview = cv2.bitwise_not(skeleton_img) # Black paths on white
        st.image(preview, use_column_width=True)
        
        # 5. VECTOR EXPORT (SVG)
        if st.button("🚀 Generate V-Bit SVG"):
            contours, _ = cv2.findContours(skeleton_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # Start building the SVG string
            h, w = img.shape
            svg_data = f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
            
            for c in contours:
                if len(c) > min_path: # Only keep significant lines
                    # Convert contour points to a single 'M L' path string
                    path_str = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in c])
                    svg_data += f'  <path d="{path_str}" fill="none" stroke="black" stroke-width="1" stroke-linecap="round"/>\n'
            
            svg_data += "</svg>"
            
            st.success("Vector Paths Created!")
            st.download_button(
                label="📥 Download SVG for ArtCAM / VCarve",
                data=svg_data,
                file_name="vbit_centerline.svg",
                mime="image/svg+xml"
            )
            st.info("Import this SVG into ArtCAM and use 'V-Bit Carving' or 'Centerline Engraving' toolpaths.")

# (Keep your other modes below as they were)
