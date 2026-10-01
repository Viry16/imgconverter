# 🖼️ Image Format Converter

A powerful, user-friendly web application for converting images between multiple formats with advanced features like batch processing, quality control, and image resizing.

## ✨ Features

- **Multiple Format Support**: Convert between PNG, JPG/JPEG, WEBP, BMP, GIF, TIFF, and ICO formats, and export to SVG
- **Single Image Conversion**: Upload and convert individual images with custom settings
- **Batch Processing**: Convert multiple images at once and download them individually or as a ZIP
- **SVG Export**: Trace images into scalable vector paths, or embed the original pixels in an SVG
- **Quality Control**: Adjust compression quality for JPEG and WEBP formats
- **Image Resizing**: Optional image resizing before conversion
- **Real-time Preview**: View original and converted images side-by-side
- **Smart Format Handling**: Handles transparency, 16-bit/float, CMYK and palette images, and fixes phone photo rotation (EXIF)
- **Friendly Errors**: Corrupted or unsupported files show a message instead of crashing the app
- **Easy Download**: Download converted images directly from the browser

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/imgconverter.git
cd imgconverter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📋 Supported Formats

| Format | Extension | Best For | Notes |
|--------|-----------|----------|-------|
| **PNG** | .png | Graphics & Web | Lossless, supports transparency |
| **JPEG** | .jpg/.jpeg | Photos | Lossy compression, smaller files |
| **WEBP** | .webp | Modern Web | Better compression than PNG/JPEG |
| **BMP** | .bmp | Legacy Systems | Uncompressed or RLE compression |
| **GIF** | .gif | Animations | Supports 256 colors + animation |
| **TIFF** | .tiff | Professional/Print | Lossless, archival quality |
| **ICO** | .ico | Favicons | Small icon format |
| **SVG** | .svg | Logos & Icons | Output only. *Vector trace* makes scalable paths; *Embed raster* wraps the pixels |

## 💡 Usage Tips

### For Photographs
- **Best Format**: JPEG
- **Recommended Quality**: 85-90 for good balance between quality and file size
- The converter automatically handles PNG transparency by adding a white background

### For Graphics & Web Design
- **Best Format**: PNG or WEBP
- PNG for maximum compatibility, WEBP for smaller file sizes
- Supports full transparency preservation

### For Modern Web Applications
- **Best Format**: WEBP
- Provides superior compression and quality
- Widely supported in modern browsers

### For Logos, Icons & Flat Artwork
- **Best Format**: SVG with *Vector trace*
- Use *Black & white* for single-colour marks, and raise *Noise filter* to remove specks
- Photos trace poorly (posterised, large files); use *Embed raster* if you need a photo in SVG form
- Images larger than 1024 px are traced at 1024 px and scaled back up, to keep the app responsive

### For Archival
- **Best Format**: TIFF
- Maintains maximum quality for long-term storage

## 🎯 How to Use

### Single Image Conversion
1. Click the "Single Image" tab
2. Upload an image file
3. Select the desired output format
4. Adjust quality (if applicable) and resize options
5. Click "Convert Image"
6. Download the converted file

### Batch Image Conversion
1. Click the "Batch Convert" tab
2. Upload multiple image files
3. Select the output format
4. Adjust quality settings (if applicable)
5. Click "Convert All Images"
6. Download each converted image, or all of them as a ZIP

## 📦 Requirements

```
streamlit>=1.50.0
Pillow>=10.0.0
vtracer>=0.6.15
```

## 🗂️ Project Structure

```
app.py              Streamlit user interface
converter.py        Image loading and conversion logic (no Streamlit code)
tests/              Tests for converter.py
```

## 🧪 Running Tests

```bash
pip install pytest
pytest
```

## 🛠️ Technologies Used

- **Streamlit** - Web framework for rapid data app development
- **Pillow (PIL)** - Python Imaging Library for image processing
- **VTracer** - Raster-to-vector tracing for SVG export
- **Python 3** - Programming language

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---
