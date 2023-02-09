import os
import shutil
import subprocess

import SimpleITK as sitk
from concurrent.futures import ThreadPoolExecutor
from nipype.interfaces.ants import N4BiasFieldCorrection
from nipype.interfaces import brainsuite
from nipype.interfaces import fsl

#step 2 (equivalent to CTpipeline)
#should be run AFTER PPall pipeline

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

5) Linear Transform (is template dependent: https://docs.google.com/document/d/1yH9umzKXfmwFrjXzhNZqUqFKMkQzXCMyaoVbdLcl76M/edit)

Use FSL FLIRT (fsl5.0-flirt -dof 6 -cost mutualinfo -omat $sub"mat" -in $sub".resamp.n4.nii.gz" -ref Template/Age_matched_Template -out $sub".flirt3";)
https://nipype.readthedocs.io/en/1.8.5/api/generated/nipype.interfaces.fsl.preprocess.html#flirt
Templates added

6) Apply the transform output of step 5 to the corrected data (output of 3/input of 4)
Done with sitk or ITK

'''

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
        if filename.endswith("CT.nii.gz"):
            continue
        else:
            image = sitk.ReadImage(os.path.join(nifti_folder, filename))

            size = [int(sz * spc) for sz, spc in zip(image.GetSize(), image.GetSpacing())]
            resampled.SetSize(size)
            resampled.SetOutputDirection(image.GetDirection())
            resampled.SetOutputOrigin(image.GetOrigin())
            resampled_image = resampled.Execute(image)
            sitk.WriteImage(resampled_image, os.path.join(resampled_folder, filename.split(".")[0] + "_resampled.nii.gz"))

    return resampled_folder


def BiasCorrect(reoriented_dir):
    B4corrected_folder = os.path.join(data_dir, "B4CorrectedMRI")
    isExist = os.path.exists(B4corrected_folder)
    if not isExist:
        os.makedirs(B4corrected_folder)

    n4_exe = "C:\\Program Files (x86)\\ANTS\\bin\\N4BiasFieldCorrection.exe"
    n4 = N4BiasFieldCorrection()
    n4.save_bias = False
    n4_cmdline_list = []

    for filename in os.listdir(reoriented_dir):
        n4.inputs.input_image = os.path.join(reoriented_dir, filename)
        n4.inputs.output_image = os.path.join(B4corrected_folder, filename.split('.')[0] + "_N4.nii.gz")
        n4_cmdline_list.append(n4.cmdline)

    n4_cmdline_exec = [i.replace('N4BiasFieldCorrection', n4_exe) for i in n4_cmdline_list]
    n4_cmdline_exec = [i.replace('\\', "/") for i in n4_cmdline_exec]


    with ThreadPoolExecutor(max_workers=5) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in n4_cmdline_exec]
        for f in results:
            f.result()
    return B4corrected_folder


'''def SkullStrip(bias_corrected):
    skull_stripped_dir = os.path.join(data_dir, "skullStrippedMRIs")
    isExist = os.path.exists(skull_stripped_dir)
    if not isExist:
        os.makedirs(skull_stripped_dir)

    bse = brainsuite.Bse()
    bse.noRotate = True
    bse_cmdline_execs_list = []

    for filename in os.listdir(bias_corrected):
        if filename.endswith("T1.nii.gz"):
            bse.inputs.inputMRIFile = filename
            bse.inputs.outputCortexFile = os.path.join(skull_stripped_dir, filename.split('.')[0] + "_Cortex.nii.gz")
            bse.inputs.outputDetailedBrainMask = os.path.join(skull_stripped_dir, filename.split('.')[0 + "_BrainMask.nii.gz")
            bse.inputs.outputDiffusionFilter = os.path.join(skull_stripped_dir, filename.split('.')[0] + "_DiffusionFilter.nii.gz")
            bse.inputs.outputEdgeMap = os.path.join(skull_stripped_dir, filename.split('.')[0] + "_EdgeMap.nii.gz")
            bse.inputs.outputMRIVolume = os.path.join(skull_stripped_dir, filename.split('.')[0] + "_MRIVolume.nii.gz")
            bse.inputs.outputMaskFile = os.path.join(skull_stripped_dir, filename.split('.')[0] + "_MaskFile.nii.gz")

            bse_cmdline_execs_list.append(bse.cmdline)

            with ThreadPoolExecutor(max_workers=5) as executor:
                results = [executor.submit(subprocess.call, exec) for exec in bse_cmdline_execs_list]
                for f in results:
                    f.result()
    return skull_stripped_dir'''


def Transform(data_dir, bias_corrected):
    registered_dir = os.path.join(data_dir, "toTemplateMRIs")
    isExist = os.path.exists(registered_dir)
    if not isExist:
        os.makedirs(registered_dir)

    FLT_cmdline_execs_list = []

    flirt_base = "flirt -in input.nii.gz -ref ref.nii -out output.nii.gz -omat matrix.mat -searchcost mutualinfo -dof 6 -interp sinc"

    for filename in os.listdir(bias_corrected):
        if "T1" in filename:
            flirt_cmd = flirt_base
            flirt_cmd = flirt_cmd.replace("ref.nii", "nihpd_asym_00-02_t1w.nii")
            flirt_cmd = flirt_cmd.replace("input.nii.gz", filename)
            flirt_cmd = flirt_cmd.replace("output.nii.gz", filename.split('.')[0] + '_FLT.nii.gz')
            flirt_cmd = flirt_cmd.replace("matrix.mat", filename.split('.')[0] + '_FLT_mat.mat')
            FLT_cmdline_execs_list.append(flirt_cmd)
            shutil.copy(os.path.join(bias_corrected, filename), os.path.join(registered_dir, filename))

        if "T2" in filename:
            flirt_cmd = flirt_base
            flirt_cmd = flirt_cmd.replace("ref.nii", "nihpd_asym_00-02_t2w.nii")
            flirt_cmd = flirt_cmd.replace("input.nii.gz", filename)
            flirt_cmd = flirt_cmd.replace("output.nii.gz", filename.split('.')[0] + '_FLT.nii.gz')
            flirt_cmd = flirt_cmd.replace("matrix.mat", filename.split('.')[0] + '_FLT_mat.mat')
            FLT_cmdline_execs_list.append(flirt_cmd)
            shutil.copy(os.path.join(bias_corrected, filename), os.path.join(registered_dir, filename))

    shutil.copy("ReferenceMRIs\\0_2yo\\nihpd_asym_00-02_t1w.nii", os.path.join(registered_dir, "nihpd_asym_00-02_t1w.nii"))
    shutil.copy("ReferenceMRIs\\0_2yo\\nihpd_asym_00-02_t2w.nii", os.path.join(registered_dir, "nihpd_asym_00-02_t2w.nii"))

    script = os.path.join(registered_dir, "script.sh")
    with open(script, 'w') as f:
        for command in FLT_cmdline_execs_list:
            f.write(f'{command} \n')

    print("It is necessary to move the script file and all dependent files to your Linux SSL!")
    print(f"You should be able to copy everything from the folder {registered_dir}")
    print("After, 1) 'cd' to the folder, 2)'dos2unix script.sh', 3)'chmod +x script.sh' and run with 4)'bash script.sh'")
    return registered_dir


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
    asNifti_dir = "D:\\Data\\CNH_Pair_Test\\asNifti"
    bias_dir = "D:\\Data\\CNH_Pair_Test\\B4CorrectedMRI"

    #resample_dir = Resample(data_dir, asNifti_dir)
    #bias_dir = BiasCorrect(resample_dir)
    #skull_strip_dir = SkullStrip(bias_dir)
    Transform(data_dir, bias_dir)
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")