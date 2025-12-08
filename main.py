import sys
import os
import subprocess
import threading
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox,
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit, QDialog, QDialogButtonBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

SETTINGS_FILE = os.path.expanduser("~/.flac_converter_settings.json")

class LogDialog(QDialog):
    def __init__(self, logs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FFmpeg Logs")
        self.resize(600, 400)
        layout = QVBoxLayout()

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlainText(logs)
        layout.addWidget(self.log_view)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_logs)
        layout.addWidget(copy_button)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.logs = logs

    def copy_logs(self):
        QApplication.clipboard().setText(self.logs)

class FLACConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.directory = ''
        self.output_directory = ''
        self.files_to_convert = []
        self.logs = ''
        self.stop_flag = False
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle('Converter')
        self.resize(600, 400)

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(20, 20, 20))
        dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(90, 90, 90))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(dark_palette)

        self.layout = QVBoxLayout()

        self.label = QLabel('Choose a directory with .mp4/.mkv files')
        self.layout.addWidget(self.label)

        self.select_button = QPushButton('Select Input Directory')
        self.select_button.clicked.connect(self.select_directory)
        self.layout.addWidget(self.select_button)

        self.output_label = QLabel('Select output directory (default: same as input)')
        self.layout.addWidget(self.output_label)

        self.output_button = QPushButton('Select Output Directory')
        self.output_button.clicked.connect(self.select_output_directory)
        self.layout.addWidget(self.output_button)

        self.file_list = QListWidget()
        self.layout.addWidget(self.file_list)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton('Start Conversion')
        self.start_button.clicked.connect(self.start_conversion)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Conversion')
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.layout.addLayout(button_layout)

        self.log_button = QPushButton('Show FFmpeg Logs')
        self.log_button.clicked.connect(self.show_logs)
        self.log_button.setEnabled(False)
        self.layout.addWidget(self.log_button)

        self.setLayout(self.layout)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.directory or os.path.expanduser("~"))
        if directory:
            self.directory = directory
            self.save_settings()
            self.label.setText(f"Selected input directory: {self.directory}")
            self.list_files()

    def select_output_directory(self):
        msg_box = QMessageBox()
        msg_box.setText("Do you want to reset to default (same as input directory)?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.No)
        response = msg_box.exec_()

        if response == QMessageBox.Yes:
            self.output_directory = ''
            self.save_settings()
            self.output_label.setText('Output directory reset to default (same as input)')
            return

        if response == QMessageBox.No:
            directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_directory or os.path.expanduser("~"))
            if directory:
                self.output_directory = directory
                self.save_settings()
                self.output_label.setText(f"Selected output directory: {self.output_directory}")(f"Selected output directory: {self.output_directory}")

    def list_files(self):
        self.file_list.clear()
        self.files_to_convert.clear()

        for filename in os.listdir(self.directory):
            if filename.endswith(('.mp4', '.mkv', '.MP4')) and not filename.startswith('converted'):
                full_path = os.path.join(self.directory, filename)
                self.files_to_convert.append(full_path)
                size = os.path.getsize(full_path) / (1024 * 1024)
                item = QListWidgetItem(f"{filename} - {size:.2f} MB")
                item.setFlags(Qt.ItemIsEnabled)
                self.file_list.addItem(item)

        self.start_button.setEnabled(bool(self.files_to_convert))
        self.stop_button.setEnabled(False)
        self.log_button.setEnabled(False)
        self.logs = ''
        self.progress_bar.setValue(0)

    def start_conversion(self):
        self.stop_flag = False
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        thread = threading.Thread(target=self.run_conversion)
        thread.start()

    def run_conversion(self):
        total = len(self.files_to_convert)
        self.logs = ''

        for index, filepath in enumerate(self.files_to_convert):
            if self.stop_flag:
                self.logs += "Conversion stopped by user.\n"
                break

            filename = os.path.basename(filepath)
            out_dir = self.output_directory or os.path.dirname(filepath)
            new_filename = os.path.join(out_dir, f"converted_{filename}")

            cmd = [
                "ffmpeg", "-i", filepath,
                "-c:v", "copy",
                "-c:a", "flac",
                "-y", new_filename
            ]

            try:
                process = subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.logs += f"--- {filename} ---\n" + process.stdout + process.stderr + "\n"
            except subprocess.CalledProcessError as e:
                self.logs += f"--- ERROR: {filename} ---\n" + e.stdout + e.stderr + "\n"
                QMessageBox.warning(self, "Conversion Error", f"Failed to convert {filename}")

            progress = int(((index + 1) / total) * 100)
            self.progress_bar.setValue(progress)

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_button.setEnabled(True)
        #QMessageBox.information(self, "Done", "Conversion finished or stopped.")

    def stop_conversion(self):
        self.stop_flag = True

    def show_logs(self):
        log_dialog = LogDialog(self.logs, self)
        log_dialog.exec_()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    self.directory = data.get('last_directory', '')
                    self.output_directory = data.get('output_directory', '')
                    if os.path.isdir(self.directory):
                        self.label.setText(f"Last used input directory: {self.directory}")
                        self.list_files()
                    if os.path.isdir(self.output_directory):
                        self.output_label.setText(f"Selected output directory: {self.output_directory}")
            except Exception:
                pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({
                    'last_directory': self.directory,
                    'output_directory': self.output_directory
                }, f)
        except Exception:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = FLACConverter()
    converter.show()
    sys.exit(app.exec_())
