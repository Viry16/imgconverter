import streamlit as st
from PIL import Image
import io
import os
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
    "ICO": "ico"
}

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
            st.image(image, caption="Original Image", use_column_width=True)
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
                    img_byte_arr = io.BytesIO()
                    save_format = SUPPORTED_FORMATS[output_format].upper()
                    save_kwargs = {"format": save_format}
                    
                    if output_format in ["JPG/JPEG", "WEBP"]:
                        save_kwargs["quality"] = quality
                    
                    converted_image.save(img_byte_arr, **save_kwargs)
                    img_byte_arr.seek(0)
                    
                    # Display converted image
                    st.image(converted_image, caption="Converted Image", use_column_width=True)
                    
                    # Download button
                    file_ext = SUPPORTED_FORMATS[output_format]
                    filename = f"{Path(uploaded_file.name).stem}.{file_ext}"
                    
                    st.download_button(
                        label=f"Download {output_format}",
                        data=img_byte_arr,
                        file_name=filename,
                        mime=f"image/{file_ext}" if file_ext != "jpeg" else "image/jpeg"
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

