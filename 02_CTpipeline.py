import os
import subprocess
import SimpleITK as sitk
import warnings
from concurrent.futures import ThreadPoolExecutor

#step 2 (equivalent to MRIpipeline)
#should be run AFTER PPall pipeline

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

            if modality == 'CT':
                applyReorientCT(patient_subfolder_with_path[j], list_subfolders_with_paths[i], nifti_folder, reoriented_folder)
            else:
                continue

    return reoriented_folder


def applyReorientCT(patient_subfolder_path, list_subfolders_path, nifti_folder, reoriented_folder):
    DCMfiles_path = patient_subfolder_path
    DCM_reader = sitk.ImageSeriesReader()
    dicom_names = DCM_reader.GetGDCMSeriesFileNames(DCMfiles_path)
    DCM_reader.SetFileNames(dicom_names)
    dicom_image = DCM_reader.Execute()

    case = list_subfolders_path.split("\\")[-1]
    case = case + "_0_CT.nii.gz"
    match = [nifti for nifti in os.listdir(nifti_folder) if nifti == case]
    if len(match) > 0:
        try:
            nifti_image = sitk.ReadImage(os.path.join(nifti_folder, match[0]))

            elastix = sitk.ElastixImageFilter()
            elastix.SetFixedImage(dicom_image)
            elastix.SetMovingImage(nifti_image)
            elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
            elastix.Execute()
            realigned_nifti = elastix.GetResultImage()

            sitk.WriteImage(realigned_nifti, os.path.join(nifti_folder, reoriented_folder, match[0]))
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
        nobed = nobed.split("_")[0]
        remove_bed_i = [remove_bed, list_CTs_with_paths[i], os.path.join(nobed_folder, nobed + "_noBed.nii.gz")]
        remove_bed_execs.append(remove_bed_i)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in remove_bed_execs]
        for f in results:
            f.result()



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
    data_dir = "D:\\Data\\CNH_Pair_Test"

    # original_dir = "D:\\Data\\CNH_Paired\\Normal"
    # asNifti_dir = "D:\\Data\\CNH_Paired\\asNifti"
    # reoriented_dir = "D:\\Data\\CNH_Paired\\Reoriented"
    # noBed_dir = "D:\\Data\\CNH_Paired\\NoBedCTs"

    reoriented_folder = ReorientToITK(data_dir)
    BedRemoval(data_dir, reoriented_folder)

    #DirCheck(original_dir, asNifti_dir)
    print("Done!")
    print("Now you should obtain the segmentations with CTimage...")