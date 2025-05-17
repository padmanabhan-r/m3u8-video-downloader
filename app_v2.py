import sys
import subprocess
import os
import time
import base64
from datetime import datetime
import logging
import tempfile

# Ensure Streamlit is available
try:
    import streamlit as st
except ModuleNotFoundError:
    sys.exit("Error: Streamlit is not installed. Please install it with 'pip install streamlit' and try again.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("StreamGrab")

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
        margin-bottom: 1rem;
    }
    .log-container {
        background-color: #0e1117;
        color: #a0a0a0;
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
        height: 200px;
        overflow-y: auto;
        margin-top: 20px;
    }
    .footer {
        margin-top: 2rem;
        text-align: center;
        color: #a0a0a0;
        font-size: 0.8rem;
    }
    .file-info {
        color: #a0a0a0;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    .log-success {
        color: #00cc66;
    }
    .log-error {
        color: #ff3333;
    }
    .log-info {
        color: #1e90ff;
    }
    .directory-picker {
        margin-top: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for logs
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(message, level="INFO"):
    """Add a log message to the session state and print to console"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    
    # Add to session state
    st.session_state.logs.append((level, log_entry))
    
    # Log to console as well
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)

def get_directory_html():
    """Generate HTML for directory selection"""
    return """
    <input type="file" webkitdirectory directory id="dirpicker" style="display: none;" onchange="updatePath()">
    <button onclick="document.getElementById('dirpicker').click();" 
        style="background-color: #1e90ff; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; border: none; cursor: pointer;">
        Browse...
    </button>
    <script>
    function updatePath() {
        const input = document.getElementById('dirpicker');
        if (input.files.length > 0) {
            const path = input.files[0].webkitRelativePath.split('/')[0];
            document.getElementById('selected-dir').value = path;
            // Notify Streamlit that the value has changed
            const event = new Event('input', { bubbles: true });
            document.getElementById('selected-dir').dispatchEvent(event);
        }
    }
    </script>
    """

# Header with logo
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown('<div style="font-size: 3rem;">🎬</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="header-container"><span class="logo-text">StreamGrab</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Download streaming videos with ease</p>', unsafe_allow_html=True)

st.markdown('<div class="custom-card">', unsafe_allow_html=True)
st.subheader("M3U8 Video Converter")

# File uploader
m3u8_files = st.file_uploader(
    "Select one or more .m3u8 files",
    type=["m3u8"],
    accept_multiple_files=True,
    key="m3u8_uploader"
)

# Output directory selection
st.markdown("### Output Directory")
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown('<div class="directory-picker">', unsafe_allow_html=True)
    st.markdown(get_directory_html(), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # Default to a user's downloads folder if possible
    default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    output_dir = st.text_input(
        "Save location",
        value=default_downloads,
        key="selected-dir"
    )

# Ensure output directory exists
if output_dir:
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            add_log(f"Created directory: {output_dir}", "INFO")
        except Exception as e:
            add_log(f"Failed to create directory: {str(e)}", "ERROR")

# Video quality options
output_quality = st.select_slider(
    "Video Quality",
    options=["Low", "Medium", "High", "Original"],
    value="Original",
    help="Low=640p, Medium=720p, High=1080p, Original=source quality"
)

# Hardware acceleration option
use_hw_accel = st.checkbox(
    "Use Hardware Acceleration",
    value=False,
    help="Speeds up conversion but may not work on all systems"
)

def convert_m3u8_to_mp4(m3u8_file, output_path, quality, use_hw_accel):
    """Convert M3U8 to MP4 with progress tracking and logging"""
    # Create a temporary file for the M3U8 content
    with tempfile.NamedTemporaryFile(suffix='.m3u8', delete=False) as tmp_file:
        tmp_file.write(m3u8_file.getvalue())
        input_path = tmp_file.name
    
    try:
        add_log(f"Starting conversion of {m3u8_file.name}", "INFO")
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-y", "-stats"]
        
        # Add hardware acceleration if requested
        if use_hw_accel:
            # Try to detect platform and add appropriate HW accel
            import platform
            system = platform.system().lower()
            if system == 'windows':
                cmd.extend(["-hwaccel", "dxva2"])
            elif system == 'darwin':  # macOS
                cmd.extend(["-hwaccel", "videotoolbox"])
            else:  # Linux and others
                cmd.extend(["-hwaccel", "vaapi"])
            
            add_log(f"Using hardware acceleration for {system}", "INFO")
        
        cmd.extend([
            "-protocol_whitelist", "file,http,https,tcp,tls",
            "-i", input_path,
        ])
        
        # Set quality
        if quality != "Original":
            scale_map = {"Low": "640:-1", "Medium": "1280:-1", "High": "1920:-1"}
            cmd.extend(["-vf", f"scale={scale_map[quality]}", "-c:v", "libx264", "-c:a", "aac"])
        else:
            cmd.extend(["-c", "copy"])
        
        cmd.append(output_path)
        
        add_log(f"Running command: {' '.join(cmd)}", "INFO")
        
        # Execute conversion process with real-time output capturing
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor the process output
        while process.poll() is None:
            stderr_line = process.stderr.readline().strip()
            if stderr_line:
                if "frame=" in stderr_line:
                    # This is progress info, update the latest log instead of adding new
                    progress_info = stderr_line.split('time=')[1].split(' ')[0] if 'time=' in stderr_line else "processing"
                    add_log(f"Converting {m3u8_file.name} - Time: {progress_info}", "INFO")
                elif stderr_line.lower().startswith('error'):
                    add_log(stderr_line, "ERROR")
                time.sleep(0.1)  # Small delay to prevent UI freezing
        
        # Get the return code
        return_code = process.poll()
        
        # Clean up temp file
        os.unlink(input_path)
        
        if return_code == 0:
            add_log(f"Successfully converted {m3u8_file.name} to {output_path}", "SUCCESS")
            return True
        else:
            remaining_errors = process.stderr.read()
            add_log(f"Failed to convert {m3u8_file.name}: {remaining_errors}", "ERROR")
            return False
            
    except Exception as e:
        add_log(f"Error in conversion process: {str(e)}", "ERROR")
        # Clean up temp file
        if os.path.exists(input_path):
            os.unlink(input_path)
        return False

# Convert button
if st.button("Convert All Videos", use_container_width=True, type="primary"):
    if not m3u8_files:
        st.warning("Please select at least one .m3u8 file first.")
    elif not output_dir or not os.path.isdir(output_dir):
        st.error("Please select a valid output directory.")
    else:
        # Clear previous logs
        st.session_state.logs.clear()
        
        # Create progress bar
        progress_bar = st.progress(0)
        
        # Process each file
        for idx, m3u8_file in enumerate(m3u8_files, start=1):
            base = os.path.splitext(m3u8_file.name)[0]
            output_path = os.path.join(output_dir, f"{base}.mp4")
            
            # Show current file being processed
            st.subheader(f"Processing {m3u8_file.name} ({idx}/{len(m3u8_files)})")
            
            # Convert the file
            success = convert_m3u8_to_mp4(m3u8_file, output_path, output_quality, use_hw_accel)
            
            # Update progress
            progress_bar.progress(idx / len(m3u8_files))
        
        # Final status
        if len(m3u8_files) > 0:
            add_log(f"Completed processing {len(m3u8_files)} files", "INFO")

# Log viewer
st.markdown("### Conversion Logs")
log_container = st.container()

with log_container:
    log_html = '<div class="log-container">'
    for level, log in st.session_state.logs:
        if "SUCCESS" in level:
            log_html += f'<div class="log-success">{log}</div>'
        elif "ERROR" in level:
            log_html += f'<div class="log-error">{log}</div>'
        else:
            log_html += f'<div class="log-info">{log}</div>'
    log_html += '</div>'
    st.markdown(log_html, unsafe_allow_html=True)

# Help section
with st.expander("Need Help?"):
    st.markdown("""
    ### Quick Guide
    1. **Select your .m3u8 files** using the file uploader above
    2. **Choose an output directory** where videos will be saved
    3. **Select video quality** - lower quality for faster conversion, original for best quality
    4. **Click "Convert All Videos"** to start the process
    5. **Monitor the logs** for conversion progress and any issues

    ### Troubleshooting
    - **No conversion happening?** Make sure FFmpeg is installed on your system
    - **Failed conversion?** Check if the M3U8 file is valid and accessible
    - **Slow conversion?** Try enabling Hardware Acceleration
    """)

# Footer
st.markdown(
    f'<div class="footer">StreamGrab v1.1.0 | © {datetime.now().year} | Made with ❤️ for streamers and viewers</div>',
    unsafe_allow_html=True
)
