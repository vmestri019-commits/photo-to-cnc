import streamlit as st
import numpy as np
from PIL import Image
import io

# --- APP CONFIG ---
st.set_page_config(page_title="CNC 3D Maker", layout="centered")

st.sidebar.title("Carving Settings")
mode = st.sidebar.radio("Project Type:", ["Artistic (Photo)", "Logo/Text (Sharp Edges)"])

st.title(f"🛠 CNC {mode} Generator")

uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Open image and convert to Grayscale
    img = Image.open(uploaded_file).convert('L')
    
    if mode == "Logo/Text (Sharp Edges)":
        st.info("Converting image to sharp black & white for clean vertical walls.")
        # Any pixel darker than middle-grey becomes black, others white
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        thickness = st.slider("Extrusion Thickness (mm)", 1, 30, 10)
        z_multiplier = thickness
    else:
        z_multiplier = st.slider("Max Carving Depth (mm)", 0.1, 10.0, 2.0)

    # Resolution (keeps file size small for phone downloads)
    res = st.select_slider("Detail Level", options=[50, 100, 150], value=100)
    img = img.resize((res, res))
    data = np.array(img)
    
    st.image(img, caption="Internal 3D Map Preview", width=300)

    if st.button("🚀 Generate 3D STL"):
        rows, cols = data.shape
        stl_output = io.StringIO()
        stl_output.write("solid cnc_model\n")
        
        progress_bar = st.progress(0)
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                # We invert it: White pixels = High, Black pixels = Low
                z1 = (data[r, c] / 255.0) * z_multiplier
                z2 = (data[r+1, c] / 255.0) * z_multiplier
                z3 = (data[r, c+1] / 255.0) * z_multiplier
                
                # Create the triangle face
                stl_output.write("facet normal 0 0 0\n  outer loop\n")
                stl_output.write(f"    vertex {r} {c} {z1}\n")
                stl_output.write(f"    vertex {r+1} {c} {z2}\n")
                stl_output.write(f"    vertex {r} {c+1} {z3}\n")
                stl_output.write("  endloop\nendfacet\n")
            
            progress_bar.progress((r + 1) / (rows - 1))
            
        stl_output.write("endsolid cnc_model\n")
        
        st.success("Model Created!")
        st.download_button(
            label="📥 Download STL",
            data=stl_output.getvalue(),
            file_name="my_cnc_project.stl",
            mime="text/plain"
        )
        
