import os
import random
import logging
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QFileDialog, QComboBox, QSpinBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTextEdit
import sys

class ConsoleWidget(QTextEdit):
    def write(self, text):
        self.insertPlainText(text)

class VideoOverlayProcessor:
    def overlay_video(self, args):
        base_file, overlay_file, output_file, scaling_percentage, x_position, y_position, selected_audio = args
        try:
            audio_sources = [overlay_file] if selected_audio == "overlay_audio" else [base_file]
            audio_source = audio_sources[0]  

            command = [
                "ffmpeg",
                "-y",
                "-i", base_file,
                "-i", overlay_file,
                "-i", audio_source,
                "-filter_complex", f"[1:v]scale=iw*{scaling_percentage}/100:ih*{scaling_percentage}/100[top];[0:v][top]overlay=(main_w-overlay_w)*{x_position}/100:(main_h-overlay_h)*{y_position}/100",
                "-map", "2:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                output_file
            ]
            subprocess.run(command, check=True, stderr=subprocess.PIPE)

            subprocess.run(command, shell=True, check=True)
            logging.info(f"Overlayed videos: {base_file}, {overlay_file} -> {output_file}")
        except Exception as e:
            logging.error(f"Error during video overlaying: {e}")
            raise RuntimeError(f"Error during video overlaying: {e}")

    def overlay_videos_sequential(self, input_folder1, input_folder2, output_folder, overlay_position, scaling_percentage, selected_audio):
        positions = [
            (0, 0), (0.5, 0), (1, 0),
            (0, 0.5), (0.5, 0.5), (1, 0.5),
            (0, 1), (0.5, 1), (1, 1)
        ]

        position = positions[overlay_position - 1]
        x_position = int(position[0] * 100)
        y_position = int(position[1] * 100)

        base_files = os.listdir(input_folder1)
        overlay_files = os.listdir(input_folder2)

        for base_filename in base_files:
            if base_filename.endswith(".mp4"):
                overlay_filename = os.path.splitext(base_filename)[0] + ".mp4"

                if overlay_filename in overlay_files:
                    base_file = os.path.join(input_folder1, base_filename)
                    overlay_file = os.path.join(input_folder2, overlay_filename)
                    output_file = os.path.join(output_folder, os.path.splitext(base_filename)[0] + ".mp4")

                    self.overlay_video((base_file, overlay_file, output_file, scaling_percentage, x_position, y_position, selected_audio))

    def overlay_videos_random(self, input_folder1, input_folder2, output_folder, overlay_position, scaling_percentage, selected_audio, num_output_files):
        positions = [
            (0, 0), (0.5, 0), (1, 0),
            (0, 0.5), (0.5, 0.5), (1, 0.5),
            (0, 1), (0.5, 1), (1, 1)
        ]

        position = positions[overlay_position - 1]
        x_position = int(position[0] * 100)
        y_position = int(position[1] * 100)

        base_files = [f for f in os.listdir(input_folder1) if f.endswith(".mp4")]
        overlay_files = [f for f in os.listdir(input_folder2) if f.endswith(".mp4")]

        random.shuffle(base_files)
        random.shuffle(overlay_files)

        num_files_to_merge = min(len(base_files), len(overlay_files), num_output_files)

        for i in range(num_files_to_merge):
            base_filename = base_files[i]
            overlay_filename = overlay_files[i]

            base_file = os.path.join(input_folder1, base_filename)
            overlay_file = os.path.join(input_folder2, overlay_filename)
            output_file = os.path.join(output_folder, os.path.splitext(base_filename)[0] + ".mp4")

            self.overlay_video((base_file, overlay_file, output_file, scaling_percentage, x_position, y_position, selected_audio))

class OverlayGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Overlay Tool by WW")
        self.setGeometry(100, 100, 300, 650)  # Set the width and height here
        self.processor = VideoOverlayProcessor()

        self.init_ui()

    def select_input_folder1(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Tentukan lokasi folder sumber video 1:")
        if folder_path:
            self.input_folder1_entry.setText(folder_path)

    def select_input_folder2(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Tentukan lokasi folder sumber video 2:")
        if folder_path:
            self.input_folder2_entry.setText(folder_path)

    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Tentukan lokasi folder hasil video:")
        if folder_path:
            self.output_folder_entry.setText(folder_path)

    def start_overlay_videos(self):
        sys.stderr = self.console_widget
        
        input_folder1 = self.input_folder1_entry.text()
        input_folder2 = self.input_folder2_entry.text()
        output_folder = self.output_folder_entry.text()
        scaling_percentage = self.scaling_percentage_spinbox.value()
        overlay_position = self.overlay_position_combobox.currentIndex() + 1
        selected_audio = self.audio_source_combobox.currentText()

        method_choice = self.method_combobox.currentText()

        if method_choice == "Nama file sama":
            base_files = [f for f in os.listdir(input_folder1) if f.endswith(".mp4")]
            overlay_files = [os.path.splitext(f)[0] + ".mp4" for f in os.listdir(input_folder2) if f != '.DS_Store.mp4']

            print("Base files:", base_files)
            print("Overlay files:", overlay_files)

            if any(overlay in base_files for overlay in overlay_files):
                self.result_label.setText("Overlaying videos...")

                self.processor.overlay_videos_sequential(input_folder1, input_folder2, output_folder, overlay_position, scaling_percentage, selected_audio)

                self.result_label.setText("Video berhasil dioverlay!")
            else:
                self.result_label.setText("Tidak ada nama file video yang sama utk dioverlay!")

        elif method_choice == "Random":
            num_output_files = self.num_output_spinbox.value()
            self.processor.overlay_videos_random(input_folder1, input_folder2, output_folder, overlay_position, scaling_percentage, selected_audio, num_output_files)
            self.result_label.setText("Video berhasil di overlay!")

    def method_changed(self):
        if self.method_combobox.currentText() == "Nama file sama":
            self.num_output_spinbox.setEnabled(False)
        else:
            self.num_output_spinbox.setEnabled(True)
      
    def close_app(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle("OVERLAY Module")
        self.setGeometry(100, 100, 300, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        title_label = QLabel("OVERLAY TOOL BY WW")  # Set your title here
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Align label to center

        # Create a QFont object with Arial font and bold style
        font = QFont("Arial", pointSize=24, weight=QFont.Weight.Bold)
        title_label.setFont(font)  # Apply the font to the label

        layout.addWidget(title_label)
        # Add a blank widget for spacing
        spacing_widget = QWidget()
        spacing_widget.setFixedHeight(20)  # Adjust the height as needed
        layout.addWidget(spacing_widget)

        self.method_combobox = QComboBox()
        self.method_combobox.addItem("Nama file sama")
        self.method_combobox.addItem("Random")
        layout.addWidget(QLabel("Metode (nama file sama/random):"))
        layout.addWidget(self.method_combobox)
        self.method_combobox.currentTextChanged.connect(self.method_changed)

        self.num_output_spinbox = QSpinBox()
        self.num_output_spinbox.setValue(1)
        layout.addWidget(QLabel("Masukkan target jumlah file video (untuk metode random):"))
        layout.addWidget(self.num_output_spinbox)
        self.num_output_spinbox.setEnabled(False)  # Initially disabled

        self.input_folder1_entry = QLineEdit()
        browse_input1_button = QPushButton("Telusuri")
        browse_input1_button.clicked.connect(self.select_input_folder1)
        layout.addWidget(QLabel("Tentukan lokasi folder sumber video 1:"))
        layout.addWidget(self.input_folder1_entry)
        layout.addWidget(browse_input1_button)

        self.input_folder2_entry = QLineEdit()
        browse_input2_button = QPushButton("Telusuri")
        browse_input2_button.clicked.connect(self.select_input_folder2)
        layout.addWidget(QLabel("Tentukan lokasi folder sumber video 2:"))
        layout.addWidget(self.input_folder2_entry)
        layout.addWidget(browse_input2_button)

        self.output_folder_entry = QLineEdit()
        browse_output_button = QPushButton("Telusuri")
        browse_output_button.clicked.connect(self.select_output_folder)
        layout.addWidget(QLabel("Tentukan lokasi folder hasil video:"))
        layout.addWidget(self.output_folder_entry)
        layout.addWidget(browse_output_button)

        self.scaling_percentage_spinbox = QSpinBox()
        self.scaling_percentage_spinbox.setValue(30)
        layout.addWidget(QLabel("Skala ukuran video overlay:"))
        layout.addWidget(self.scaling_percentage_spinbox)

        self.overlay_positions = [
            "Kiri atas", "Tengah atas", "Kanan atas",
            "Kiri tengah", "Tengah", "Kanan tengah",
            "Kiri bawah", "Tengah bawah", "Kanan bawah"
        ]
        self.overlay_position_combobox = QComboBox()
        self.overlay_position_combobox.addItems(self.overlay_positions)
        layout.addWidget(QLabel("Posisi video overlay:"))
        layout.addWidget(self.overlay_position_combobox)

        self.audio_source_combobox = QComboBox()
        self.audio_source_combobox.addItem("overlay_audio")
        self.audio_source_combobox.addItem("base_audio")
        layout.addWidget(QLabel("Sumber suara:"))
        layout.addWidget(self.audio_source_combobox)

        self.console_widget = ConsoleWidget()  # Create the console widget
        self.console_widget.setVisible(False)  # Set visibility to False initially
        layout.addWidget(self.console_widget)

        sys.stdout = self.console_widget  # Redirect stdout to the custom QTextEdit
        sys.stderr = self.console_widget  # Redirect stderr to the custom QTextEdit

        layout.addStretch()  # Add stretch to provide spacing

        self.result_label = QLabel()
        layout.addWidget(self.result_label)
        
        start_button = QPushButton("Mulai Overlaying")
        start_button.setFixedHeight(start_button.sizeHint().height() * 2)
        
        start_button.clicked.connect(self.start_overlay_videos)
        layout.addWidget(start_button)

        central_widget.setLayout(layout)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    gui = OverlayGUI()
    gui.show()
    sys.exit(app.exec())
