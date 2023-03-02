import os
import subprocess
import SimpleITK as sitk
import warnings
from concurrent.futures import ThreadPoolExecutor

#step 4, attempt to address CTimage related issue, wherein orientation drastically impacts segmentation guess

import os
import SimpleITK as sitk
import warnings

def ReorientToITKsingle(data_dir):
    CT_reoriented_folder = os.path.join(data_dir, "Ready", "ReorientedCT")
    MR_reoriented_folder = os.path.join(data_dir, "Ready", "ReorientedMR")

    for folder in [CT_reoriented_folder, MR_reoriented_folder]:
        isExist = os.path.exists(folder)
        if not isExist:
            os.makedirs(folder)

    CT_reference_for_alignment = os.path.join(data_dir, "Normal", "186", "1.2.840.113619.2.359.3.1862931524.642.1445577095.307")
    DCM_reader = sitk.ImageSeriesReader()
    dicom_names = DCM_reader.GetGDCMSeriesFileNames(CT_reference_for_alignment)
    DCM_reader.SetFileNames(dicom_names)
    dicom_image = DCM_reader.Execute()

    CT_folder = os.path.join(data_dir, "noBedCTs_T1regs_9DOF")
    MR_folder = os.path.join(data_dir, "B4CorrectedMRI_OG")

    CTtoRef_Files = [f for f in os.listdir(CT_folder) if f.endswith(".nii.gz")]
    MRtoRef_Files = [f for f in os.listdir(MR_folder) if f.endswith(".nii.gz")]

    for ct_filename in CTtoRef_Files:
        filename = ct_filename.split("_")[0]
        matching_mr_filenames = [f for f in MRtoRef_Files if f.split("_")[0] == filename]
        if matching_mr_filenames:
            try:
                ct_moving = sitk.ReadImage(os.path.join(CT_folder, ct_filename))
                mr_moving = sitk.ReadImage(os.path.join(MR_folder, matching_mr_filenames[0]))

                ct_out = filename + "_CT_RO.nii.gz"
                mr_out = filename + "_MR_RO.nii.gz"

                ct_moving.SetOrigin(dicom_image.GetOrigin())
                mr_moving.SetOrigin(dicom_image.GetOrigin())
                ct_moving.SetDirection(dicom_image.GetDirection())
                mr_moving.SetDirection(dicom_image.GetDirection())

                elastix = sitk.ElastixImageFilter()
                elastix.SetFixedImage(dicom_image)
                elastix.SetMovingImage(ct_moving)
                elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
                elastix.LogToConsoleOff()
                elastix.Execute()
                realigned_ct = elastix.GetResultImage()

                elastix = sitk.ElastixImageFilter()
                elastix.SetFixedImage(dicom_image)
                elastix.SetMovingImage(mr_moving)
                elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
                elastix.LogToConsoleOff()
                elastix.Execute()
                realigned_mr = elastix.GetResultImage()

                sitk.WriteImage(realigned_ct, os.path.join(CT_reoriented_folder, ct_out))
                sitk.WriteImage(realigned_mr, os.path.join(MR_reoriented_folder, mr_out))

            except RuntimeError as e:
                warnings.warn(str(e))

    return CT_reoriented_folder, MR_reoriented_folder


def ReorientToITK(data_dir):
    CT_reoriented_folder = os.path.join(data_dir, "Ready", "ReorientedCT")
    MR_reoriented_folder = os.path.join(data_dir, "Ready", "ReorientedMR")

    for folder in [CT_reoriented_folder, MR_reoriented_folder]:
        isExist = os.path.exists(folder)
        if not isExist:
            os.makedirs(folder)

    CT_folder = os.path.join(data_dir, "noBedCTs_T1regs_9DOF")
    MR_folder = os.path.join(data_dir, "B4CorrectedMRI_OG")

    CTtoRef_Files = [f for f in os.listdir(CT_folder) if f.endswith(".nii.gz")]
    MRtoRef_Files = [f for f in os.listdir(MR_folder) if f.endswith(".nii.gz")]

    for ct_filename in CTtoRef_Files:
        filename = ct_filename.split("_")[0]
        matching_mr_filenames = [f for f in MRtoRef_Files if f.split("_")[0] == filename]
        if matching_mr_filenames:
            try:
                list_subfolders_with_paths = [f.path for f in os.scandir(data_dir+"\\Normal") if f.is_dir()]
                matching_dicom = [f for f in list_subfolders_with_paths if f.split("\\")[-1] == filename]
                if matching_dicom:
                    files = [file for file in os.listdir(matching_dicom[0])]
                    for i in range(len(files)):
                        file_list = [file for file in os.listdir(os.path.join(matching_dicom[0], files[i]))]
                        single_file = file_list[2]

                        single_file_reader = sitk.ImageFileReader()
                        single_file_reader.SetFileName(os.path.join(matching_dicom[0], files[i], single_file))
                        single_dcm = single_file_reader.Execute()
                        modality = single_dcm.GetMetaData('0008|0060')

                        if modality == "CT":
                            DCMfiles_path = os.path.join(matching_dicom[0], files[i])
                            DCM_reader = sitk.ImageSeriesReader()
                            dicom_names = DCM_reader.GetGDCMSeriesFileNames(DCMfiles_path)
                            DCM_reader.SetFileNames(dicom_names)
                            dicom_image = DCM_reader.Execute()
                            applyReorient(dicom_image, ct_filename, matching_mr_filenames[0], CT_folder, MR_folder, CT_reoriented_folder, MR_reoriented_folder)
                        else:
                            pass
            except RuntimeError as e:
                warnings.warn(str(e))

    return 0


def applyReorient(dicom, ctfile, mrfile, CTfolder, MRfolder, CT_RO_folder, MR_RO_folder):
    try:
        CT_image = sitk.ReadImage(os.path.join(CTfolder, ctfile))
        MR_image = sitk.ReadImage(os.path.join(MRfolder, mrfile))


        elastix = sitk.ElastixImageFilter()
        elastix.SetFixedImage(dicom)
        elastix.SetMovingImage(CT_image)
        elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
        elastix.LogToConsoleOff()
        elastix.Execute()
        realigned_CT = elastix.GetResultImage()

        sitk.WriteImage(realigned_CT, os.path.join(CT_RO_folder, ctfile.split("_")[0] + "_CT_RO.nii.gz"))

        elastix = sitk.ElastixImageFilter()
        elastix.SetFixedImage(dicom)
        elastix.SetMovingImage(MR_image)
        elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
        elastix.LogToConsoleOff()
        elastix.Execute()
        realigned_MR = elastix.GetResultImage()

        sitk.WriteImage(realigned_MR, os.path.join(MR_RO_folder, mrfile.split("_")[0] + "_MR_RO.nii.gz"))

    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


if __name__ == '__main__':
    #note, no longer used
    data_dir = "D:\\Data\\CNH_Paired"
    reoriented_folder = ReorientToITK(data_dir)

    print("Done!")
    print("Now you should obtain the segmentations with CTimage...")