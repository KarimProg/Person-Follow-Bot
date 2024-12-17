import os

def set_class_id_to_zero(labels_folder_path):
    """
    This function iterates through all text files in the labels folder and sets the 
    first number (class ID) in every line to 0.
    
    Args:
    labels_folder_path (str): Path to the folder containing YOLO label files.
    """
    # Check if the folder exists
    if not os.path.exists(labels_folder_path):
        print(f"Error: The folder '{labels_folder_path}' does not exist.")
        return

    # Loop through all files in the folder
    for filename in os.listdir(labels_folder_path):
        if filename.endswith(".txt"):  # Only process .txt files
            file_path = os.path.join(labels_folder_path, filename)
            
            with open(file_path, 'r') as file:
                lines = file.readlines()
            
            # Change the first number (class ID) of every line to 0
            modified_lines = ['0' + line[line.find(' '):] for line in lines]

            # Write the modified labels back to the file
            with open(file_path, 'w') as file:
                file.writelines(modified_lines)

            print(f"Processed: {filename} - Total labels updated: {len(lines)}")
    
    print("✅ Class IDs successfully set to 0.")

# Specify the path to the folder containing YOLO labels
labels_folder_path = "path/to/your/labels/folder"

# Call the function
set_class_id_to_zero("dataset2/train/labels")
set_class_id_to_zero("dataset2/valid/labels")
