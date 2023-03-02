import os
import subprocess
import json
import shutil
from concurrent.futures import ThreadPoolExecutor

def remove_empty_dirs(path):
    count = 0
    for dir_entry in os.scandir(path):
        if dir_entry.is_dir():
            remove_empty_dirs(dir_entry.path)
            if not os.listdir(dir_entry.path):
                os.rmdir(dir_entry.path)
                count += 1
    return count


def DCM2niix(data_dir):
    list_subfolders_with_paths = [f.path for f in os.scandir(data_dir) if f.is_dir()]
    DCM2niix = "C:\\Users\\Austin Tapp\\Documents\\ImagePreProcessUtils\\dcm2niix\\build\\install\\bin\\dcm2niix.exe"

    DCM2niix_execs = []

    for i in range(len(list_subfolders_with_paths)):
        nifti_folder = os.path.join(data_dir, "asNifti")
        # print(nifti_folder)
        isExist = os.path.exists(nifti_folder)
        if not isExist:
            os.makedirs(nifti_folder)
        patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]
        for j in range(0, len(patient_subfolder_with_path)):
            # print(patient_subfolder_with_path[j].split('\\')[-1])
            patient_scanfiles_with_path = [f.path for f in os.scandir(patient_subfolder_with_path[j]) if f.is_dir()]
            patient_subfolder = patient_subfolder_with_path[j].split("\\")[-1]
            if not os.path.exists(os.path.join(nifti_folder, f"{patient_subfolder}_0_CT.nii.gz")):
                for l in range(len(patient_scanfiles_with_path)):
                    DCM2niix_i = [DCM2niix, '-o', nifti_folder, '-f',
                                     patient_subfolder_with_path[j].split("\\")[-1] + "_" + str(l),
                                     '-z', 'y', '-6',
                                     patient_scanfiles_with_path[l]]
                    DCM2niix_execs.append(DCM2niix_i)
                    # print(patient_imagefiles_with_path[k])
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in DCM2niix_execs]
        for f in results:
            f.result()

    return nifti_folder


def rename(nifti_folder):
    jsons = [file for file in os.listdir(nifti_folder) if file.endswith('.json')]
    for file in jsons:
        json_path = os.path.join(nifti_folder, file)
        with open(json_path) as json_file:
            data = json.load(json_file)
        key = 'Modality'
        if data[key] == 'CT':
            base_name, ext = os.path.splitext(json_path)
            try:
                os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1]+".nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Eq_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_Eq_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                pass
        if data[key] == 'MR':
            base_name, ext = os.path.splitext(json_path)
            FLAIRss = "FLAIR"
            T2ss = "T2"
            check_modality = data["SeriesDescription"]
            if check_modality.find(FLAIRss) != -1:
                try:
                    os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_FLAIR.nii.gz")
                except FileNotFoundError:
                    pass
            if T2ss in check_modality and FLAIRss not in check_modality:
                if base_name.endswith("_e1"):
                    b_name = base_name.split('\\')[-1]
                    try:
                        shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"),
                                    os.path.join(nifti_folder, b_name.split("_")[0] + "_" + b_name.split("_")[1] + "_T2.nii.gz"))
                    except FileNotFoundError:
                        pass
                if base_name.endswith("_e2"):
                    b_name = base_name.split('\\')[-1]
                    try:
                        shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"),
                                    os.path.join(nifti_folder, b_name.split("_")[0] + "_" + b_name.split("_")[1] + "_T2.nii.gz"))
                    except FileNotFoundError:
                        pass
                else:
                    try:
                        os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_T2.nii.gz")
                    except FileNotFoundError:
                        pass
            else:
                try:
                    os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_T1.nii.gz")
                except FileNotFoundError:
                    pass


def cleanup(nifti_folder):
    for file_name in os.listdir(nifti_folder):
        if file_name.endswith('.json'):
            file_path = os.path.join(nifti_folder, file_name)
            os.remove(file_path)


def DirCheck(first, second):
    count = 0
    firstfiles = os.listdir(first)
    secondfiles = os.listdir(second)
    for file in secondfiles:
        file = file.split("_")[0]
        #if 'CT' in file:
        if file not in firstfiles:
            print(file)
            count += 1
    print(count)


if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Paired"
    emptys = remove_empty_dirs(data_dir)
    print(f"{emptys} directories removed")

    asNifti_dir = DCM2niix(data_dir)
    rename(asNifti_dir)
    cleanup(asNifti_dir)
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")
