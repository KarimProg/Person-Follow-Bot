import os
import sys

# Ensure GStreamer is in the PATH
gstreamer_path = "D:\\gstreamer\\1.0\\msvc_x86_64\\bin"
if not os.path.exists(gstreamer_path):
    print(f"GStreamer binaries not found in {gstreamer_path}. Please check the installation.")
    sys.exit(1)

os.environ["PATH"] += os.pathsep + gstreamer_path

try:
    import gi
except ImportError:
    print("The 'gi' module is not installed. Please install it using 'pip install pycairo PyGObject'.")
    sys.exit(1)

try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
except ValueError as e:
    print(f"Error loading GStreamer: {e}")
    sys.exit(1)

# Initialize GStreamer
Gst.init(None)

# Print GStreamer version
print(Gst.version())
