import os
import SimpleITK as sitk
from glob import glob
import csv

def Extract(data_dir):
    patient_data = []

    subfolders = glob(data_dir+"/*", recursive=True)
    for folder in subfolders:
        for i in range(1, 25):
            if folder.split("\\")[-1] == str(i) + "M":
                for dirpath, dirnames, filenames in os.walk(folder):
                    if not dirnames:
                        continue
                    if dirnames[0] == "DICOMOBJ":
                        patient_DICOM_with_path = os.path.join(dirpath+"\\", dirnames[0])
                        files = [file for file in os.listdir(patient_DICOM_with_path)]
                        single_file = files[int(len(files) / 2)]

                        single_file_reader = sitk.ImageFileReader()
                        single_file_reader.SetFileName(os.path.join(patient_DICOM_with_path, single_file))
                        single_dcm = single_file_reader.Execute()
                        birthday = single_dcm.GetMetaData('0010|0030')
                        birthday = insert_character(birthday, 4)
                        birthday = insert_character(birthday, 7)
                        gender = single_dcm.GetMetaData('0010|0040')
                        scanAge = folder.split("\\")[-1]
                        ID = dirpath.split("\\")[-2]
                        sort = i

                        patient_data.append([birthday, gender, scanAge, ID, sort])

    write_to_csv(data_dir+"_AntonioCases.csv", patient_data)
    return 0

def write_to_csv(file_path, data):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write headers
        headers = ["DOB", "Gender", "Age at time of Scan Folder", "Original ID", "To sort by age"]
        writer.writerow(headers)

        # Write data rows
        for row in data:
            writer.writerow(row)


def insert_character(birthday, num_letters, char="-"):
    new_text = ''
    count = 0
    for letter in birthday:
        new_text += letter
        count += 1
        if count == num_letters:
            new_text += char
    return new_text

if __name__ == '__main__':
    data_dir = "E:\\Data\\Skull\\NormalCases_All"
    Extract(data_dir)
    print("Done!")