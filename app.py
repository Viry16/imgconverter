import io
import zipfile

import streamlit as st

from converter import (
    FORMATS,
    INPUT_EXTENSIONS,
    SVG_MODES,
    SVG_TRACE,
    ConversionError,
    ConvertOptions,
    convert,
    load_image,
    normalize,
)

st.set_page_config(page_title="Image Converter", layout="wide")

st.title("🖼️ Image Format Converter")
st.markdown("Convert images between different formats easily")


def format_options(key_prefix, image=None):
    """Render the conversion settings and return (format, options)."""
    fmt = FORMATS[st.selectbox("Convert to:", list(FORMATS), key=f"{key_prefix}_format")]
    options = ConvertOptions()

    if fmt.has_quality:
        options.quality = st.slider("Quality:", 1, 100, 95, key=f"{key_prefix}_quality")

    if fmt.label == "SVG":
        options.svg_mode = st.radio(
            "SVG mode:", SVG_MODES, key=f"{key_prefix}_svg_mode",
            help="Vector trace converts pixels into scalable paths (best for logos, icons, flat art). "
                 "Embed raster wraps the original pixels inside an SVG file (exact copy, not scalable).",
        )
        if options.svg_mode == SVG_TRACE:
            if st.checkbox("Black & white", key=f"{key_prefix}_svg_bw"):
                options.svg_colormode = "binary"
            options.svg_filter_speckle = st.slider(
                "Noise filter:", 0, 16, 4, key=f"{key_prefix}_svg_speckle",
                help="Discard patches smaller than this many pixels",
            )
            options.svg_color_precision = st.slider(
                "Color precision:", 1, 8, 6, key=f"{key_prefix}_svg_colors",
                help="Higher keeps more distinct colors",
            )

    if image is not None and st.checkbox("Resize image?", key=f"{key_prefix}_resize"):
        col_w, col_h = st.columns(2)
        with col_w:
            width = st.number_input("Width (px):", value=image.width, min_value=1, key=f"{key_prefix}_w")
        with col_h:
            height = st.number_input("Height (px):", value=image.height, min_value=1, key=f"{key_prefix}_h")
        options.resize = (int(width), int(height))

    return fmt, options


tab_single, tab_batch = st.tabs(["Single Image", "Batch Convert"])

with tab_single:
    st.subheader("Convert Single Image")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload an image", type=INPUT_EXTENSIONS, key="single_upload")
        image = None
        if uploaded_file:
            try:
                image = load_image(uploaded_file)
            except ConversionError as e:
                st.error(f"❌ {e}")
            else:
                st.image(normalize(image), caption="Original Image", width="stretch")
                st.text(f"Original format: {image.format}")
                st.text(f"Size: {image.width} × {image.height} px")

    with col2:
        if image is not None:
            st.write("### Conversion Options")
            fmt, options = format_options("single", image)
            # Results are kept in session state so they survive reruns, and are
            # only shown while the file and settings still match.
            signature = (uploaded_file.file_id, fmt.label, repr(options))

            if st.button("Convert Image", key="single_convert"):
                try:
                    with st.spinner("Converting..."):
                        st.session_state.single_result = (signature, convert(image, fmt, options, uploaded_file.name))
                except ConversionError as e:
                    st.session_state.pop("single_result", None)
                    st.error(f"❌ {e}")

            saved = st.session_state.get("single_result")
            if saved and saved[0] == signature:
                result = saved[1]
                st.image(result.preview, caption="Converted Image", width="stretch")
                st.download_button(
                    label=f"Download {fmt.label}",
                    data=result.data,
                    file_name=result.filename,
                    mime=result.mime,
                    on_click="ignore",
                )
                st.success(f"✅ Image converted to {fmt.label} ({len(result.data) / 1024:,.1f} KB)")

with tab_batch:
    st.subheader("Batch Convert Images")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_files = st.file_uploader(
            "Upload multiple images", type=INPUT_EXTENSIONS, accept_multiple_files=True, key="batch_upload"
        )
        if uploaded_files:
            st.write(f"📁 **{len(uploaded_files)} files selected**")
            for file in uploaded_files:
                st.write(f"  • {file.name}")

    with col2:
        if uploaded_files:
            st.write("### Conversion Settings")
            fmt, options = format_options("batch")
            signature = (tuple(f.file_id for f in uploaded_files), fmt.label, repr(options))

            if st.button("Convert All Images", key="batch_convert"):
                converted, failed = [], []
                progress = st.progress(0.0, text="Converting images...")
                for i, file in enumerate(uploaded_files, start=1):
                    try:
                        converted.append(convert(load_image(file), fmt, options, file.name))
                    except ConversionError as e:
                        failed.append((file.name, str(e)))
                    progress.progress(i / len(uploaded_files), text=f"Converted {i}/{len(uploaded_files)}")
                progress.empty()
                st.session_state.batch_result = (signature, converted, failed)

            saved = st.session_state.get("batch_result")
            if saved and saved[0] == signature:
                _, converted, failed = saved
                for name, error in failed:
                    st.error(f"❌ {name}: {error}")

                if converted:
                    st.success(f"✅ Successfully converted {len(converted)} images!")

                    zip_buffer = io.BytesIO()
                    used_names = set()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for result in converted:
                            name, n = result.filename, 1
                            while name in used_names:
                                stem, ext = result.filename.rsplit(".", 1)
                                name, n = f"{stem}_{n}.{ext}", n + 1
                            used_names.add(name)
                            zf.writestr(name, result.data)

                    st.download_button(
                        label="📦 Download all as ZIP",
                        data=zip_buffer.getvalue(),
                        file_name="converted_images.zip",
                        mime="application/zip",
                        on_click="ignore",
                        type="primary",
                    )

                    st.write("### Converted Files")
                    cols = st.columns(min(3, len(converted)))
                    for idx, result in enumerate(converted):
                        with cols[idx % 3]:
                            st.download_button(
                                label=f"📥 {result.filename}",
                                data=result.data,
                                file_name=result.filename,
                                mime=result.mime,
                                key=f"download_{idx}",
                                on_click="ignore",
                            )
