import os
import shutil
import subprocess

import SimpleITK as sitk
from concurrent.futures import ThreadPoolExecutor
from nipype.interfaces.ants import N4BiasFieldCorrection
import numpy as np
#step 2 (equivalent to CTpipeline)
#should be run AFTER PPall pipeline
#can probably go before CTpipeline because most is processed on Linux SS

'''
Note there is an FSL preprocessing course at: https://open.win.ox.ac.uk/pages/fslcourse/website/
Also nipype has some useful course documentation as well

https://docs.google.com/document/d/1l88iZftdH8fge33M08L0u-3gPvAZL6hV0LGxfTP613g/edit
1) Nifti conversion - dcm2niix, already done
2) Resample to isotropy - SITK 
_____________________

The below scripts use nipype for all uses:
https://nipype.readthedocs.io/en/1.8.5/index.html
https://nipype.readthedocs.io/en/1.8.5/interfaces.html

Note that these are WRAPPERS. The program must be installed and should be accessible by the command line (i.e. in your path).

3) ANTs N4 BFC - ants.utils.bias_correction (possible to download binaries for windows: https://stnava.github.io/ANTs/)
I have downloaded a recent option from the sourceforge (https://sourceforge.net/projects/advants/)
https://nipype.readthedocs.io/en/1.8.5/api/generated/nipype.interfaces.ants.html#n4biasfieldcorrection
https://antspy.readthedocs.io/en/latest/_modules/ants/utils/bias_correction.html

**Corrected Data** --> input for step 6

4) Skull Stripping - Brainsuite
https://nipype.readthedocs.io/en/1.8.5/api/generated/nipype.interfaces.brainsuite.brainsuite.html#bse
# this does not seem to help aside from alignment, but application of the same matrix to a CT does not work

5) Linear Transform (is template dependent: https://docs.google.com/document/d/1yH9umzKXfmwFrjXzhNZqUqFKMkQzXCMyaoVbdLcl76M/edit)

Use FSL FLIRT (fsl5.0-flirt -dof 6 -cost mutualinfo -omat $sub"mat" -in $sub".resamp.n4.nii.gz" -ref Template/Age_matched_Template -out $sub".flirt3";)
https://nipype.readthedocs.io/en/1.8.5/api/generated/nipype.interfaces.fsl.preprocess.html#flirt
Templates added

6) Apply the transform output of step 5 to the corrected data (output of 3/input of 4)
Done with sitk or ITK

'''

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

    print(f"A total of {count} images were removed due to poor large image slices (spacing)")
    return 0

def Resample(data_dir, nifti_folder):
    resampled_folder = os.path.join(data_dir, "Resampled")
    isExist = os.path.exists(resampled_folder)
    if not isExist:
        os.makedirs(resampled_folder)

    spacing = [1.0, 1.0, 1.0]
    resampled = sitk.ResampleImageFilter()
    resampled.SetInterpolator(sitk.sitkLanczosWindowedSinc)
    resampled.SetOutputSpacing(spacing)

    for filename in os.listdir(nifti_folder):
        if filename.endswith("T1.nii.gz"):
            image = sitk.ReadImage(os.path.join(nifti_folder, filename))

            size = [int(sz * spc) for sz, spc in zip(image.GetSize(), image.GetSpacing())]
            resampled.SetSize(size)
            resampled.SetOutputDirection(image.GetDirection())
            resampled.SetOutputOrigin(image.GetOrigin())
            resampled_image = resampled.Execute(image)
            sitk.WriteImage(resampled_image, os.path.join(resampled_folder, filename.split(".")[0] + "_resampled.nii.gz"))
        else:
            continue

    return resampled_folder


def BiasCorrect(reoriented_dir):
    B4corrected_folder = os.path.join(data_dir, "B4CorrectedMR")
    isExist = os.path.exists(B4corrected_folder)
    if not isExist:
        os.makedirs(B4corrected_folder)

    n4_exe = "C:\\Program Files (x86)\\ANTS\\bin\\N4BiasFieldCorrection.exe"
    n4 = N4BiasFieldCorrection()
    n4.save_bias = False
    n4_cmdline_list = []

    for filename in os.listdir(reoriented_dir):
        n4.inputs.input_image = os.path.join(reoriented_dir, filename)
        n4.inputs.output_image = os.path.join(B4corrected_folder, filename.split('.')[0] + "_B4.nii.gz")
        n4_cmdline_list.append(n4.cmdline)

    n4_cmdline_exec = [i.replace('N4BiasFieldCorrection', n4_exe) for i in n4_cmdline_list]
    n4_cmdline_exec = [i.replace('\\', "/") for i in n4_cmdline_exec]


    with ThreadPoolExecutor(max_workers=5) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in n4_cmdline_exec]
        for f in results:
            f.result()
    return B4corrected_folder


#skull strip was removed because downstream CT to T1 registration suffered
'''def SkullStrip(data_dir, bias_corrected):
    skull_stripped_dir = os.path.join(data_dir, "skullStrippedMRIs")
    isExist = os.path.exists(skull_stripped_dir)
    if not isExist:
        os.makedirs(skull_stripped_dir)

    SS_cme = []
    Brainsuite_Coritcal_extraction = "~/BrainSuite21a/bin/ce_edit.sh"

    t1_filenames = [f for f in os.listdir(bias_corrected) if "T1" in f and f.endswith(".nii.gz")]
    for filename in t1_filenames:
        ss_cmd = Brainsuite_Coritcal_extraction + " " + filename
        shutil.copy(os.path.join(bias_corrected, filename), os.path.join(skull_stripped_dir, filename))
        SS_cme.append(ss_cmd)

    #handle errors with the executable file below, also, save mask, use mask for rigid then deformable elastix (parameters are in the elastix extension folder)
    print("\nIt is necessary to move the script file and all dependent files to your Linux SSL!")
    print(f"You should be able to copy everything from the folder {skull_stripped_dir}")
    print("After, 1) 'cd' to the folder, 2)'dos2unix script.sh', 3)'chmod +x script.sh' and run with 4)'bash script.sh'\n")


    script = os.path.join(skull_stripped_dir, "script.sh")
    with open(script, 'w') as f:
        for command in SS_cme:
            f.write(f'{command} \n')

    return skull_stripped_dir'''


