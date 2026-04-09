import streamlit as st
import numpy as np
from PIL import Image, ImageFilter
import io
from streamlit_stl import stl_from_text

st.set_page_config(page_title="CNC 3D Maker Pro", layout="centered")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🛠 Carving Settings")

mode = st.sidebar.radio("Project Type:", ["Artistic (Photo)", "Logo/Text (Sharp)"])

# Smoothing control to fix the "pixelated/triangular" look
smooth_val = st.sidebar.slider("Smoothing (Blur)", 0, 10, 2)

# Set Max Depth to 50mm as requested
if mode == "Logo/Text (Sharp)":
    z_multiplier = st.sidebar.slider("Extrusion Thickness (mm)", 1, 50, 10)
else:
    z_multiplier = st.sidebar.slider("Max Carving Depth (mm)", 0.1, 50.0, 5.0)

base_height = st.sidebar.slider("Base Plate Thickness (mm)", 0.0, 10.0, 2.0)

res = st.sidebar.select_slider("Detail Level (Resolution)", options=[50, 100, 150], value=100)

# --- MAIN INTERFACE ---
st.title(f"CNC {mode} Generator")
st.write("Adjust settings in the left sidebar ⬅️")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 1. Load Image
    img = Image.open(uploaded_file).convert('L')
    
    # 2. Apply Smoothing
    if smooth_val > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=smooth_val))
    
    # 3. Handle Vector Mode Sharpening
    if mode == "Logo/Text (Sharp)":
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')

    # 4. Resize for processing
    img = img.resize((res, res))
    data = np.array(img)
    
    st.image(img, caption="Processed Heightmap (Input)", width=250)

    if st.button("🚀 Generate 3D Model"):
        rows, cols = data.shape
        stl_output = io.StringIO()
        stl_output.write("solid cnc_model\n")
        
        progress_bar = st.progress(0)
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                # Calculate Heights (Z values)
                z1 = (data[r, c] / 255.0) * z_multiplier + base_height
                z2 = (data[r+1, c] / 255.0) * z_multiplier + base_height
                z3 = (data[r, c+1] / 255.0) * z_multiplier + base_height
                
                # Write STL Triangle Face
                stl_output.write("facet normal 0 0 0\n  outer loop\n")
                stl_output.write(f"    vertex {float(r)} {float(c)} {float(z1)}\n")
                stl_output.write(f"    vertex {float(r+1)} {float(c)} {float(z2)}\n")
                stl_output.write(f"    vertex {float(r)} {float(c+1)} {float(z3)}\n")
                stl_output.write("  endloop\nendfacet\n")
            
            progress_bar.progress((r + 1) / (rows - 1))
            
        stl_output.write("endsolid cnc_model\n")
        stl_content = stl_output.getvalue()

        # --- PREVIEW AND DOWNLOAD ---
        st.subheader("📦 3D Preview")
        stl_from_text(stl_content, color="#A0522D", height=400)

        st.success(f"Model Created with {z_multiplier}mm Depth!")
        st.download_button(
            label="📥 Download STL File",
            data=stl_content,
            file_name="cnc_carving_50mm.stl",
            mime="text/plain"
            )
        
