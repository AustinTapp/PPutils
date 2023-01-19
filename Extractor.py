import os
import subprocess
import json
import shutil
import glob
import time
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
                DCM2niix_args = ['-o', nifti_folder, '-f',
                                 patient_subfolder_with_path[j].split("\\")[-1] + "_" + str(l),
                                 '-z', 'y', '-9',
                                 patient_scanfiles_with_path[l]]
                # print(patient_imagefiles_with_path[k])
                subprocess.call([DCM2niix] + DCM2niix_args)
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
                continue
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                continue
        if data[key] == 'MR':
            base_name, ext = os.path.splitext(json_path)
            FLAIRss = "FLAIR"
            T2ss = "T2"
            check_modality = data["SeriesDescription"]
            if check_modality.find(FLAIRss) != -1:
                try:
                    os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_FLAIR.nii.gz")
                except FileNotFoundError:
                    continue
            if T2ss in check_modality and FLAIRss not in check_modality:
                try:
                    os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_T2.nii.gz")
                except FileNotFoundError:
                    continue
            else:
                try:
                    os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1] + ".nii.gz"), base_name + "_T1.nii.gz")
                except FileNotFoundError:
                    continue


def cleanup(nifti_folder):
    nifti_folder = "D:\\Data\\CNH_Paired\\asNifti"
    for file_name in os.listdir(nifti_folder):
        if file_name.endswith('.json'):
            file_path = os.path.join(nifti_folder, file_name)
            os.remove(file_path)


def ReorientToITK(data_dir):
    reoriented_folder = os.path.join(data_dir, "Reoriented")
    isExist = os.path.exists(reoriented_folder)
    if not isExist:
        os.makedirs(reoriented_folder)
    list_subfolders_with_paths = [f.path for f in os.scandir(data_dir+"\\Normal") if f.is_dir()]
    for i in range(len(list_subfolders_with_paths)):
        nifti_folder = os.path.join(data_dir, "asNifti")
        patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]
        for j in range(len(patient_subfolder_with_path)):

            single_file = [file for file in os.listdir(patient_subfolder_with_path[j])]
            single_file = single_file[int(len(single_file)/2)]

            single_file_reader = sitk.ImageFileReader()
            single_file_reader.SetFileName(os.path.join(patient_subfolder_with_path[j], single_file))
            single_dcm = single_file_reader.Execute()
            modality = single_dcm.GetMetaData('0008|0060')

            if modality != 'CT':
                continue
            else:
                DCMfiles_path = patient_subfolder_with_path[j]
                DCM_reader = sitk.ImageSeriesReader()
                dicom_names = DCM_reader.GetGDCMSeriesFileNames(DCMfiles_path)
                DCM_reader.SetFileNames(dicom_names)
                dicom_image = DCM_reader.Execute()

                case = list_subfolders_with_paths[i].split("\\")[-1]
                match = [nifti for nifti in os.listdir(nifti_folder) if 'CT' in nifti and case in nifti]
                if len(match) > 0:
                    nifti_image = sitk.ReadImage(os.path.join(nifti_folder, match[0]))

                    elastix = sitk.ElastixImageFilter()
                    elastix.SetFixedImage(dicom_image)
                    elastix.SetMovingImage(nifti_image)
                    elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
                    elastix.Execute()
                    realigned_nifti = elastix.GetResultImage()

                    sitk.WriteImage(realigned_nifti, os.path.join(nifti_folder, reoriented_folder, match[0]))
    return reoriented_folder

def BedRemoval(data_dir, reoriented_folder):
    remove_bed = "C:\\Users\\Austin Tapp\\Documents\\ImagePreProcessUtils\\BedRemoveFilter\\build\\Debug\\BedRemovalFilter.exe"

    nobed_folder = os.path.join(data_dir, "NoBedCTs")
    isExist = os.path.exists(nobed_folder)
    if not isExist:
        os.makedirs(nobed_folder)

    remove_bed_execs = []

    list_CTs_with_paths = [f.path for f in os.scandir(reoriented_folder)]
    for i in range(len(list_CTs_with_paths)):
        nobed = list_CTs_with_paths[i].split("\\")[-1]
        nobed = nobed.split("_")[0]
        remove_bed_i = [remove_bed, list_CTs_with_paths[i], os.path.join(nobed_folder, nobed + "_noBed.nii.gz")]
        remove_bed_execs.append(remove_bed_i)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in remove_bed_execs]
        for f in results:
            f.result()


if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Paired"
    remove_empty_dirs(data_dir)
    nifti_folder = DCM2niix(data_dir)
    rename(nifti_folder)
    cleanup(nifti_folder)
    reoriented_folder = ReorientToITK(data_dir)
    BedRemoval(data_dir, "D:\\Data\\CNH_Paired\\Reoriented")

    #TODO bias correction
    print("Done!")