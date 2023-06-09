import os
from PyQt5.QtGui import QPixmap

class ImageSwitcher:
    def __init__(self):
        self.folder_dir = None
        self.folder_images = []
        self.folder_current_image_index = None
        self.image = None
        self.scene = None

    def load_folder_images(self):
        # Check if the folder directory is valid
        if not os.path.isdir(self.folder_dir):
            print("Invalid folder directory")
            return

        # Retrieve the image files in the folder directory
        self.folder_images = [file for file in os.listdir(self.folder_dir) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]

        # Check if there are any image files in the folder
        if not self.folder_images:
            print("No image files found in the folder")
            return

        # Set the current image index to the first image
        self.folder_current_image_index = 0

        # Load and display the first image
        self.update_image()

    def update_image(self):
        # Build the path to the current image
        image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])

        # Load the image and display it in the scene
        self.image = QPixmap(image_path)
        self.scene.clear()
        self.scene.addPixmap(self.image)

        # Read labels associated with the image
        self.read_labels(image_path)

    def read_labels(self, image_path):
        # Code to read labels associated with the image
        pass