def TransformMRIs(data_dir, bias_dir):
    registered_dir = os.path.join(data_dir, "toTemplateMRIs")
    isExist = os.path.exists(registered_dir)
    if not isExist:
        os.makedirs(registered_dir)

    FLT_cmdline_execs_list = []

    flirt_base = "flirt -in input.nii.gz -ref ref.nii -out output.nii.gz -omat matrix.mat -searchcost mutualinfo -dof 6 -interp sinc"

    for filename in os.listdir(bias_dir):
        if "T2" in filename:
            flirt_cmd = flirt_base
            flirt_cmd = flirt_cmd.replace("ref.nii", "nihpd_asym_00-02_t2w.nii")
            flirt_cmd = flirt_cmd.replace("input.nii.gz", filename)
            flirt_cmd = flirt_cmd.replace("output.nii.gz", filename.split('.')[0] + '_FLT.nii.gz')
            flirt_cmd = flirt_cmd.replace("matrix.mat", filename.split('.')[0] + '_FLTmat.tfm')
            FLT_cmdline_execs_list.append(flirt_cmd)
            shutil.copy(os.path.join(bias_dir, filename), os.path.join(registered_dir, filename))
        if "T1" in filename:
            flirt_cmd = flirt_base
            flirt_cmd = flirt_cmd.replace("ref.nii", "nihpd_asym_00-02_t1w.nii")
            flirt_cmd = flirt_cmd.replace("input.nii.gz", filename)
            flirt_cmd = flirt_cmd.replace("output.nii.gz", filename.split('.')[0] + '_FLT.nii.gz')
            flirt_cmd = flirt_cmd.replace("matrix.mat", filename.split('.')[0] + '_FLTmat.tfm')
            FLT_cmdline_execs_list.append(flirt_cmd)
            shutil.copy(os.path.join(bias_dir, filename), os.path.join(registered_dir, filename))

    shutil.copy("ReferenceMRIs\\0_2yo\\nihpd_asym_00-02_t1w.nii", os.path.join(registered_dir, "nihpd_asym_00-02_t1w.nii"))
    shutil.copy("ReferenceMRIs\\0_2yo\\nihpd_asym_00-02_t2w.nii", os.path.join(registered_dir, "nihpd_asym_00-02_t2w.nii"))

    script = os.path.join(registered_dir, "script.sh")
    with open(script, 'w') as f:
        f.write('echo Running FSL FLIRT....\n')
        for command in FLT_cmdline_execs_list:
            f.write(f'{command} \n')

    print("It is necessary to move the script file and all dependent files to your Linux SSL!")
    print(f"You should be able to copy everything from the folder {registered_dir}")
    print("After, 1) 'cd' to the folder, 2)'dos2unix script.sh', 3)'chmod +x script.sh' and run with 4)'bash script.sh'")
    return registered_dir


def TransformMasks(skull, flirt):

    image_files = [f for f in os.listdir(skull) if f.endswith("mask.nii.gz")]

    for mask in image_files:
        image_base_name = mask.split(".")[0]

        transform_file = image_base_name + "_bse_FLT_mat.tfm"
        transform_path = os.path.join(flirt, transform_file)
        if os.path.exists(transform_path):

            with open(transform_path, 'r') as f:
                transform_text = f.read()
            transform_matrix = np.fromstring(transform_text, sep=' ')
            f.close()

            image_path = os.path.join(skull, mask)
            image = sitk.ReadImage(image_path)

            transform = sitk.Euler3DTransform()
            transform.SetParameters(transform_matrix.tolist())
            fitted = sitk.ReadImage(os.path.join(flirt, image_base_name + "_bse_FLT.nii.gz"))
            transformed_image = sitk.Resample(image, transform, sitk.sitkLinear, 0.0, image.GetPixelID())
            transformed_image.SetOrigin(fitted.GetOrigin())
            transformed_image.SetSpacing(fitted.GetSpacing())
            transformed_image.SetDirection(fitted.GetDirection())

            output_file = image_base_name + "_mask_transformed.nii.gz"
            output_path = os.path.join(flirt, output_file)
            sitk.WriteImage(transformed_image, output_path)


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
    asNifti_dir = "D:\\Data\\CNH_Paired\\asNifti"

    #bias_dir = "D:\\Data\\CNH_Pair_Test\\B4CorrectedMRI"
    #skull_strip_dir = "D:\\Data\\CNH_Pair_Test\\skullStrippedMRIs"
    #flirt_dir = "D:\\Data\\CNH_Pair_Test\\toTemplateMRIs"

    check_spacing(asNifti_dir)
    resample_dir = Resample(data_dir, asNifti_dir)
    BiasCorrect(resample_dir)

    #skull_strip_dir = SkullStrip(data_dir, bias_dir)
    #print("Run the skull stripping on T1 first, then press enter to continue with the alignment process...")
    #input("Press enter to continue!")

    #flirt_dir = TransformMRIs(data_dir, bias_dir)

    #TransformMasks(skull_strip_dir, flirt_dir)
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")