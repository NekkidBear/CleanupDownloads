import os
import zipfile
import shutil
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QPushButton, QProgressBar, \
    QListWidget, QCheckBox, QListWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import send2trash
from shutil import Error as ShutilError

# get the value of the USERPROFILE environment variable
userprofile = os.environ['USERPROFILE']

# construct the path to your downloads directory
path_to_downloads_dir = os.path.join(userprofile, 'Downloads')

# create a temporary directory for holding files before deletion
temp_dir = os.path.join(userprofile, 'Temp')
os.makedirs(temp_dir, exist_ok=True)


# function to set the backup directory
def set_backup_dir():
    backup_directory = QFileDialog.getExistingDirectory(None, 'Select the directory for comparison.')
    return backup_directory


# function to compare contents of two zip files
def compare_zip_files(file1, file2):
    with zipfile.ZipFile(file1, 'r') as zip1, zipfile.ZipFile(file2, 'r') as zip2:
        return sorted(zip1.namelist()) == sorted(zip2.namelist())


class Worker(QThread):
    progress = pyqtSignal(int)
    info = pyqtSignal(str)

    def __init__(self, backup_directory):
        super().__init__()
        self.backup_directory = backup_directory

    # function to check and delete duplicates
    def run(self):
        # get a list of all files in the downloads directory
        downloads_files = os.listdir(path_to_downloads_dir)

        # get a list of all files in the backup directory
        backup_files = os.listdir(self.backup_directory)

        # iterate over all files in the downloads directory
        for i, filename in enumerate(downloads_files):
            # update the progress bar
            self.progress.emit(i / len(downloads_files) * 100)

            # construct the full path to the file
            file_path = os.path.join(path_to_downloads_dir, filename)
            backup_file_path = os.path.join(self.backup_directory, filename)

            # if a file in the downloads directory exists in the backup directory
            if filename in backup_files:
                # if the file is a zip file, compare the contents
                if zipfile.is_zipfile(file_path) and zipfile.is_zipfile(backup_file_path):
                    if not compare_zip_files(file_path, backup_file_path):
                        continue

                # ask for confirmation before moving the file to the temporary directory
                confirm = QMessageBox.question(None, 'Confirmation',
                                               f'I found {filename} in {self.backup_directory}. Do you want to move the original to the temporary folder?',
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    try:
                        # try to move the file to the temporary directory
                        shutil.move(file_path, os.path.join(temp_dir, filename))
                        self.info.emit(f'Moved {file_path} to the temporary directory')
                    except ShutilError as e:
                        print(f'Error occurred: {e}')
            else:
                # if the file does not exist in the backup directory, ask if the user wants to copy it
                confirm = QMessageBox.question(None, 'Confirmation',
                                               f'{filename} does not exist in {self.backup_directory}. Would you like to copy it?',
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    try:
                        # try to copy the file
                        shutil.copy(file_path, backup_file_path)
                        self.info.emit(f'Copied {file_path} to {backup_file_path}')
                    except ShutilError as e:
                        print(f'Error occurred: {e}')

        # set the progress bar to 100% when done
        self.progress.emit(100)


# usage
app = QApplication([])
backup_dir = set_backup_dir()  # Show the file dialog and get the selected directory

window = QWidget()
layout = QVBoxLayout()
window.setLayout(layout)

listbox = QListWidget()
layout.addWidget(listbox)

progress_bar = QProgressBar()
layout.addWidget(progress_bar)

worker = Worker(backup_dir)
worker.progress.connect(progress_bar.setValue)
worker.info.connect(listbox.addItem)
worker.start()

delete_button = QPushButton('Delete')
layout.addWidget(delete_button)


def delete_files():
    for i in range(listbox.count()):
        item = listbox.item(i)
        if item.checkState() == Qt.Checked:
            try:
                send2trash.send2trash(os.path.join(temp_dir, item.text()))
                print(f'Moved {item.text()} from the temporary directory to the Recycle Bin')
            except Exception as e:
                print(f'Error occurred: {e}')
    # refresh the listbox
    refresh()


delete_button.clicked.connect(delete_files)

restore_button = QPushButton('Restore')
layout.addWidget(restore_button)


def restore_files():
    for i in range(listbox.count()):
        item = listbox.item(i)
        if item.checkState() == Qt.Checked:g
            try:
                shutil.move(os.path.join(temp_dir, item.text()), os.path.join(path_to_downloads_dir, item.text()))
                print(f'Restored {item.text()} to the original location')
            except Exception as e:
                print(f'Error occurred: {e}')
    # refresh the listbox
    refresh()


restore_button.clicked.connect(restore_files)


def refresh():
    listbox.clear()
    for filename in os.listdir(temp_dir):
        item = QListWidgetItem(filename)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        listbox.addItem(item)


window.show()
app.exec_()
