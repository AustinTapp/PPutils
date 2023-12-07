import os
import subprocess
import json
import shutil
import SimpleITK as sitk
from concurrent.futures import ThreadPoolExecutor


def remove_empty_dirs(path):
    for dir_entry in os.scandir(path):
        if dir_entry.is_dir():
            remove_empty_dirs(dir_entry.path)
            if not os.listdir(dir_entry.path):
                os.rmdir(dir_entry.path)


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
        for j in range(len(patient_subfolder_with_path)):
            # print(patient_subfolder_with_path[j].split('\\')[-1])
            patient_scanfiles_with_path = [f.path for f in os.scandir(patient_subfolder_with_path[j]) if f.is_dir()]
            for l in range(len(patient_scanfiles_with_path)):
                DCM2niix_i = [DCM2niix, '-o', nifti_folder, '-f',
                                 patient_subfolder_with_path[j].split("\\")[-1] + "_" + str(l),
                                 '-z', 'y', '-9',
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
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+".nii.gz"),
                          os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_CT.nii.gz"))
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Eq_1.nii.gz"),
                            os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_CT.nii.gz"))
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_1.nii.gz"),
                            os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_CT.nii.gz"))
            except FileNotFoundError:
                pass
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_Eq_1.nii.gz"),
                            os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_CT.nii.gz"))
            except FileNotFoundError:
                pass
        if data[key] == 'MR':
            base_name, ext = os.path.splitext(json_path)
            FLAIRss = "FLAIR"
            T2ss = "T2"
            check_modality = data["SeriesDescription"]
            if check_modality.find(FLAIRss) != -1:
                try:
                    shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"),
                              os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_FLAIR.nii.gz"))
                except FileNotFoundError:
                    pass
            if T2ss in check_modality and FLAIRss not in check_modality:
                try:
                    shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"),
                              os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_T2.nii.gz"))
                except FileNotFoundError:
                    pass
            else:
                try:
                    shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"),
                              os.path.join(nifti_folder, base_name.split('\\')[-1].split('_')[0]+"_T1.nii.gz"))
                except FileNotFoundError:
                    pass


def cleanup(nifti_folder):
    for file_name in os.listdir(nifti_folder):
        if file_name.endswith('.json'):
            file_path = os.path.join(nifti_folder, file_name)
            os.remove(file_path)


def Resample(data_dir):
    reoriented_folder = os.path.join(data_dir, "Reoriented")

    resampled_folder = os.path.join(data_dir, "Resampled")
    isExist = os.path.exists(resampled_folder)
    if not isExist:
        os.makedirs(resampled_folder)

    spacing = [1.0, 1.0, 1.0]
    resampled = sitk.ResampleImageFilter()
    resampled.SetInterpolator(sitk.sitkGaussian)
    resampled.SetOutputSpacing(spacing)

    for filename in os.listdir(reoriented_folder):
        image = sitk.ReadImage(os.path.join(reoriented_folder, filename))

        size = [int(sz * spc) for sz, spc in zip(image.GetSize(), image.GetSpacing())]
        resampled.SetSize(size)
        resampled.SetOutputDirection(image.GetDirection())
        resampled.SetOutputOrigin(image.GetOrigin())
        resampled = resampled.Execute(image)
        sitk.WriteImage(resampled, os.path.join(resampled_folder, filename, "_resampled.nii.gz"))

    return resampled_folder


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
    # original_dir = "D:\\Data\\CNH_Paired\\Normal"
    nifti_folder = "D:\\Data\\CNH_Paired\\asNifti"
    # reoriented_dir = "D:\\Data\\CNH_Paired\\Reoriented"
    # noBed_dir = "D:\\Data\\CNH_Paired\\NoBedCTs"

    remove_empty_dirs(data_dir)
    nifti_folder = DCM2niix(data_dir)
    rename(nifti_folder)
    cleanup(nifti_folder)
    resampled_folder = Resample(data_dir)

    #DirCheck(original_dir, asNifti_dir)
    print("Done!")