import os
import zipfile
import shutil
from tkinter import filedialog, Tk, Listbox, Button, Checkbutton, IntVar, messagebox, Text, Scrollbar, Toplevel, \
    DoubleVar
from tkinter.ttk import Progressbar
import send2trash
from tkinter import TclError
from shutil import Error as ShutilError
import threading

# get the value of the USERPROFILE environment variable
userprofile = os.environ['USERPROFILE']

# construct the path to your downloads directory
path_to_downloads_dir = os.path.join(userprofile, 'Downloads')

# create a temporary directory for holding files before deletion
temp_dir = os.path.join(userprofile, 'Temp')
os.makedirs(temp_dir, exist_ok=True)


# function to set the backup directory
def set_backup_dir():
    try:
        root = Tk()
        root.withdraw()  # Hide the main window
        messagebox.showinfo('Prompt', 'Select the directory for comparison.')
        backup_directory = filedialog.askdirectory()  # Show the file dialog and get the selected directory
    except TclError:
        # If the environment does not support a GUI, ask the user to input the directory path
        backup_directory = input('Please enter the path to the backup directory: ')
    return backup_directory


# function to compare contents of two zip files
def compare_zip_files(file1, file2):
    with zipfile.ZipFile(file1, 'r') as zip1, zipfile.ZipFile(file2, 'r') as zip2:
        return sorted(zip1.namelist()) == sorted(zip2.namelist())


# function to check and delete duplicates
def check_and_delete_duplicates(backup_directory, progress_var, history_text):
    # get a list of all files in the downloads directory
    downloads_files = os.listdir(path_to_downloads_dir)

    # get a list of all files in the backup directory
    backup_files = os.listdir(backup_directory)

    # iterate over all files in the downloads directory
    for i, filename in enumerate(downloads_files):
        # update the progress bar
        progress_var.set(i / len(downloads_files) * 100)

        # construct the full path to the file
        file_path = os.path.join(path_to_downloads_dir, filename)
        backup_file_path = os.path.join(backup_directory, filename)

        # if a file in the downloads directory exists in the backup directory
        if filename in backup_files:
            # if the file is a zip file, compare the contents
            if zipfile.is_zipfile(file_path) and zipfile.is_zipfile(backup_file_path):
                if not compare_zip_files(file_path, backup_file_path):
                    continue

            # ask for confirmation before moving the file to the temporary directory
            confirm = messagebox.askyesno('Confirmation',
                                          f'I found {filename} in {backup_directory}. Do you want to move the original to the temporary folder?')
            if confirm:
                try:
                    # try to move the file to the temporary directory
                    shutil.move(file_path, os.path.join(temp_dir, filename))
                    messagebox.showinfo('Moved File', f'Moved {file_path} to the temporary directory')
                    history_text.insert('end', f'Moved {file_path} to the temporary directory\n')
                except ShutilError as e:
                    print(f'Error occurred: {e}')
        else:
            # if the file does not exist in the backup directory, ask if the user wants to copy it
            confirm = messagebox.askyesno('Confirmation',
                                          f'{filename} does not exist in {backup_directory}. Would you like to copy it?')
            if confirm:
                try:
                    # try to copy the file
                    shutil.copy(file_path, backup_file_path)
                    messagebox.showinfo('Copied File', f'Copied {file_path} to {backup_file_path}')
                    history_text.insert('end', f'Copied {file_path} to {backup_file_path}\n')
                except ShutilError as e:
                    print(f'Error occurred: {e}')

    # set the progress bar to 100% when done
    progress_var.set(100)


# usage
backup_dir = set_backup_dir()  # Show the file dialog and get the selected directory

# create a GUI for systems that support it
try:
    root = Tk()
    root.title('Temporary Directory')

    # create a listbox to display the files in the temporary directory
    listbox = Listbox(root)
    listbox.pack()

    # create a list of checkboxes to select the files for the operation
    checkboxes = []
    for filename in os.listdir(temp_dir):
        var = IntVar()
        checkbox_widget = Checkbutton(root, text=filename, variable=var)
        checkbox_widget.pack()
        checkboxes.append((checkbox_widget, var))

    # create a button to delete the selected files
    def delete_files():
        for checkbox_widget, var in checkboxes:
            if var.get():
                try:
                    send2trash.send2trash(os.path.join(temp_dir, checkbox_widget.cget('text')))
                    print(f'Moved {checkbox_widget.cget("text")} from the temporary directory to the Recycle Bin')
                except Exception as e:
                    print(f'Error occurred: {e}')
        # refresh the listbox and checkboxes
        refresh()


    delete_button = Button(root, text='Delete', command=delete_files)
    delete_button.pack()

    # create a button to restore the selected files to their original location
    def restore_files():
        for checkbox_widget, var in checkboxes:
            if var.get():
                try:
                    shutil.move(os.path.join(temp_dir, checkbox_widget.cget('text')),
                                os.path.join(path_to_downloads_dir, checkbox_widget.cget('text')))
                    print(f'Restored {checkbox_widget.cget("text")} to the original location')
                except Exception as e:
                    print(f'Error occurred: {e}')
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
        for checkbox_widget, var in checkboxes:
            checkbox_widget.destroy()

        # clear the list of checkboxes
        checkboxes.clear()

        # update the listbox and checkboxes
        for filename in os.listdir(temp_dir):
            listbox.insert('end', filename)
            var = IntVar()
            checkbox_widget = Checkbutton(root, text=filename, variable=var)
            checkbox_widget.pack()
            checkboxes.append((checkbox_widget, var))


    # create a history window
    history_window = Toplevel(root)
    history_window.title('History')

    # create a Text widget to display the history
    history_text = Text(history_window)
    history_text.pack()

    # create a Scrollbar for the Text widget
    scrollbar = Scrollbar(history_window, command=history_text.yview)
    scrollbar.pack(side='right', fill='y')
    history_text['yscrollcommand'] = scrollbar.set

    # create a progress bar
    progress_var = DoubleVar()
    progress_bar = Progressbar(root, length=200, mode='determinate', variable=progress_var)
    progress_bar.pack()

    # start a new thread to check and delete duplicates
    threading.Thread(target=check_and_delete_duplicates, args=(backup_dir, progress_var, history_text)).start()

    root.mainloop()
except TclError:
    # create a text-based interface for terminal users
    while True:
        print('Files in the temporary directory:')
        for i, filename in enumerate(os.listdir(temp_dir), start=1):
            print(f'{i}. {filename}')
        print('Enter the number of the file you want to delete, or "q" to quit:')
        choice = input()
        if choice.lower() == 'q':
            break
        try:
            filename = os.listdir(temp_dir)[int(choice) - 1]
            send2trash.send2trash(os.path.join(temp_dir, filename))
            print(f'Moved {filename} from the temporary directory to the Recycle Bin')
        except Exception as e:
            print(f'Error occurred: {e}')
