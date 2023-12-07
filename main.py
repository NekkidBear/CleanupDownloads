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
        root_window = Tk()
        root_window.withdraw()  # Hide the main window
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
def check_and_delete_duplicates(backup_directory, progress_variable, log):
    # get a list of all files in the downloads directory
    downloads_files = os.listdir(path_to_downloads_dir)

    # get a list of all files in the backup directory
    backup_files = os.listdir(backup_directory)

    # iterate over all files in the downloads directory
    for x, file_name in enumerate(downloads_files):
        # update the progress bar
        progress_variable.set(x / len(downloads_files) * 100)

        # construct the full path to the file
        file_path = os.path.join(path_to_downloads_dir, file_name)
        backup_file_path = os.path.join(backup_directory, file_name)

        # if a file in the downloads directory exists in the backup directory
        if file_name in backup_files:
            # if the file is a zip file, compare the contents
            if zipfile.is_zipfile(file_path) and zipfile.is_zipfile(backup_file_path):
                if not compare_zip_files(file_path, backup_file_path):
                    continue

            # ask for confirmation before moving the file to the temporary directory
            confirm = messagebox.askyesno('Confirmation',
                                          f'I found {file_name} in {backup_directory}. Do you want to move the original to the temporary folder?')
            if confirm:
                try:
                    # try to move the file to the temporary directory
                    shutil.move(file_path, os.path.join(temp_dir, file_name))
                    messagebox.showinfo('Moved File', f'Moved {file_path} to the temporary directory')
                    log.insert('end', f'Moved {file_path} to the temporary directory\n')
                except ShutilError as move_error:
                    print(f'Error occurred: {move_error}')
        else:
            # if the file does not exist in the backup directory, ask if the user wants to copy it
            confirm = messagebox.askyesno('Confirmation',
                                          f'{file_name} does not exist in {backup_directory}. Would you like to copy it?')
            if confirm:
                try:
                    # try to copy the file
                    shutil.copy(file_path, backup_file_path)
                    messagebox.showinfo('Copied File', f'Copied {file_path} to {backup_file_path}')
                    log.insert('end', f'Copied {file_path} to {backup_file_path}\n')
                except ShutilError as move_error:
                    print(f'Error occurred: {move_error}')

    # set the progress bar to 100% when done
    progress_variable.set(100)


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
        for checkbox_widget_del, var_state in checkboxes:
            if var_state.get():
                try:
                    send2trash.send2trash(os.path.join(temp_dir, checkbox_widget_del.cget('text')))
                    print(f'Moved {checkbox_widget_del.cget("text")} from the temporary directory to the Recycle Bin')
                except Exception as del_error:
                    print(f'Error occurred: {del_error}')
        # refresh the listbox and checkboxes
        refresh()


    delete_button = Button(root, text='Delete', command=delete_files)
    delete_button.pack()

    # create a button to restore the selected files to their original location
    def restore_files():
        for checkbox_widget_restore, var_restore_state in checkboxes:
            if var_restore_state.get():
                try:
                    shutil.move(os.path.join(temp_dir, checkbox_widget_restore.cget('text')),
                                os.path.join(path_to_downloads_dir, checkbox_widget_restore.cget('text')))
                    print(f'Restored {checkbox_widget_restore.cget("text")} to the original location')
                except Exception as rest_error:
                    print(f'Error occurred: {rest_error}')
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
        for checkbox_widget_refresh, var_state in checkboxes:
            checkbox_widget_refresh.destroy()

        # clear the list of checkboxes
        checkboxes.clear()

        # update the listbox and checkboxes
        for file_name in os.listdir(temp_dir):
            listbox.insert('end', file_name)
            var_state = IntVar()
            checkbox_widget_refresh = Checkbutton(root, text=file_name, variable=var_state)
            checkbox_widget_refresh.pack()
            checkboxes.append((checkbox_widget_refresh, var_state))


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
