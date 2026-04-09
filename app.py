import streamlit as st
import numpy as np
from PIL import Image, ImageFilter
import io
from streamlit_stl import stl_from_text

st.set_page_config(page_title="CNC 3D Maker Pro", layout="centered")

st.sidebar.title("Carving Settings")
mode = st.sidebar.radio("Project Type:", ["Artistic (Photo)", "Logo/Text (Sharp)"])

st.title(f"🛠 CNC {mode} Generator")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 1. Basic Processing
    img = Image.open(uploaded_file).convert('L')
    
    # 2. Add Smoothing (Blur) Slider
    smooth_val = st.sidebar.slider("Smoothing (Blur)", 0, 10, 2)
    if smooth_val > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=smooth_val))
    
    if mode == "Logo/Text (Sharp)":
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        z_multiplier = st.sidebar.slider("Extrusion Thickness (mm)", 1, 30, 10)
    else:
        z_multiplier = st.sidebar.slider("Max Carving Depth (mm)", 0.1, 10.0, 2.0)

    # Base thickness so the model isn't floating
    base_height = st.sidebar.slider("Base Plate Thickness", 0.0, 5.0, 1.0)

    res = st.select_slider("Detail Level", options=[50, 100, 150], value=100)
    img = img.resize((res, res))
    data = np.array(img)
    
    st.image(img, caption="Smoothed Heightmap Preview", width=200)

    if st.button("🚀 Generate 3D Model"):
        rows, cols = data.shape
        stl_output = io.StringIO()
        stl_output.write("solid cnc_model\n")
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                # We add the base_height to every Z point
                z1 = (data[r, c] / 255.0) * z_multiplier + base_height
                z2 = (data[r+1, c] / 255.0) * z_multiplier + base_height
                z3 = (data[r, c+1] / 255.0) * z_multiplier + base_height
                
                stl_output.write("facet normal 0 0 0\n  outer loop\n")
                stl_output.write(f"    vertex {float(r)} {float(c)} {float(z1)}\n")
                stl_output.write(f"    vertex {float(r+1)} {float(c)} {float(z2)}\n")
                stl_output.write(f"    vertex {float(r)} {float(c+1)} {float(z3)}\n")
                stl_output.write("  endloop\nendfacet\n")
            
        stl_output.write("endsolid cnc_model\n")
        stl_content = stl_output.getvalue()

        st.subheader("📦 3D Preview")
        stl_from_text(stl_content, color="#A0522D", height=400) # Wood color preview

        st.success("Smoothed Model Ready!")
        st.download_button(
            label="📥 Download STL",
            data=stl_content,
            file_name="smooth_cnc_project.stl",
            mime="text/plain"
        )
        
