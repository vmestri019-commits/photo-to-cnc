import streamlit as st
import numpy as np
from PIL import Image, ImageFilter
import io
from streamlit_stl import stl_from_text

st.set_page_config(page_title="CNC 3D Maker Pro", layout="centered")

st.title("🛠 CNC 3D Model Generator")

# 1. File Uploader
uploaded_file = st.file_uploader("Step 1: Upload your Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # --- MAIN SCREEN CONTROLS ---
    st.subheader("Step 2: Adjust Carving Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mode = st.radio("Project Type:", ["Artistic (Photo)", "Logo/Text (Sharp)"])
        # Detail Level slider is now on the main screen
        res = st.select_slider("Detail Level (Resolution)", options=[50, 100, 150], value=100)

    with col2:
        # Max Depth set to 50mm as requested
        z_multiplier = st.slider("Max Carving Depth (mm)", 0.1, 50.0, 10.0)
        smooth_val = st.slider("Smoothing (Blur)", 0, 10, 2)
        base_height = st.slider("Base Plate Thickness (mm)", 0.0, 10.0, 2.0)

    # 2. Image Processing
    img = Image.open(uploaded_file).convert('L')
    
    if smooth_val > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=smooth_val))
    
    if mode == "Logo/Text (Sharp)":
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')

    img_resize = img.resize((res, res))
    data = np.array(img_resize)
    
    st.image(img_resize, caption="Heightmap Preview", width=250)

    # 3. Generation Logic
    if st.button("🚀 Step 3: Generate 3D Model"):
        rows, cols = data.shape
        stl_output = io.StringIO()
        stl_output.write("solid cnc_model\n")
        
        progress_bar = st.progress(0)
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                z1 = (data[r, c] / 255.0) * z_multiplier + base_height
                z2 = (data[r+1, c] / 255.0) * z_multiplier + base_height
                z3 = (data[r, c+1] / 255.0) * z_multiplier + base_height
                
                stl_output.write("facet normal 0 0 0\n  outer loop\n")
                stl_output.write(f"    vertex {float(r)} {float(c)} {float(z1)}\n")
                stl_output.write(f"    vertex {float(r+1)} {float(c)} {float(z2)}\n")
                stl_output.write(f"    vertex {float(r)} {float(c+1)} {float(z3)}\n")
                stl_output.write("  endloop\nendfacet\n")
            
            progress_bar.progress((r + 1) / (rows - 1))
            
        stl_output.write("endsolid cnc_model\n")
        stl_content = stl_output.getvalue()

        # 4. Preview and Download
        st.subheader("📦 3D Preview")
        stl_from_text(stl_content, color="#A0522D", height=400)

        st.success(f"Model Created: {z_multiplier}mm Depth")
        st.download_button(
            label="📥 Download STL File",
            data=stl_content,
            file_name="cnc_project.stl",
            mime="text/plain"
        )
        
