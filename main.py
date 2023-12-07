import os
import zipfile

# get the value of the USERPROFILE environment variable
userprofile = os.environ['USERPROFILE']

# construct the paths to your directories
path_to_downloads_dir = os.path.join(userprofile, 'Downloads')
path_to_backup_dir = 'D:\\blender models'  # replace with your actual backup directory path

# get a list of all files in both directories
downloads_files = os.listdir(path_to_downloads_dir)
backup_files = os.listdir(path_to_backup_dir)


# function to compare contents of two zip files
def compare_zip_files(file1, file2):
    with zipfile.ZipFile(file1, 'r') as zip1, zipfile.ZipFile(file2, 'r') as zip2:
        return sorted(zip1.namelist()) == sorted(zip2.namelist())


# iterate over all files in the downloads directory
for file in downloads_files:
    # if a file in the downloads directory exists in the backup directory
    if file in backup_files:
        # construct the full path to the file
        file_path = os.path.join(path_to_downloads_dir, file)
        backup_file_path = os.path.join(path_to_backup_dir, file)

        # if the file is a zip file, compare the contents
        if zipfile.is_zipfile(file_path) and zipfile.is_zipfile(backup_file_path):
            if not compare_zip_files(file_path, backup_file_path):
                continue

            # ask for confirmation before deleting the file
            confirm = input(f'Do you want to delete {file_path}? (y/n): ')
            if confirm.lower() == 'y':
                try:
                    # try to delete the file
                    os.remove(file_path)
                    print(f'Deleted {file_path}')
                except PermissionError:
                    print(f'Permission denied: {file_path}')
                except Exception as e:
                    print(f'Error occurred: {e}')
