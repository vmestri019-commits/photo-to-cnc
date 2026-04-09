import streamlit as st
import numpy as np
from PIL import Image, ImageOps
import io

st.set_page_config(page_title="CNC 3D Maker")

st.sidebar.title("App Settings")
mode = st.sidebar.radio("Conversion Mode:", ["Artistic (Photo)", "Vector-Style (Logo/Text)"])

st.title(f"🛠 CNC {mode} Converter")

uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Load and process image
    img = Image.open(uploaded_file).convert('L')
    
    if mode == "Vector-Style (Logo/Text)":
        st.info("Tip: Use high-contrast black & white images for best results.")
        # Sharpen the image to make edges vertical
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        thickness = st.slider("Extrusion Thickness (mm)", 1, 20, 5)
        depth_val = thickness
    else:
        depth_val = st.slider("Max Carving Depth", 0.01, 1.0, 0.2)

    res = st.select_slider("Resolution (Low = Faster)", options=[50, 100, 150, 200], value=100)
    img = img.resize((res, res))
    data = np.array(img)
    
    if st.button("Generate STL"):
        rows, cols = data.shape
        stl_buffer = io.StringIO()
        stl_buffer.write("solid cnc_mesh\n")
        
        # Progress bar for mobile users
        bar = st.progress(0)
        for r in range(rows - 1):
            for c in range(cols - 1):
                # Map pixel brightness to Z height
                # In Vector mode, this creates a 'cliff' effect
                z1 = (255 - data[r, c]) * (depth_val / 255)
                z2 = (255 - data[r+1, c]) * (depth_val / 255)
                z3 = (255 - data[r, c+1]) * (depth_val / 255)
                
                # Create the triangle face
                stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
                stl_buffer.write(f"    vertex {r} {c} {z1}\n")
                stl_buffer.write(f"    vertex {r+1} {c} {z2}\n")
                stl_buffer.write(f"    vertex {r} {c+1} {z3}\n")
                stl_buffer.write("  endloop\nendfacet\n")
            bar.progress((r + 1) / (rows - 1))
            
        stl_buffer.write("endsolid cnc_mesh\n")
        
        st.success("3D Model Ready!")
        st.download_button(
            label="📥 Download STL File",
            data=stl_buffer.getvalue(),
            file_name="cnc_project.stl",
            mime="text/plain"
        )
    
    st.image(img, caption="Preview of heightmap logic", use_column_width=True)
        
