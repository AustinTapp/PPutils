import SimpleITK as sitk
import pandas as pd
from datetime import datetime
import os
import zipfile

def extract_last_zip(directory):
    # Get the list of files and directories in the specified directory
    data_dir = "E:\\Data\\FlyWheel\\UG_High_DICOMs\\SUBJECTS"
    contents = os.listdir(directory)

    # Filter only zip files
    zip_files = [file for file in contents if file.endswith('.zip')]

    if zip_files:
        case = directory.split('\\')[5]
        # If zip files are found, choose the last one
        last_zip = zip_files[-1]

        # Get the absolute path of the last zip file
        zip_file_path = os.path.join(directory, last_zip)

        # Get the first folder of the absolute path
        first_folder = os.path.basename(os.path.normpath(directory))

        # Extract the zip file
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # Extract the contents of the zip file
                new_dir = os.path.join(data_dir, case)
                zip_ref.extractall(new_dir)
        except:
            pass

        print(f"Zip file '{last_zip}' extracted to '{os.path.join(directory, first_folder)}'.")
    else:
        # If no zip files are found, recursively search in subdirectories
        for item in contents:
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # Recursively call the function for subdirectories
                extract_last_zip(item_path)


def get_bdays(excel_file_path, path):
    directories = os.listdir(path)
    for directory in directories:
                # Get the list of files and directories in the specified directory
        contents = os.listdir(os.path.join(path, directory))

        # Iterate through subdirectories
        for item in contents:
            item_path = os.path.join(path, directory, item)
            image = os.listdir(item_path)
            try:
                image = image[0]
                single_file_reader = sitk.ImageFileReader()
                single_file_reader.SetFileName(os.path.join(item_path, image))
                single_dcm = single_file_reader.Execute()
                birthday = single_dcm.GetMetaData('0010|0030')
                birthday = datetime.strptime(birthday, '%Y%m%d').strftime('%Y-%m-%d')

                # Read existing Excel file or create a new one
                try:
                    df = pd.read_excel(excel_file_path)
                except FileNotFoundError:
                    df = pd.DataFrame(columns=['Case', 'PatientBirthday'])

                # Add a new row with DicomFilePath and PatientBirthday
                new_row = {'Case': directory, 'PatientBirthday': birthday}
                df = df._append(new_row, ignore_index=True)

                # Write the updated DataFrame to the Excel file
                df.to_excel(excel_file_path, index=False)
                print(f"Patient's birthday added to '{excel_file_path}'.")

            except:
                print(f"there was an error with case {directory}")
                continue


if __name__ == '__main__':
    data_dir = "E:\\Data\\FlyWheel\\UG_High_DICOMs\\SUBJECTS"
    excel_file_path = "E:\\Data\\FlyWheel\\UG_High_DICOMs\\birthdays.xlsx"
    extract_last_zip(data_dir)
    get_bdays(excel_file_path, data_dir)
    print("Done!")