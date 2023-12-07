import os
import re
import subprocess
import SimpleITK as sitk
import warnings
from concurrent.futures import ThreadPoolExecutor

#step 2 (equivalent to MRIpipeline)
#should be run AFTER PPall pipeline
#takes longer, so should be run third while MRI pipeline works on linux

def Reorient(data_dir):
    reoriented_folder = os.path.join(data_dir, "Reoriented")
    isExist = os.path.exists(reoriented_folder)
    if not isExist:
        os.makedirs(reoriented_folder)
    list_subfolders_with_paths = [f.path for f in os.scandir(data_dir) if f.is_dir()]
    for i in range(len(list_subfolders_with_paths)):
        nifti_folder = os.path.join(data_dir, "asNifti")
        patient_nifti_with_path = [f.path for f in os.scandir(nifti_folder)]
        patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]
        for j in range(len(patient_subfolder_with_path)):
            patient_subsub_with_path = [f.path for f in os.scandir(patient_subfolder_with_path[j]) if f.is_dir()]
            for k in range(len(patient_subsub_with_path)):
                patient_DICOM_with_path = [f.path for f in os.scandir(patient_subsub_with_path[k]) if f.is_dir()]
                for l in range(len(patient_DICOM_with_path)):
                    single_file = [file for file in os.listdir(patient_DICOM_with_path[l])]
                    single_file = single_file[int(len(single_file) / 2)]

                    single_file_reader = sitk.ImageFileReader()
                    single_file_reader.SetFileName(os.path.join(patient_DICOM_with_path[l], single_file))
                    single_dcm = single_file_reader.Execute()
                    modality = single_dcm.GetMetaData('0008|0060')

                    if modality == 'CT':
                        try:
                            for m in range(len(patient_nifti_with_path)):
                                case = patient_nifti_with_path[m].split("\\")[-1].split(".")[0]
                                case = case.replace("_CT", "")
                                if case == "_".join(patient_subsub_with_path[k].split("\\")[-3:-1]):
                                    applyReorientCT(patient_subsub_with_path[k] + "\\DICOMOBJ", case, nifti_folder, reoriented_folder)
                        except IndexError as e:
                            warnings.warn(str(e))
                else:
                    continue

    return reoriented_folder


def applyReorientCT(patient_subfolder_path, case, nifti_folder, reoriented_folder):
    DCMfiles_path = patient_subfolder_path
    DCM_reader = sitk.ImageSeriesReader()
    dicom_names = DCM_reader.GetGDCMSeriesFileNames(DCMfiles_path)
    DCM_reader.SetFileNames(dicom_names)
    dicom_image = DCM_reader.Execute()
    name = case + "_RO.nii.gz"

    try:
        nifti_image = sitk.ReadImage(os.path.join(nifti_folder, case + "_CT"))

        elastix = sitk.ElastixImageFilter()
        elastix.SetFixedImage(dicom_image)
        elastix.SetMovingImage(nifti_image)
        elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
        elastix.LogToConsoleOff()
        elastix.Execute()
        realigned_nifti = elastix.GetResultImage()

        sitk.WriteImage(realigned_nifti, os.path.join(reoriented_folder, name))
    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


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
        nobed = nobed.split(".")[0]
        remove_bed_i = [remove_bed, list_CTs_with_paths[i], os.path.join(nobed_folder, nobed + "_noBed.nii.gz")]
        remove_bed_execs.append(remove_bed_i)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in remove_bed_execs]
        for f in results:
            f.result()



def DirCheck(first, second):
    count = 0
    firstfiles = os.listdir(first)
    firstfiles = [string.rstrip('_CT.nii.gz') for string in firstfiles]
    secondfiles = os.listdir(second)
    for file in secondfiles:
        file = "_".join(file.split("_")[0:2])
        #if 'CT' in file:
        if file not in firstfiles:
            print(file)
            count += 1
    print(count)


def check_spacing(nifti_folder):
    image_files = [f for f in os.listdir(nifti_folder) if f.endswith('.nii.gz')]
    count = 0
    for image_file in image_files:
        image = sitk.ReadImage(os.path.join(nifti_folder, image_file))
        spacing = image.GetSpacing()

        if any(s > 3 for s in spacing):
            print(f"Image {image_file} has a spacing greater than 3.")
            os.remove(os.path.join(nifti_folder, image_file))
            count += 1

    print(f"A total of {count} images were removed due to large image spacing, i.e. low quality.")
    return 0


if __name__ == '__main__':
    data_dir = "E:\\Data\\IFA\\IFA\\NoBedCTs"
    #reoriented_folder = "E:\\Data\\Skull\\NormalCases_All\\Reoriented"

    #reoriented_folder = Reorient(data_dir)
    #BedRemoval(data_dir, reoriented_folder)

    #DirCheck("D:\\Data\\IFA\\IFA\\asNifti", "D:\\Data\\IFA\\IFA\\IFADicoms")

    check_spacing(data_dir)
    print("Done!")
    print("Now you should obtain the segmentations with CTimage...")