# PPutils
Preprocessing Utilities and Scripts for CT and MR 

The full pipeline is as follows:
1) Using ClearCanvas (Synapase) pull T1 and CT (thins only) DICOM files. Put these files in the same folder, denoted by the corresponding patient ID.
2) Run 01_PPall.py
  a) This script ensures directories are not empty and removes them if they are. 
  b) Then the script runs a DCM2Niix executable, which converts DICOMS to nifti format simultaneously anonymizing and gantry tilt correcting them (CT only)
    i) DCM2niix is found here: https://github.com/rordenlab/dcm2niix
  c) Files are then renamed with a proper extension. Files that are "duplicated" due to DCM2niix default of saving both tilt corrected and tilt uncorrected images are removed.
3) Run 02_CTpipeline.py
  a) This script first applies a bed removal algorithm, which ensures the bed regions that appear in the CT are set to background (-1024 HU).
    i) BedRemoveFilter is found here: https://github.com/Barnonewdm/BedRemoveFilter
    ii) The bed removal script will result in a reorientation of the image because it is built on a previous version of ITK
  b) The 'Reorient' function will utilize Elastix to rigidly reorient (6 DOF) the cleaned image to the original DICOM image
4) Run 02_MRIpipeline.py
  a) This script has number of embedded functions to achieve bias field correction, reorientation to a template, skull stripping, and isotropic resampling.
  b) For the current implimentation, bias field correction and isotropic resampling is used and accomplished with an ANTS executable and SimpleITK, respectively.
    i) ANTS N4BiasFieldCorrection can be built from source: https://github.com/ANTsX/ANTs
    ii) This provides the added benefit of not requiring a swap between Linux subsystem for windows. I.e. all scripts can be run on Windows.
    iii) Isotropic resampling is done at this stage prior to CT --> MR registration (step 4), so that images do NOT need to be resampled for other tasks (e.g. neural network training).
  c) The MRIs are further checked (check_spacing) to ensure none of them have a spacing of greater than 3mm in any direction.
    i) Cases that exceed this spacing are removed from the overall dataset.
5) Run 03_CTtoMR.py
  a) This script has many options for Elastix Registration. Currently, the only registration performed is 'CTtoT1', which is a 9 DOF transform.
    i) The Parameters_Rigid.txt file is used to define registration parameters.
    ii) Parameters include: 2048 spatial samples, 32 histogram bins, AdvancedMattesMutualInformation, E InitialBSplineInterpolation = 1, FinalBSplineInterpolation = 3, a multiresolution of 4, no mask is used
  b) Although the CT is registered to the MR quite well, applying the same transform to the segmentation of the CT seems to have some issues
    i) The CTsegmenation is then rigidly registered onto the CTtoT1 volume that is skull mask thresholded using segToCTskullMask
    ii) some label cleanup is also in the works
6) The preprocessing is now complete. 04_MRandCTAlignToOne.py should ONLY be used if MRIs were registered to a template during step 4.

