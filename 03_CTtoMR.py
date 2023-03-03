import os
import SimpleITK as sitk
import warnings
import numpy as np

#C:\Users\Austin Tapp\AppData\Local\Slicer 5.0.2\NA-MIC\Extensions-30822\SlicerElastix\lib\Slicer-5.0\qt-scripted-modules\Resources\RegistrationParameters

def InitialRigid(ct_file, t1_file):
    initial_registered_ct_image = None
    mri = sitk.ReadImage(t1_file)
    ct = sitk.ReadImage(ct_file)

    size = mri.GetSize()
    origin = mri.GetOrigin()
    spacing = mri.GetSpacing()
    center = [origin[i] + (size[i] - 1) * spacing[i] / 2.0 for i in range(3)]
    center = ' '.join([str(c) for c in center])

    try:
        RigidElastix = sitk.ElastixImageFilter()
        RigidElastix.SetFixedImage(mri)
        RigidElastix.SetMovingImage(ct)
        rigid_map = RigidElastix.ReadParameterFile("Rigid.txt")
        rigid_map['CenterOfRotation'] = [center]
        rigid_map['ResultImageFormat'] = ['nii']
        RigidElastix.LogToConsoleOff()

        RigidElastix.Execute()
        initial_registered_ct_image = RigidElastix.GetResultImage()

    except RuntimeError as e:
        warnings.warn(str(e))

    return initial_registered_ct_image


def CTtoMRregistration(ct_file, t1_file, seg_file, output_file, register_dir):
    try:
        #aligned_ct = InitialRigid(ct_file, t1_file)

        mri = sitk.ReadImage(t1_file)
        RigidElastix = sitk.ElastixImageFilter()

        RigidElastix.SetFixedImage(mri)
        RigidElastix.SetMovingImage(sitk.ReadImage(ct_file))
        RigidElastix.LogToConsoleOff()
        rigid_map = RigidElastix.ReadParameterFile("Parameters_Rigid.txt")

        size = mri.GetSize()
        origin = mri.GetOrigin()
        spacing = mri.GetSpacing()
        center = [origin[i] + (size[i] - 1) * spacing[i] / 2.0 for i in range(3)]
        center = ' '.join([str(c) for c in center])

        rigid_map['CenterOfRotation'] = [center]
        rigid_map['ResultImageFormat'] = ['nii']
        RigidElastix.SetParameterMap(rigid_map)
        RigidElastix.Execute()

        CT_to_T1_image_transform = RigidElastix.GetTransformParameterMap()[0]
        CT_to_T1_image = RigidElastix.GetResultImage()

        #CT values are 0 where not aligned, address with intensity shift
        CT_to_T1_array = sitk.GetArrayFromImage(CT_to_T1_image)
        CT_to_T1_array[CT_to_T1_array == 0] = -1024
        CT_to_T1_array = sitk.GetImageFromArray(CT_to_T1_array)

        CT_to_T1_array.SetOrigin(CT_to_T1_image.GetOrigin())
        CT_to_T1_array.SetDirection(CT_to_T1_image.GetDirection())

        rigid_map['FinalBSplineInterpolationOrder'] = ['0']
        RigidElastix.SetParameterMap(rigid_map)
        RigidElastix.SetMovingImage(sitk.ReadImage(seg_file))
        RigidElastix.Execute()

        CTseg_resampled = RigidElastix.GetResultImage()
        CTseg_resampled = sitk.Cast(CTseg_resampled, sitk.sitkInt16)


        sitk.WriteImage(CT_to_T1_array, os.path.join(register_dir, output_file + "_noBed_T1registered.nii.gz"))
        sitk.WriteParameterFile(CT_to_T1_image_transform, os.path.join(register_dir, output_file + "transform.txt"))
        sitk.WriteImage(CTseg_resampled, os.path.join(register_dir, output_file + "_seg_T1registered.nii.gz"))
        sitk.WriteImage(CTseg_resampled, os.path.join(register_dir, output_file + "_seg_T1registered.nii.gz"))

    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


def CTtoMR_Def_registration(ct_file, t1_file, output_file, register_dir):
    try:
        aligned_ct = InitialRigid(ct_file, t1_file)

        DeformableElastix = sitk.ElastixImageFilter()

        DeformableElastix.SetFixedImage(sitk.ReadImage(t1_file))
        DeformableElastix.SetMovingImage(aligned_ct)
        def_map = DeformableElastix.ReadParameterFile("Deformable.txt")
        def_map['ResultImageFormat'] = ['nii']
        DeformableElastix.LogToConsoleOn()

        DeformableElastix.Execute()
        CT_to_T1_image = DeformableElastix.GetResultImage()

        sitk.WriteImage(CT_to_T1_image, os.path.join(register_dir, output_file))

    except RuntimeError as e:
        warnings.warn(str(e))


