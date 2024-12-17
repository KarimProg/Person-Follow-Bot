from PIL import Image
import os

# Set the path to the directory with your images
input_folder = 'split_frames'
output_folder = 'resized_frames'

# Create output directory if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Set the target size (640x640)
target_size = (640, 640)

# Loop through all the images in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):  # Add other formats if needed
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)

        # Resize the image
        img_resized = img.resize(target_size)

        # Save the resized image to the output folder
        output_path = os.path.join(output_folder, filename)
        img_resized.save(output_path)

        print(f'Resized and saved: {filename}')

print("All images have been resized to 640x640!")
