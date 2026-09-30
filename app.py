import streamlit as st
from PIL import Image
import io
import os
import base64
import vtracer
from pathlib import Path

st.set_page_config(page_title="Image Converter", layout="wide")

st.title("🖼️ Image Format Converter")
st.markdown("Convert images between different formats easily")

# Supported formats
SUPPORTED_FORMATS = {
    "PNG": "png",
    "JPG/JPEG": "jpeg",
    "WEBP": "webp",
    "BMP": "bmp",
    "GIF": "gif",
    "TIFF": "tiff",
    "ICO": "ico",
    "SVG": "svg"
}

SVG_MODES = ["Vector trace", "Embed raster"]


def svg_options(key_prefix):
    """Render SVG conversion options and return them as a dict."""
    svg_mode = st.radio(
        "SVG mode:", SVG_MODES, key=f"{key_prefix}_svg_mode",
        help="Vector trace converts pixels into scalable paths (best for logos, icons, flat art). "
             "Embed raster wraps the original pixels inside an SVG file (exact copy, not scalable)."
    )
    opts = {"mode": svg_mode}
    if svg_mode == "Vector trace":
        opts["colormode"] = "binary" if st.checkbox("Black & white", key=f"{key_prefix}_svg_bw") else "color"
        opts["filter_speckle"] = st.slider("Noise filter:", 0, 16, 4, key=f"{key_prefix}_svg_speckle",
                                           help="Discard patches smaller than this many pixels")
        opts["color_precision"] = st.slider("Color precision:", 1, 8, 6, key=f"{key_prefix}_svg_colors",
                                            help="Higher keeps more distinct colors")
    return opts


def image_to_svg(image, opts):
    """Convert a PIL image to SVG markup."""
    if image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
        image = image.convert("RGBA")
    png_bytes = io.BytesIO()
    image.save(png_bytes, format="PNG")
    png_bytes = png_bytes.getvalue()

    if opts["mode"] == "Embed raster":
        b64 = base64.b64encode(png_bytes).decode("ascii")
        w, h = image.size
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<image width="{w}" height="{h}" href="data:image/png;base64,{b64}"/></svg>'
        )

    return vtracer.convert_raw_image_to_svg(
        png_bytes,
        img_format="png",
        colormode=opts["colormode"],
        filter_speckle=opts["filter_speckle"],
        color_precision=opts["color_precision"],
    )

# Create tabs for different conversion modes
tab1, tab2 = st.tabs(["Single Image", "Batch Convert"])

