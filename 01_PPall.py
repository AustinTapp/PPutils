import os
import subprocess
import json
import shutil
from concurrent.futures import ThreadPoolExecutor


def split(path):

    image_folder = os.path.join(data_dir, "DCMs")
    isExist = os.path.exists(image_folder)
    if not isExist:
        os.makedirs(image_folder)

    seg_folder = os.path.join(data_dir, "Segments")
    isExist = os.path.exists(seg_folder)
    if not isExist:
        os.makedirs(seg_folder)

    list_subfolders_with_paths = [f.path for f in os.scandir(path) if f.is_dir()]
    for i in range(len(list_subfolders_with_paths)):
        patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]
        for j in range(0, len(patient_subfolder_with_path)):
            folder_name = patient_subfolder_with_path[j].split("\\")[-2].split("-")[-1]
            # print(patient_subfolder_with_path[j].split('\\')[-1])
            patient_scanfiles_with_path = [f.path for f in os.scandir(patient_subfolder_with_path[j]) if f.is_dir()]
            for l in range(len(patient_scanfiles_with_path)):
                old_name = patient_scanfiles_with_path[l].split("\\")[-1]
                if "RTSTRUCT" in old_name:
                    shutil.move(patient_scanfiles_with_path[l], seg_folder)
                    os.rename(os.path.join(seg_folder, old_name), os.path.join(seg_folder, folder_name))
                elif "NA" in old_name:
                    shutil.move(patient_scanfiles_with_path[l], seg_folder)
                    os.rename(os.path.join(seg_folder, old_name), os.path.join(seg_folder, folder_name))
                else:
                    shutil.move(patient_scanfiles_with_path[l], image_folder)
                    os.rename(os.path.join(image_folder, old_name), os.path.join(image_folder, folder_name))
    return image_folder


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
    DCM2niix_exe = "C:\\Users\\Austin Tapp\\Documents\\ImagePreProcessUtils\\dcm2niix\\build\\install\\bin\\dcm2niix.exe"
    DCM2niix_execs = []
    DCM2niix_i = None

    nifti_folder = os.path.join(data_dir, "asNifti")
    isExist = os.path.exists(nifti_folder)
    if not isExist:
        os.makedirs(nifti_folder)

    upper_paths = [f.path for f in os.scandir(data_dir) if f.is_dir()]

    for h in range(len(upper_paths)):
        list_subfolders_with_paths = [f.path for f in os.scandir(upper_paths[h]) if f.is_dir()]
        #for i in range(len(list_subfolders_with_paths)):
            #patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]
        for j in range(0, len(list_subfolders_with_paths)):
            # print(patient_subfolder_with_path[j].split('\\')[-1])
            #patient_scanfiles_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[j]) if f.is_dir()]
            patient_subfolder = list_subfolders_with_paths[j].split("\\")[-2]
            DCM2niix_i = [DCM2niix_exe, '-o', nifti_folder, '-f',
                          patient_subfolder,
                          '-z', 'y', '-6',
                          list_subfolders_with_paths[j]]
            DCM2niix_execs.append(DCM2niix_i)
            # for l in range(len(patient_scanfiles_with_path)):
            #if not os.path.exists(os.path.join(nifti_folder, f"{patient_subfolder}_CT.nii.gz")):
                # print(patient_imagefiles_with_path[k])
    with ThreadPoolExecutor(max_workers=10) as executor:
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
        if file not in firstfiles:
            print(file)
            count += 1
    print(count)


if __name__ == '__main__':
    data_dir = "E:\\Data\\IFA\\IFA_data\\PRS\\AnielDicoms"
    #split(data_dir)
    #emptys = remove_empty_dirs(data_dir)
    #print(f"{emptys} directories removed")

    asNifti_dir = DCM2niix(data_dir)
    rename(asNifti_dir)
    cleanup(asNifti_dir)
    #DirCheck(all_dir, data_dir)
    print("Done!")
