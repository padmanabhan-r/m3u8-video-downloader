import sys

# Ensure Streamlit is available
try:
    import streamlit as st
except ModuleNotFoundError:
    sys.exit("Error: Streamlit is not installed. Please install it with 'pip install streamlit' and try again.")

import subprocess
import os
import time
import base64
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="StreamGrab - M3U8 Video Downloader",
    page_icon="🎬",
    layout="wide",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .css-1d391kg {
        padding-top: 3rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #262730;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e90ff;
    }
    .download-btn {
        background-color: #1e90ff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: none;
        font-weight: bold;
        width: 100%;
        cursor: pointer;
    }
    .download-btn:hover {
        background-color: #0078d7;
    }
    .custom-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .logo-text {
        color: #1e90ff;
        margin-left: 10px;
        font-weight: bold;
        font-size: 2.5rem;
    }
    .subtitle {
        color: #a0a0a0;
        font-style: italic;
        margin-bottom: 2rem;
    }
    .progress-container {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0e1117;
        padding: 10px;
        text-align: center;
        color: #a0a0a0;
        font-size: 0.8rem;
    }
    .file-info {
        color: #a0a0a0;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    .status-success {
        color: #00cc66;
        font-weight: bold;
    }
    .status-error {
        color: #ff3333;
        font-weight: bold;
    }
    .status-info {
        color: #1e90ff;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown('<div style="font-size: 3rem;">🎬</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="header-container"><span class="logo-text">StreamGrab</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Download streaming videos with ease</p>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🏠 Home", "⚙️ Settings", "❓ Help"])

with tab1:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Upload Your M3U8 Files")

    # Multiple file uploader
    m3u8_files = st.file_uploader(
        "Select one or more .m3u8 files",
        type=["m3u8"],
        accept_multiple_files=True,
        key="m3u8_uploader"
    )

    # Output directory
    output_dir = st.text_input(
        "Download Directory",
        value="./downloads",
        help="Folder where converted videos will be saved"
    )
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        st.info(f"Created directory: {output_dir}")

    # Video quality
    output_quality = st.select_slider(
        "Video Quality",
        options=["Low", "Medium", "High", "Original"],
        value="Original"
    )

    # Convert button
    convert_all = st.button("Convert All Videos", use_container_width=True)

    if convert_all:
        if m3u8_files:
            overall_progress = st.progress(0)
            summary = []

            for idx, m3u8_file in enumerate(m3u8_files, start=1):
                # Save temp m3u8
                input_path = os.path.join(output_dir, f"tmp_{idx}.m3u8")
                with open(input_path, "wb") as f:
                    f.write(m3u8_file.getvalue())

                # Derive output file name
                base = os.path.splitext(m3u8_file.name)[0]
                output_path = os.path.join(output_dir, f"{base}.mp4")

                # Build ffmpeg command
                cmd = [
                    "ffmpeg",
                    "-protocol_whitelist", "file,http,https,tcp,tls",
                    "-i", input_path,
                ]
                if output_quality != "Original":
                    scale_map = {"Low": "640:-1", "Medium": "1280:-1", "High": "1920:-1"}
                    cmd += ["-vf", f"scale={scale_map[output_quality]}", "-c:v", "libx264", "-c:a", "aac"]
                else:
                    cmd += ["-c", "copy"]
                cmd.append(output_path)

                # Run conversion
                with st.spinner(f"Converting {m3u8_file.name}..."):
                    result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    summary.append(f"✅ {m3u8_file.name} → {output_path}")
                else:
                    err = result.stderr.splitlines()[-1] if result.stderr else "Unknown error"
                    summary.append(f"❌ {m3u8_file.name} failed: {err}")

                # Clean up temp file
                os.remove(input_path)

                # Update progress
                overall_progress.progress(idx / len(m3u8_files))

            # Show summary
            st.markdown("### Conversion Summary")
            for line in summary:
                st.markdown(line)
        else:
            st.warning("Please select at least one .m3u8 file first.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Advanced Settings")

    col1, col2 = st.columns(2)
    with col1:
        ffmpeg_path = st.text_input("FFmpeg Path", value="ffmpeg", help="Path to the FFmpeg executable")
        enable_hardware_accel = st.checkbox("Enable Hardware Acceleration", value=False,
                                            help="Use GPU for faster processing if available")
    with col2:
        download_dir = st.text_input("Download Directory", value="./", help="Where to save downloaded videos")
        keep_temp_files = st.checkbox("Keep Temporary Files", value=False,
                                      help="Don't delete temporary files after processing")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("FFmpeg Command Customization")
    custom_args = st.text_area("Additional FFmpeg Arguments", help="Add custom FFmpeg arguments separated by spaces")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("How to Use StreamGrab")

    st.markdown("""
    1. **Upload your .m3u8 files** using the file uploader on the Home tab  
    2. **Set the download directory** where videos will be saved  
    3. **Choose your preferred quality** setting  
    4. **Click the Convert All Videos button** to start sequential conversion  
    5. **Wait for the process to complete** - you can monitor progress in real-time  
    6. **Find your videos** in the specified download folder
    """)

    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

    st.subheader("Troubleshooting")
    st.markdown("""
    - **Error: FFmpeg not found** - Make sure FFmpeg is installed on your system and available in your PATH  
    - **Failed to convert** - Check if the M3U8 file is valid and accessible  
    - **No audio in output** - The stream might not contain an audio track  
    - **Slow conversion** - Consider using the hardware acceleration option in Settings
    """)

    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

    expander = st.expander("About M3U8 Files")
    expander.markdown("""
    M3U8 files are playlist files used for streaming media. They contain URLs to media segments  
    and are commonly used in HTTP Live Streaming (HLS), a protocol developed by Apple for  
    streaming audio and video over HTTP.

    This application helps you download and combine these segments into a single video file  
    for offline viewing.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(
    '<div class="footer">StreamGrab v1.0.0 | © ' +
    str(datetime.now().year) +
    ' | Made with ❤️ for streamers and viewers</div>',
    unsafe_allow_html=True
)