def CTtoT1(CTs, MRs, Segs, data_dir):
    registered_toMRI = os.path.join(data_dir, "noBedCTs_T1regs_9DOF")
    isExist = os.path.exists(registered_toMRI)
    if not isExist:
        os.makedirs(registered_toMRI)
    ct_filenames = [f for f in os.listdir(CTs)]
    seg_filenames = [f for f in os.listdir(Segs)]
    seg_filename_dict = {f.split("_")[0]: f for f in seg_filenames}

    t1_filenames = [f for f in os.listdir(MRs) if "T1" in f and f.endswith(".nii.gz")]
    t1_filename_dict = {f.split("_")[0]: f for f in t1_filenames}

    for ct_filename in ct_filenames:
        filename = ct_filename.split("_")[0]
        seg_filename = seg_filename_dict.get(filename)
        t1_filename = t1_filename_dict.get(filename)
        if t1_filename:
            ct_file = os.path.join(CTs, ct_filename)
            t1_file = os.path.join(MRs, t1_filename)
            seg_file = os.path.join(Segs, seg_filename)
            output_file = filename
            CTtoMRregistration(ct_file, t1_file, seg_file, output_file, registered_toMRI)

    return registered_toMRI


def CTsegToCTT1(CTtoT1, nbCTs):
    reoriented_folder = os.path.join(data_dir, "nbCTsegs_T1regsRO")
    isExist = os.path.exists(reoriented_folder)
    if not isExist:
        os.makedirs(reoriented_folder)
    CTtoT1_Files = [f for f in os.listdir(CTtoT1) if f.endswith(".nii.gz")]
    CTseg_Files = [f for f in os.listdir(nbCTs) if f.endswith(".nii.gz")]
    CT_filename_dict = {f.split("_")[0]: f for f in CTseg_Files}

    for ct_filename in CTtoT1_Files:
        filename = ct_filename.split("_")[0]
        nbCT_filename = CT_filename_dict.get(filename)
        if nbCT_filename:
            try:
                ctToT1_file = sitk.ReadImage(os.path.join(CTtoT1, ct_filename))
                CTseg_file = sitk.ReadImage(os.path.join(nbCTs, nbCT_filename))
                output_file = filename + "_nbCTseg_T1reg.nii.gz"

                transform = sitk.Euler3DTransform()
                transformed_image = sitk.Resample(CTseg_file, ctToT1_file, transform, sitk.sitkLinear, 0.0)
                transformed_image.SetOrigin(ctToT1_file.GetOrigin())
                transformed_image.SetSpacing(ctToT1_file.GetSpacing())
                transformed_image.SetDirection(ctToT1_file.GetDirection())

                sitk.WriteImage(transformed_image, os.path.join(reoriented_folder, output_file))
            except RuntimeError as e:
                warnings.warn(str(e))

    return reoriented_folder


def labelcleanup(seg_dir):
    clean_folder = os.path.join(data_dir, "nbCTseg_Reg_clean")
    isExist = os.path.exists(clean_folder)
    if not isExist:
        os.makedirs(clean_folder)

    SegRegFiles = [f for f in os.listdir(seg_dir)]
    for segmentation in SegRegFiles:
        seg_img = sitk.ReadImage(os.path.join(seg_dir, segmentation))
        unique_labels = sitk.GetArrayFromImage(seg_img)
        unique_labels = np.unique(unique_labels)
        unique_labels = unique_labels[1:]
        filled_img = sitk.Image(seg_img.GetSize(), sitk.sitkUInt16)

        for label in unique_labels:
            binary_mask = (sitk.GetArrayFromImage(seg_img) == label).astype(int)
            binary_mask = sitk.GetArrayFromImage(binary_mask)

            filled_mask = sitk.VotingBinaryHoleFilling(binary_mask, [2]*3)
            filled_label_img = sitk.GetImageFromArray(filled_mask)
            filled_label_img.CopyInformation(seg_img)
            masked_img = sitk.Mask(seg_img, filled_label_img)
            filled_img += masked_img

        sitk.WriteImage(filled_img, clean_folder)

    return 0


def to_binary(seg_dir):
    clean_folder = os.path.join(data_dir, "nbCTseg_Reg_clean")
    isExist = os.path.exists(clean_folder)
    if not isExist:
        os.makedirs(clean_folder)

    SegRegFiles = [f for f in os.listdir(seg_dir)]
    for segmentation in SegRegFiles:
        seg_img = sitk.ReadImage(os.path.join(seg_dir, segmentation))
        filled_img = sitk.BinaryThreshold(seg_img, 1, 7, 1, 0)
        sitk.WriteImage(filled_img, os.path.join(clean_folder, segmentation.split("_")[0] + "_binary.nii.gz"))

    return 0

if __name__ == '__main__':

    data_dir = "D:\\Data\\CNH_Paired"
    NoBedCTs_dir = os.path.join(data_dir, "NoBedCTs")
    Seg_dir = os.path.join(data_dir, "nbCTsegs")
    MRIs = os.path.join(data_dir, "B4CorrectedMR")
    #label_dir = os.path.join(data_dir, "nbCTsegs_T1Reg_RO")

    #MRItotemplate_dir = os.path.join(data_dir, "toTemplateMRIs")

    #to the template registered MRI
    toMRI = CTtoT1(NoBedCTs_dir, MRIs, Seg_dir, data_dir)

    #ctRO = CTtoOriginReset(CTtoT1s, NoBedCTs_dir)
    #CTsegToCTT1(CTtoT1s, label_dir)

    #labelcleanup(label_dir)
    #to_binary(label_dir)
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")
