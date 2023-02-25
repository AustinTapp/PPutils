import os
import subprocess
import SimpleITK as sitk
import warnings
from concurrent.futures import ThreadPoolExecutor

#step 4, attempt to address CTimage related issue, wherein orientation drastically impacts segmentation guess

import os
import SimpleITK as sitk
import warnings

def ReorientToITK(data_dir):
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

    CT_folder = os.path.join(data_dir, "noBedCTs_T1regsPV180")
    MR_folder = os.path.join(data_dir, "t1fitted_PV180")

    CTtoRef_Files = [f for f in os.listdir(CT_folder) if f.endswith(".mhd")]
    MRtoRef_Files = [f for f in os.listdir(MR_folder) if f.endswith(".mhd")]

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

                sitk.WriteImage(ct_moving, os.path.join(CT_reoriented_folder, ct_out))
                sitk.WriteImage(mr_moving, os.path.join(MR_reoriented_folder, mr_out))

            except RuntimeError as e:
                warnings.warn(str(e))

    return CT_reoriented_folder, MR_reoriented_folder



if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Paired"
    reoriented_folder = ReorientToITK(data_dir)

    print("Done!")
    print("Now you should obtain the segmentations with CTimage...")