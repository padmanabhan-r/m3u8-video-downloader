import streamlit as st
import subprocess
import tempfile
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
    # Main card
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Upload Your M3U8 File")
    
    # File uploader with better styling
    m3u8_file = st.file_uploader("", type=["m3u8"], key="m3u8_uploader")
    
    if m3u8_file:
        file_size = len(m3u8_file.getvalue()) / 1024  # Size in KB
        st.markdown(f'<p class="file-info">File: {m3u8_file.name} ({file_size:.2f} KB)</p>', unsafe_allow_html=True)
    
    # Output options
    st.subheader("Output Options")
    col1, col2 = st.columns(2)
    
    with col1:
        output_filename = st.text_input("Output Filename", 
                                        value="video.mp4" if not m3u8_file else m3u8_file.name.replace(".m3u8", ".mp4"),
                                        placeholder="Enter filename with .mp4 extension")
    
    with col2:
        output_quality = st.select_slider("Video Quality", 
                                         options=["Low", "Medium", "High", "Original"],
                                         value="Original")
    
    # Download button
    download_col1, download_col2, download_col3 = st.columns([1, 2, 1])
    with download_col2:
        download_button = st.button("Download Video", key="download_btn", use_container_width=True)
    
    # Process the download
    if download_button and m3u8_file and output_filename:
        # Save the uploaded m3u8 file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m3u8") as tmp:
            tmp.write(m3u8_file.getvalue())
            m3u8_path = tmp.name

        # Create progress components
        progress_text = st.empty()
        progress_bar = st.progress(0)
        log_output = st.empty()
        
        # Determine quality settings based on selected option
        quality_params = []
        if output_quality != "Original":
            if output_quality == "Low":
                quality_params = ["-vf", "scale=640:-1"]
            elif output_quality == "Medium":
                quality_params = ["-vf", "scale=1280:-1"]
            elif output_quality == "High":
                quality_params = ["-vf", "scale=1920:-1"]
        
        # ffmpeg command to download video from m3u8
        command = [
            "ffmpeg",
            "-protocol_whitelist", "file,http,https,tcp,tls",
            "-i", m3u8_path,
        ]
        
        # Add quality parameters if any
        if quality_params:
            command.extend(quality_params)
            command.extend(["-c:v", "libx264", "-c:a", "aac"])
        else:
            command.extend(["-c", "copy"])
            
        command.append(output_filename)
        
        # Run the command and capture output in real-time
        progress_text.markdown('<p class="status-info">Starting download process...</p>', unsafe_allow_html=True)
        
        start_time = time.time()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_lines = []
        duration_seconds = None
        current_time = 0
        
        for line in process.stdout:
            output_lines.append(line)
            
            # Try to extract duration information
            if "Duration:" in line and duration_seconds is None:
                duration_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = map(float, duration_str.split(':'))
                duration_seconds = h * 3600 + m * 60 + s
            
            # Try to extract progress information
            if "time=" in line:
                time_str = line.split("time=")[1].split(" ")[0].strip()
                h, m, s = map(float, time_str.split(':'))
                current_time = h * 3600 + m * 60 + s
                
                if duration_seconds:
                    progress = min(current_time / duration_seconds, 1.0)
                    progress_bar.progress(progress)
                    elapsed = time.time() - start_time
                    estimated_total = elapsed / progress if progress > 0 else 0
                    remaining = estimated_total - elapsed
                    
                    progress_text.markdown(
                        f'<p class="status-info">Processing: {progress:.1%} complete '
                        f'(ETA: {int(remaining//60)}m {int(remaining%60)}s)</p>', 
                        unsafe_allow_html=True
                    )
            
            # Show last few lines for feedback
            log_output.markdown(f"""
            ```
            {''.join(output_lines[-5:])}
            ```
            """)

        process.wait()

        if process.returncode == 0:
            progress_bar.progress(1.0)
            progress_text.markdown('<p class="status-success">Download completed successfully!</p>', unsafe_allow_html=True)
            
            # Create download link
            with open(output_filename, "rb") as file:
                btn = st.download_button(
                    label="Save Video to Computer",
                    data=file,
                    file_name=output_filename,
                    mime="video/mp4"
                )
                
            # Video preview
            st.subheader("Video Preview")
            st.video(output_filename)
        else:
            progress_text.markdown('<p class="status-error">Failed to download the video.</p>', unsafe_allow_html=True)
            st.error("Check the log output above for specific errors.")

        # Cleanup temp file
        os.remove(m3u8_path)
        
    elif download_button:
        st.warning("Please upload a .m3u8 file and enter an output filename.")
    
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
    custom_args = st.text_area("Additional FFmpeg Arguments", 
                              help="Add custom FFmpeg arguments separated by spaces")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("How to Use StreamGrab")
    
    st.markdown("""
    1. **Upload your .m3u8 file** using the file uploader on the Home tab
    2. **Set the output filename** for the downloaded video (must end with .mp4)
    3. **Choose your preferred quality** setting
    4. **Click the Download button** to start the download process
    5. **Wait for the process to complete** - you can monitor progress in real-time
    6. **Save the video** to your computer when complete
    """)
    
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    
    st.subheader("Troubleshooting")
    
    st.markdown("""
    - **Error: FFmpeg not found** - Make sure FFmpeg is installed on your system and available in your PATH
    - **Failed to download** - Check if the M3U8 URL is valid and accessible
    - **No audio in output** - The stream might not contain audio, or try changing quality settings
    - **Slow download speed** - Consider using hardware acceleration in Settings tab if available
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
