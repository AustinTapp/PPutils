import os
import subprocess
import json
import shutil
import SimpleITK as sitk
from concurrent.futures import ThreadPoolExecutor

'''
Note there is an FSL preprocessing course at: https://open.win.ox.ac.uk/pages/fslcourse/website/
Also nipype has some useful course documentation as well

https://docs.google.com/document/d/1l88iZftdH8fge33M08L0u-3gPvAZL6hV0LGxfTP613g/edit
1) Nifti conversion - dcm2niix, already done
2) Resample to isotropy - SITK, already done
_____________________

The below scripts use nipype for all uses:
https://nipype.readthedocs.io/en/0.12.1/interfaces/

However, these are WRAPPERS. The true program must be install and should be EASY accessible by the command line (i.e. they should be in your path).
I THINK!!

3) ANTs N4 BFC - ants.utils.bias_correction
https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html#n4biasfieldcorrection
https://antspy.readthedocs.io/en/latest/_modules/ants/utils/bias_correction.html

**Corrected Data** --> input for step 6

4) Skull Stripping - Brainsuite
https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.brainsuite.brainsuite.html#bse


5) Linear Transform (is template dependent: https://docs.google.com/document/d/1yH9umzKXfmwFrjXzhNZqUqFKMkQzXCMyaoVbdLcl76M/edit)

For 0 - 4 years: https://nist.mni.mcgill.ca/infant-atlases-0-4-5-years/
    found in: http://www.bic.mni.mcgill.ca/~vfonov/nihpd/obj2/nihpd_obj2_asym_nifti.zip or https://drive.google.com/drive/u/0/folders/1AVJyLkM7V-YBJn6hJXuJITL_8-bKZDln

Note that these files have intensity of 0 - 100, therefore:
    a) when using them, should we ensure the images are also scaled to the same intensity, then save the output transform for step 6?
    b) other notes?

Use FSL FLIRT (fsl5.0-flirt -dof 6 -cost mutualinfo -omat $sub"mat" -in $sub".resamp.n4.nii.gz" -ref Template/Age_matched_Template -out $sub".flirt3";)
https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.fsl.preprocess.html#flirt

6) Apply the transform output of step 5 to the corrected data (output of 3/input of 4)
Done with sitk or ITK

'''
#function imports for MRI processing

#step 3
from nipype.interfaces.ants import N4BiasFieldCorrection

#step 4
from nipype.interfaces import brainsuite
#strip with bse = brainsuite.Bse()

#step 5
from nipype.interfaces import fsl
fsl.FLIRT().run()

#step 6
#itk/sitk



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
                os.rename(os.path.join(nifti_folder, base_name.split('\\')[-1]+".nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                continue
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Eq_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                continue
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_1.nii.gz"), base_name+"_CT.nii.gz")
            except FileNotFoundError:
                continue
            try:
                shutil.move(os.path.join(nifti_folder, base_name.split('\\')[-1]+"_Tilt_Eq_1.nii.gz"), base_name+"_CT.nii.gz")
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
                    except RuntimeError:
                        continue
    return reoriented_folder


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


if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Paired"
    # original_dir = "D:\\Data\\CNH_Paired\\Normal"
    # asNifti_dir = "D:\\Data\\CNH_Paired\\asNifti"
    # reoriented_dir = "D:\\Data\\CNH_Paired\\Reoriented"
    # noBed_dir = "D:\\Data\\CNH_Paired\\NoBedCTs"


    #DirCheck(original_dir, asNifti_dir)
    print("Done!")

    anspy - downloaded as wheel (ubuntu) need N4Bias field correction
    brainsuite skull strip now installed

    transform to template with FSL flirt - flirt install in ubuntu already
        save transform and apply to no stripped skull (may be hard to do... althoguh output matrix can be requested by args)