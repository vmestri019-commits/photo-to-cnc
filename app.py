import streamlit as st
import numpy as np
from PIL import Image
import io
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

st.set_page_config(page_title="CNC 3D Generator")

st.sidebar.title("Settings")
mode = st.sidebar.radio("Choose Mode:", ["Artistic Photo (Heightmap)", "Clean Vector (Extrusion)"])

st.title(f"🛠 CNC {mode}")

if mode == "Artistic Photo (Heightmap)":
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    depth = st.slider("Carving Depth", 0.01, 0.5, 0.1)
    res = st.select_slider("Resolution", options=[50, 100, 150, 200], value=100)

    if uploaded_file:
        img = Image.open(uploaded_file).convert('L').resize((res, res))
        data = np.array(img)
        rows, cols = data.shape
        
        stl_buffer = io.StringIO()
        stl_buffer.write("solid photo_mesh\n")
        for r in range(rows - 1):
            for c in range(cols - 1):
                z1, z2, z3 = data[r, c]*depth, data[r+1, c]*depth, data[r, c+1]*depth
                stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
                stl_buffer.write(f"    vertex {r} {c} {z1}\n")
                stl_buffer.write(f"    vertex {r+1} {c} {z2}\n")
                stl_buffer.write(f"    vertex {r} {c+1} {z3}\n")
                stl_buffer.write("  endloop\nendfacet\n")
        stl_buffer.write("endsolid photo_mesh\n")
        st.download_button("📥 Download Photo STL", stl_buffer.getvalue(), "photo_relief.stl")

elif mode == "Clean Vector (Extrusion)":
    uploaded_svg = st.file_uploader("Upload Vector (SVG)", type=["svg"])
    thickness = st.slider("Extrusion Thickness", 1.0, 20.0, 5.0)

    if uploaded_svg:
        # Save uploaded SVG to a temporary location for the library to read
        with open("temp.svg", "wb") as f:
            f.write(uploaded_svg.getbuffer())
        
        # Convert SVG to a Bitmap image at high resolution
        drawing = svg2rlg("temp.svg")
        renderPM.drawToFile(drawing, "temp.png", fmt="PNG")
        
        img = Image.open("temp.png").convert('L').resize((200, 200))
        data = np.array(img)
        
        # Make edges sharp: Black stays 0, anything else becomes 1
        data = np.where(data < 250, 1, 0) 
        
        stl_buffer = io.StringIO()
        stl_buffer.write("solid vector_mesh\n")
        rows, cols = data.shape
        for r in range(rows - 1):
            for c in range(cols - 1):
                if data[r,c] == 1:
                    z = thickness
                    stl_buffer.write(f"facet normal 0 0 0\n  outer loop\n")
                    stl_buffer.write(f"    vertex {r} {c} {z}\n")
                    stl_buffer.write(f"    vertex {r+1} {c} {z}\n")
                    stl_buffer.write(f"    vertex {r} {c+1} {z}\n")
                    stl_buffer.write("  endloop\nendfacet\n")
        stl_buffer.write("endsolid vector_mesh\n")
        
        st.image("temp.png", caption="Vector Preview")
        st.download_button("📥 Download Vector STL", stl_buffer.getvalue(), "vector_3d.stl")
