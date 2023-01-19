import os
import shutil
import SimpleITK as sitk

if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Paired"
    list_subfolders_with_paths = [f.path for f in os.scandir(data_dir) if f.is_dir()]
    for i in range(len(list_subfolders_with_paths)):
        nifti_folder = os.path.join(data_dir, "asNifti")
        #print(nifti_folder)
        isExist = os.path.exists(nifti_folder)
        if not isExist:
            os.makedirs(nifti_folder)
        patient_subfolder_with_path = [f.path for f in os.scandir(list_subfolders_with_paths[i]) if f.is_dir()]

        for j in range(len(patient_subfolder_with_path)):
            #print(patient_subfolder_with_path[j].split('\\')[-1])
            patient_scanfiles_with_path = [f.path for f in os.scandir(patient_subfolder_with_path[j]) if f.is_dir()]

            # for k in range(len(patient_scanfiles_with_path)):
                # print(patient_subfolder_with_path[j].split('\\')[-1])
                # patient_imagefiles_with_path = [f.path for f in os.scandir(patient_scanfiles_with_path[k]) if f.is_dir()]

            for l in range(len(patient_scanfiles_with_path)):
                #print(patient_imagefiles_with_path[k])
                if len(patient_scanfiles_with_path[l]) == 0:
                    continue
                elif patient_scanfiles_with_path[l].split('\\')[-1] == "CT":
                    DCMfiles_path = [f.path for f in os.scandir(patient_scanfiles_with_path[l]) if f.is_dir()]
                    for k in range(len(DCMfiles_path)):
                        reader = sitk.ImageSeriesReader()
                        dicom_names = reader.GetGDCMSeriesFileNames(DCMfiles_path[k])
                        reader.SetFileNames(dicom_names)
                        dicom_image = reader.Execute()
                        nifti_image_name = os.path.join(data_dir, "asNifti",
                                                        patient_subfolder_with_path[j].split('\\')[-1] + "_" +
                                                        patient_scanfiles_with_path[l].split('\\')[-1] + ".nii.gz")

                        sitk.WriteImage(dicom_image, nifti_image_name)
                        print(f"Writing {nifti_image_name} to file was successful...\n")
                else:
                    MRI_files_path = [f.path for f in os.scandir(patient_scanfiles_with_path[l]) if f.is_dir()]
                    for m in range(len(MRI_files_path)):
                        if len(MRI_files_path) < 2:
                            reader = sitk.ImageSeriesReader()
                            dicom_names = reader.GetGDCMSeriesFileNames(MRI_files_path[m])
                            reader.SetFileNames(dicom_names)
                            dicom_image = reader.Execute()
                            nifti_image_name = os.path.join(data_dir, "asNifti",
                                                            patient_subfolder_with_path[j].split('\\')[-1] + "_" +
                                                            patient_scanfiles_with_path[l].split('\\')[-1] + "_T1.nii.gz")

                            sitk.WriteImage(dicom_image, nifti_image_name)
                            print(f"Writing {nifti_image_name} to file was successful...\n")
                        else:
                            MRI_DCMfiles_path = [f.path for f in os.scandir(MRI_files_path[m]) if f.is_dir()]
                            for n in range(len(MRI_DCMfiles_path)):
                                reader = sitk.ImageSeriesReader()
                                dicom_names = reader.GetGDCMSeriesFileNames(MRI_DCMfiles_path[n])
                                reader.SetFileNames(dicom_names)
                                dicom_image = reader.Execute()
                                nifti_image_name = os.path.join(data_dir, "asNifti",
                                                                patient_subfolder_with_path[j].split('\\')[-1] + "_" +
                                                                patient_scanfiles_with_path[l].split('\\')[-1] + "_" +
                                                                MRI_files_path[m].split('\\')[-1] + ".nii.gz")

                                sitk.WriteImage(dicom_image, nifti_image_name)
                                print(f"Writing {nifti_image_name} to file was successful...\n")
                        # shutil.rmtree(patient_subfolder_with_path[l])

    print("Done!")