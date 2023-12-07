import os
import zipfile
import shutil
from tkinter import filedialog, Tk, Listbox, Button, Toplevel, Checkbutton, IntVar, messagebox
import send2trash

# get the value of the USERPROFILE environment variable
userprofile = os.environ['USERPROFILE']

# construct the path to your downloads directory
path_to_downloads_dir = os.path.join(userprofile, 'Downloads')


# function to set the backup directory
def set_backup_dir():
    try:
        root = Tk()
        root.withdraw()  # Hide the main window
        dir_name = filedialog.askdirectory()  # Show the file dialog and get the selected directory
    except Exception:
        # If the environment does not support a GUI, ask the user to input the directory path
        dir_name = input('Please enter the path to the backup directory: ')
    return dir_name


# function to compare contents of two zip files
def compare_zip_files(file1, file2):
    with zipfile.ZipFile(file1, 'r') as zip1, zipfile.ZipFile(file2, 'r') as zip2:
        return sorted(zip1.namelist()) == sorted(zip2.namelist())


# function to check and delete duplicates
def check_and_delete_duplicates(backup_directory):
    # get a list of all files in the downloads directory
    downloads_files = os.listdir(path_to_downloads_dir)

    # get a list of all files in the backup directory
    backup_files = os.listdir(backup_directory)

    # create a temporary directory for holding files before deletion
    temp_dir = os.path.join(userprofile, 'Temp')
    os.makedirs(temp_dir, exist_ok=True)

    # iterate over all files in the downloads directory
    for file in downloads_files:
        # construct the full path to the file
        file_path = os.path.join(path_to_downloads_dir, file)
        backup_file_path = os.path.join(backup_directory, file)

        # if a file in the downloads directory exists in the backup directory
        if file in backup_files:
            # if the file is a zip file, compare the contents
            if zipfile.is_zipfile(file_path) and zipfile.is_zipfile(backup_file_path):
                if not compare_zip_files(file_path, backup_file_path):
                    continue

            # ask for confirmation before moving the file to the temporary directory
            confirm = messagebox.askyesno('Confirmation',
                                          f'I found {file} in {backup_directory}. Do you want to move the original to the temporary folder?')
            if confirm:
                try:
                    # try to move the file to the temporary directory
                    shutil.move(file_path, os.path.join(temp_dir, file))
                    print(f'Moved {file_path} to the temporary directory')
                except Exception as e:
                    print(f'Error occurred: {e}')
        else:
            # if the file does not exist in the backup directory, ask if the user wants to copy it
            confirm = messagebox.askyesno('Confirmation',
                                          f'{file} does not exist in {backup_directory}. Would you like to copy it?')
            if confirm:
                try:
                    # try to copy the file
                    shutil.copy(file_path, backup_file_path)
                    print(f'Copied {file_path} to {backup_file_path}')
                except Exception as e:
                    print(f'Error occurred: {e}')

    # create a GUI for systems that support it
    try:
        root = Tk()
        root.title('Temporary Directory')

        # create a listbox to display the files in the temporary directory
        listbox = Listbox(root)
        listbox.pack()

        # create a list of checkboxes to select the files for the operation
        checkboxes = []
        for file in os.listdir(temp_dir):
            var = IntVar()
            checkbox = Checkbutton(root, text=file, variable=var)
            checkbox.pack()
            checkboxes.append((checkbox, var))

        # create a button to delete the selected files
        def delete_files():
            for checkbox, var in checkboxes:
                if var.get():
                    send2trash.send2trash(os.path.join(temp_dir, checkbox.cget('text')))
                    print(f'Moved {checkbox.cget("text")} from the temporary directory to the Recycle Bin')
            # refresh the listbox and checkboxes
            refresh()

        delete_button = Button(root, text='Delete', command=delete_files)
        delete_button.pack()

        # create a button to restore the selected files to their original location
        def restore_files():
            for checkbox, var in checkboxes:
                if var.get():
                    shutil.move(os.path.join(temp_dir, checkbox.cget('text')),
                                os.path.join(path_to_downloads_dir, checkbox.cget('text')))
                    print(f'Restored {checkbox.cget("text")} to the original location')
            # refresh the listbox and checkboxes
            refresh()

        restore_button = Button(root, text='Restore', command=restore_files)
        restore_button.pack()

        # create a button to cancel the window
        cancel_button = Button(root, text='Cancel', command=root.destroy)
        cancel_button.pack()

        # function to refresh the listbox and checkboxes
        def refresh():
            # clear the listbox
            listbox.delete(0, 'end')

            # destroy the checkboxes
            for checkbox, var in checkboxes:
                checkbox.destroy()

            # clear the list of checkboxes
            checkboxes.clear()

            # update the listbox and checkboxes
            for file in os.listdir(temp_dir):
                listbox.insert('end', file)
                var = IntVar()
                checkbox = Checkbutton(root, text=file, variable=var)
                checkbox.pack()
                checkboxes.append((checkbox, var))

        root.mainloop()
    except Exception:
        # create a text-based interface for terminal users
        while True:
            print('Files in the temporary directory:')
            for i, file in enumerate(os.listdir(temp_dir), start=1):
                print(f'{i}. {file}')
            print('Enter the number of the file you want to delete, or "q" to quit:')
            choice = input()
            if choice.lower() == 'q':
                break
            try:
                file = os.listdir(temp_dir)[int(choice) - 1]
                send2trash.send2trash(os.path.join(temp_dir, file))
                print(f'Moved {file} from the temporary directory to the Recycle Bin')
            except Exception as e:
                print(f'Error occurred: {e}')


# usage
backup_dir = set_backup_dir()  # Show the file dialog and get the selected directory
check_and_delete_duplicates(backup_dir)
