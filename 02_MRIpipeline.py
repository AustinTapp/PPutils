import os
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

Use FSL FLIRT (fsl5.0-flirt -dof 6 -cost mutualinfo -omat $sub"mat" -in $sub".resamp.n4.nii.gz" -ref Template/Age_matched_Template -out $sub".flirt3";)
https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.fsl.preprocess.html#flirt

6) Apply the transform output of step 5 to the corrected data (output of 3/input of 4)
Done with sitk or ITK

'''

def Resample(nifti_folder):
    resampled_folder = os.path.join(data_dir, "Resampled")
    isExist = os.path.exists(resampled_folder)
    if not isExist:
        os.makedirs(resampled_folder)

    spacing = [1.0, 1.0, 1.0]
    resampled = sitk.ResampleImageFilter()
    resampled.SetInterpolator(sitk.sitkGaussian)
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
            resampled = resampled.Execute(image)
            sitk.WriteImage(resampled, os.path.join(resampled_folder, filename, "_resampled.nii.gz"))

    return resampled_folder


def BiasCorrect(reoriented_dir):
    B4corrected_folder = os.path.join(data_dir, "B4CorrectedMRI")
    isExist = os.path.exists(B4corrected_folder)
    if not isExist:
        os.makedirs(B4corrected_folder)

    n4 = N4BiasFieldCorrection
    n4.save_bias = False
    n4_cmdline_execs_list = []

    for filename in os.listdir(reoriented_dir):
        n4.inputs.input_image = os.path.join(reoriented_dir, filename)
        n4.inputs.output_image = os.path.join(B4corrected_folder, filename.split('.')[0], + 'nii.gz')
        n4_cmdline_execs_list.append(n4.cmdline)

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = [executor.submit(subprocess.call, exec) for exec in n4_cmdline_execs_list]
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
            bse.inputs.outputCortexFile = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_Cortex.nii.gz")
            bse.inputs.outputDetailedBrainMask = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_BrainMask.nii.gz")
            bse.inputs.outputDiffusionFilter = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_DiffusionFilter.nii.gz")
            bse.inputs.outputEdgeMap = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_EdgeMap.nii.gz")
            bse.inputs.outputMRIVolume = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_MRIVolume.nii.gz")
            bse.inputs.outputMaskFile = os.path.join(skull_stripped_dir, filename.split('.')[0], + "_MaskFile.nii.gz")

            bse_cmdline_execs_list.append(bse.cmdline)

            with ThreadPoolExecutor(max_workers=5) as executor:
                results = [executor.submit(subprocess.call, exec) for exec in bse_cmdline_execs_list]
                for f in results:
                    f.result()
    return skull_stripped_dir'''


def Transform(bias_corrected, reference_dir):
    registered_dir = os.path.join(data_dir, "toTemplateMRIs")
    isExist = os.path.exists(registered_dir)
    if not isExist:
        os.makedirs(registered_dir)

    FLT_cmdline_execs_list = []

    for filename in os.listdir(bias_corrected):
        FLT = fsl.FLIRT(bins=64, cost_func='mututalinfo', dof=6, interp='nearestneighbour', output_type='NIFTI_GZ',
                        save_log=False, out_matrix_file=os.path.join(registered_dir + filename.split('.')[0]+'.mat'))
        FLT.inputs.in_file = os.path.join(bias_corrected, filename)

        if filename.split("_")[-1] == "_T1.nii.gz":
            FLT.inputs.reference = os.path.join(reference_dir, "nihpd_asym_00-02_t1w.nii.gz")
        if filename.split("_")[-1] == "_T2.nii.gz":
            FLT.inputs.reference = os.path.join(reference_dir, "nihpd_asym_00-02_t2w.nii.gz")

        FLT_cmdline_execs_list.append(FLT.cmdline)

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = [executor.submit(subprocess.call, exec) for exec in FLT_cmdline_execs_list]
            for f in results:
                f.result()

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
    resample_dir = Resample(asNifti_dir)
    bias_dir = BiasCorrect(resample_dir)
    #skull_strip_dir = SkullStrip(bias_dir)
    registered_dir = Transform(bias_dir, reference_dir="ReferenceMRIs\\0_2yo")
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")