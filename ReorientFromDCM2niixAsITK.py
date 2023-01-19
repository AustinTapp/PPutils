import numpy as np
import SimpleITK as sitk

if __name__ == '__main__':
    DCMfiles_path = "D:\\Data\\CNH_Paired\\Normal\\PID17\\CT\\DICOMOBJ"
    DCM_reader = sitk.ImageSeriesReader()
    dicom_names = DCM_reader.GetGDCMSeriesFileNames(DCMfiles_path)
    DCM_reader.SetFileNames(dicom_names)
    dicom_image = DCM_reader.Execute()

    nifti_image = sitk.ReadImage("D:\\Data\\CNH_Paired\\asNifti\\test_ignore\\CT_BRAIN_AXIAL_4M-2Y_Head_20140303182432_4_Tilt_1.nii.gz")

    elastix = sitk.ElastixImageFilter()
    elastix.SetFixedImage(dicom_image)
    elastix.SetMovingImage(nifti_image)
    elastix.SetParameterMap(sitk.GetDefaultParameterMap("rigid"))
    elastix.Execute()

    realigned_nifti = elastix.GetResultImage()

    sitk.WriteImage(realigned_nifti, 'D:\\Data\\CNH_Paired\\asNifti\\test_ignore\\reoriented.nii.gz')

    print("Done!")