with tab1:
    st.subheader("Convert Single Image")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
        
        if uploaded_file:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", width="stretch")
            st.text(f"Original format: {image.format}")
            st.text(f"Size: {image.size}")
    
    with col2:
        if uploaded_file:
            st.write("### Conversion Options")
            
            output_format = st.selectbox("Convert to:", list(SUPPORTED_FORMATS.keys()))
            
            # Quality slider for JPEG and WEBP
            quality = 95
            if output_format in ["JPG/JPEG", "WEBP"]:
                quality = st.slider("Quality:", 1, 100, 95)
            
            svg_opts = svg_options("single") if output_format == "SVG" else None
            
            # Resize option
            resize_option = st.checkbox("Resize image?")
            width, height = None, None
            if resize_option:
                col_w, col_h = st.columns(2)
                with col_w:
                    width = st.number_input("Width (px):", value=image.width, min_value=1)
                with col_h:
                    height = st.number_input("Height (px):", value=image.height, min_value=1)
            
            if st.button("Convert Image", key="single_convert"):
                try:
                    # Convert image
                    converted_image = image.copy()
                    
                    # Resize if requested
                    if resize_option and width and height:
                        converted_image = converted_image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary (for formats that don't support transparency)
                    if output_format in ["JPG/JPEG"] and converted_image.mode in ("RGBA", "LA", "P"):
                        rgb_image = Image.new("RGB", converted_image.size, (255, 255, 255))
                        rgb_image.paste(converted_image, mask=converted_image.split()[-1] if converted_image.mode == "RGBA" else None)
                        converted_image = rgb_image
                    
                    # Save to bytes
                    if output_format == "SVG":
                        with st.spinner("Generating SVG..."):
                            svg_markup = image_to_svg(converted_image, svg_opts)
                        img_byte_arr = io.BytesIO(svg_markup.encode("utf-8"))
                        st.image(svg_markup, caption="Converted Image", width="stretch")
                    else:
                        img_byte_arr = io.BytesIO()
                        save_format = SUPPORTED_FORMATS[output_format].upper()
                        save_kwargs = {"format": save_format}
                        
                        if output_format in ["JPG/JPEG", "WEBP"]:
                            save_kwargs["quality"] = quality
                        
                        converted_image.save(img_byte_arr, **save_kwargs)
                        img_byte_arr.seek(0)
                        
                        # Display converted image
                        st.image(converted_image, caption="Converted Image", width="stretch")
                    
                    # Download button
                    file_ext = SUPPORTED_FORMATS[output_format]
                    filename = f"{Path(uploaded_file.name).stem}.{file_ext}"
                    
                    st.download_button(
                        label=f"Download {output_format}",
                        data=img_byte_arr,
                        file_name=filename,
                        mime="image/svg+xml" if file_ext == "svg" else f"image/{file_ext}"
                    )
                    st.success(f"✅ Image converted to {output_format}!")
                    
                except Exception as e:
                    st.error(f"❌ Error converting image: {str(e)}")

with tab2:
    st.subheader("Batch Convert Images")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload multiple images",
            type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"📁 **{len(uploaded_files)} files selected**")
            for file in uploaded_files:
                st.write(f"  • {file.name}")
    
    with col2:
        if uploaded_files:
            st.write("### Conversion Settings")
            
            output_format = st.selectbox("Convert all to:", list(SUPPORTED_FORMATS.keys()), key="batch_format")
            
            quality = 95
            if output_format in ["JPG/JPEG", "WEBP"]:
                quality = st.slider("Quality:", 1, 100, 95, key="batch_quality")
            
            svg_opts = svg_options("batch") if output_format == "SVG" else None
            
            if st.button("Convert All Images", key="batch_convert"):
                try:
                    converted_images = []
                    
                    with st.spinner("Converting images..."):
                        for uploaded_file in uploaded_files:
                            image = Image.open(uploaded_file)
                            
                            # Convert to RGB if necessary
                            if output_format in ["JPG/JPEG"] and image.mode in ("RGBA", "LA", "P"):
                                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                                image = rgb_image
                            
                            # Save to bytes
                            if output_format == "SVG":
                                img_byte_arr = io.BytesIO(image_to_svg(image, svg_opts).encode("utf-8"))
                            else:
                                img_byte_arr = io.BytesIO()
                                save_format = SUPPORTED_FORMATS[output_format].upper()
                                save_kwargs = {"format": save_format}
                                
                                if output_format in ["JPG/JPEG", "WEBP"]:
                                    save_kwargs["quality"] = quality
                                
                                image.save(img_byte_arr, **save_kwargs)
                                img_byte_arr.seek(0)
                            
                            file_ext = SUPPORTED_FORMATS[output_format]
                            filename = f"{Path(uploaded_file.name).stem}.{file_ext}"
                            
                            converted_images.append((filename, img_byte_arr.getvalue()))
                    
                    # Display results
                    st.success(f"✅ Successfully converted {len(converted_images)} images!")
                    
                    st.write("### Converted Files")
                    cols = st.columns(min(3, len(converted_images)))
                    
                    for idx, (filename, img_data) in enumerate(converted_images):
                        with cols[idx % 3]:
                            st.download_button(
                                label=f"📥 {filename}",
                                data=img_data,
                                file_name=filename,
                                key=f"download_{idx}"
                            )
                
                except Exception as e:
                    st.error(f"❌ Error converting images: {str(e)}")

