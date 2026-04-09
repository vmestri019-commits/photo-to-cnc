import streamlit as st
import numpy as np
from PIL import Image
import io

# --- APP INTERFACE ---
st.title("📸 Image to CNC STL Converter")
st.write("Upload a photo to generate a 3D relief for your CNC router.")

# 1. User Inputs
uploaded_file = st.file_uploader("Choose a photo...", type=["jpg", "jpeg", "png"])
depth_multiplier = st.slider("Select Carving Depth (Z-Scale):", 0.01, 0.5, 0.1)
resolution = st.select_slider("Resolution (Lower is faster):", options=[50, 100, 150, 200], value=100)

if uploaded_file is not None:
    # 2. Image Processing
    img = Image.open(uploaded_file).convert('L') # Convert to Grayscale
    img = img.resize((resolution, resolution))   # Resize for mobile performance
    data = np.array(img)
    rows, cols = data.shape

    st.image(img, caption="Processed Image", use_column_width=True)

    # 3. Generate STL Data
    # We use an 'io.StringIO' buffer to build the file in the phone's memory
    stl_buffer = io.StringIO()
    stl_buffer.write("solid image_mesh\n")

    progress_bar = st.progress(0)
    
    for r in range(rows - 1):
        for c in range(cols - 1):
            # Define 3D coordinates based on pixel brightness
            z1, z2, z3 = data[r, c]*depth_multiplier, data[r+1, c]*depth_multiplier, data[r, c+1]*depth_multiplier
            
            # Create a triangle face in STL format
            stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
            stl_buffer.write(f"    vertex {r} {c} {z1}\n")
            stl_buffer.write(f"    vertex {r+1} {c} {z2}\n")
            stl_buffer.write(f"    vertex {r} {c+1} {z3}\n")
            stl_buffer.write("  endloop\nendfacet\n")
        
        progress_bar.progress((r + 1) / (rows - 1))

    stl_buffer.write("endsolid image_mesh\n")
    
    # 4. Download Button
    st.success("STL Generated Successfully!")
    st.download_button(
        label="📥 Download STL for CNC",
        data=stl_buffer.getvalue(),
        file_name="cnc_carving.stl",
        mime="text/plain"
  )
  
