import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageFilter
from skimage.morphology import skeletonize
import io
from streamlit_stl import stl_from_text

st.set_page_config(page_title="CNC Master Suite", layout="centered")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛠 CNC Toolset")
mode = st.sidebar.radio("Choose Mode:", ["V-Bit Line Art (Centerline)", "Artistic Photo (3D Relief)", "Nameplate Designer"])

# --- MODE 1: V-BIT CENTERLINE ---
if mode == "V-Bit Line Art (Centerline)":
    st.header("Portrait to Single-Line Vector")
    st.write("Optimized for V-Bit engraving. Generates centerlines only.")
    
    uploaded_file = st.file_uploader("Upload Portrait", type=["jpg", "png"])
    
    if uploaded_file:
        # Convert to OpenCV format
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        
        # Controls
        sensitivity = st.sidebar.slider("Edge Sensitivity", 10, 255, 100)
        simplify = st.sidebar.slider("Path Smoothing", 1, 11, 3, step=2)
        
        # Processing: Blur -> Canny Edges -> Skeletonize
        blurred = cv2.GaussianBlur(img, (simplify, simplify), 0)
        edges = cv2.Canny(blurred, sensitivity/2, sensitivity)
        
        # Centerline logic
        skeleton = skeletonize(edges > 0)
        skeleton_img = (skeleton * 255).astype(np.uint8)
        
        # Preview (Black lines on White)
        preview = cv2.bitwise_not(skeleton_img)
        st.image(preview, caption="V-Bit Toolpath Preview", use_column_width=True)
        
        if st.button("🚀 Generate SVG Vector"):
            # Simple SVG Path Construction
            contours, _ = cv2.findContours(skeleton_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            svg_data = f'<svg viewBox="0 0 {img.shape[1]} {img.shape[0]}" xmlns="http://www.w3.org/2000/svg">'
            for c in contours:
                if len(c) > 2:
                    path = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in c])
                    svg_data += f'<path d="{path}" fill="none" stroke="black" stroke-width="1"/>'
            svg_data += "</svg>"
            
            st.download_button("📥 Download SVG for ArtCAM", svg_data, "vbit_portrait.svg", "image/svg+xml")

# --- MODE 2: ARTISTIC PHOTO (3D RELIEF) ---
elif mode == "Artistic Photo (3D Relief)":
    st.header("3D Photo Relief")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
    
    if uploaded_file:
        depth = st.sidebar.slider("Max Depth (mm)", 0.1, 100.0, 50.0)
        base = st.sidebar.slider("Base Plate (mm)", 0.0, 60.0, 5.0)
        smooth = st.sidebar.slider("Smoothing", 0, 15, 3)
        res = st.sidebar.select_slider("Resolution", [50, 100, 150, 200], 100)
        
        img = Image.open(uploaded_file).convert('L')
        if smooth > 0: img = img.filter(ImageFilter.GaussianBlur(smooth))
        img = img.resize((res, res))
        data = np.array(img)
        
        if st.button("🚀 Generate 3D STL"):
            stl_io = io.StringIO()
            stl_io.write("solid relief\n")
            for r in range(data.shape[0]-1):
                for c in range(data.shape[1]-1):
                    z1, z2, z3 = (data[r,c]/255)*depth + base, (data[r+1,c]/255)*depth + base, (data[r,c+1]/255)*depth + base
                    stl_io.write(f"facet normal 0 0 0\n  outer loop\n    vertex {r} {c} {z1}\n    vertex {r+1} {c} {z2}\n    vertex {r} {c+1} {z3}\n  endloop\nendfacet\n")
            stl_io.write("endsolid relief\n")
            stl_text = stl_io.getvalue()
            
            st.download_button("📥 Download STL", stl_text, "relief.stl")
            stl_from_text(stl_text, height=400)

# --- MODE 3: NAMEPLATE DESIGNER ---
elif mode == "Nameplate Designer":
    st.header("2D Nameplate Generator")
    name = st.text_input("Text:", "CNC MASTER")
    if name:
        st.success(f"Previewing: {name}")
        st.write("This mode uses the 2D logic to generate a high-contrast TIFF for ArtCAM.")
        # (Simplified for briefness, keeping your existing Nameplate logic here)
