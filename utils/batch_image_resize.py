import cv2
import os

# Define source and destination folders
source_folder = '../app/images/new_world/2560x1440/'  # Replace with your source folder path
destination_folder = 'new_imgs/'  # Replace with your destination folder path

# Create the destination folder if it doesn't exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# Iterate through all files in the source folder
for filename in os.listdir(source_folder):
    # Check if the file is an image (you may want to add more file format checks)
    if filename.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        # Read the image from the source folder
        img = cv2.imread(os.path.join(source_folder, filename))

        # Get the original dimensions
        height, width, _ = img.shape

        # Resize the image by 1.5x
        new_height = int(height * 1.5)
        new_width = int(width * 1.5)
        resized_img = cv2.resize(img, (new_width, new_height))

        # Save the resized image to the destination folder
        new_filename = os.path.splitext(filename)[0] + '.png'  # You can change the file format if needed
        cv2.imwrite(os.path.join(destination_folder, new_filename), resized_img)

print("Images have been duplicated and resized.")