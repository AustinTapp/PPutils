import os
import shutil

def move_contents_to_subdirectory(directory):
    folders = os.listdir(directory)
    for folder in folders:
        top = os.path.join(directory, folder)
        for root, dirs, files in os.walk(top):
            if not dirs and files:
                for file in files:
                    source_path = os.path.join(root, file)
                    destination_path = os.path.join(top, file)
                    shutil.copy(source_path, destination_path)

def delete_directories(folder_path):
    all_folders = os.listdir(folder_path)
    for folder in all_folders:
        for filename in os.listdir(os.path.join(folder_path, folder)):
            file_path = os.path.join(folder_path, folder, filename)

            if os.path.isdir(file_path):
                shutil.rmtree(file_path)

# Provide the directory path here
directory_path = 'E:\\Data\\Brain\\ADNI'
move_contents_to_subdirectory(directory_path)
#delete_directories(directory_path)