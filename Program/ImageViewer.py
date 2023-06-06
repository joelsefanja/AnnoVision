import sys, subprocess, os, json
from PyQt5.QtCore import Qt, QTimer, QStandardPaths
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Image Viewer")
        self.setWindowState(Qt.WindowMaximized)  # Set window to fullscreen

        # Create the main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create the first row layout
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(10, 20, 10, 20)

        buttons = ['open image', 'predict', 'save as']
        self.buttons = []
        # Create three buttons and add them to the first row layout
        for b in buttons:
            button = QPushButton(b)
            button.setStyleSheet("background-color: lightblue; padding: 20px; font-size: 32px")
            row1_layout.addWidget(button)
            self.buttons.append(button)

        # Create the second row layout
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)

        # Create an empty label for the image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("background-color: white; border: none;")

        # Add the label to the second row layout
        row2_layout.addWidget(self.image_label)

        # Add the row layouts to the main layout
        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)

        # Connect the first button to open an image
        self.buttons[0].clicked.connect(self.open_image)

        # Connect the second button to execute a subprocess command
        self.buttons[1].clicked.connect(self.run_subprocess_command)

        # Variable to store the file path
        self.file_path = ""

    def open_image(self):
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        options = QFileDialog.Options()
        # options |= QFileDialog.D
        #
        # ontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", default_dir,
                                                   "Image Files (*.png *.jpg *.jpeg *.bmp)",
                                                   options=options)

        if file_path:
            self.file_path = file_path  # Store the file path
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))

    def run_subprocess_command(self):
        if self.file_path:
            subprocess_command = f"python ../yolov7/detect.py --weights ../yolov7/yolov7-tiny.pt --conf 0.25 --img-size 640 --source  {self.file_path} --save-txt"  # Replace with the actual subprocess command
            subprocess.run(subprocess_command, shell=True)

            detect_dir = './runs/detect'
            folders = sorted(os.listdir(detect_dir), key=lambda x: os.path.getmtime(os.path.join(detect_dir, x)),
                             reverse=True)
            newest_folder = folders[0]
            images_dir = os.path.join(detect_dir, newest_folder)
            image_files = sorted(os.listdir(images_dir))
            if image_files:
                first_image_path = os.path.join(images_dir, image_files[0])
                pixmap = QPixmap(first_image_path)
                self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
            else:
                print("No image found in the newest folder.")
        else:
            print("No image file selected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_()) 
