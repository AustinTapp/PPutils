import os
import SimpleITK as sitk
import warnings

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
        RigidElastix.LogToConsoleOn()

        RigidElastix.Execute()
        initial_registered_ct_image = RigidElastix.GetResultImage()

    except RuntimeError as e:
        warnings.warn(str(e))

    return initial_registered_ct_image


def CTtoMRregistration(ct_file, t1_file, output_file, register_dir):
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


def CTtoT1(CTs, MRs, data_dir):
    registered_toMRI = os.path.join(data_dir, "CTtoT1")
    isExist = os.path.exists(registered_toMRI)
    if not isExist:
        os.makedirs(registered_toMRI)
    ct_filenames = [f for f in os.listdir(CTs)]
    t1_filenames = [f for f in os.listdir(MRs) if "T1" in f and f.endswith("_FLT.nii.gz")]
    t1_filename_dict = {f.split("_")[0]: f for f in t1_filenames}

    for ct_filename in ct_filenames:
        filename = ct_filename.split("_")[0]
        t1_filename = t1_filename_dict.get(filename)
        if t1_filename:
            ct_file = os.path.join(CTs, ct_filename)
            t1_file = os.path.join(MRs, t1_filename)
            output_file = filename + "_noBed_T1registered.nii.gz"
            CTtoMRregistration(ct_file, t1_file, output_file, registered_toMRI)

    return registered_toMRI

if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Pair_Test"
    NoBedCTs_dir = os.path.join(data_dir, "NoBedCTs")
    MRItotemplate_dir = os.path.join(data_dir, "toTemplateMRIs")

    #to the template registered MRI
    toMRI_dir = CTtoT1(NoBedCTs_dir, MRItotemplate_dir, data_dir)

    #even though we are using literally the exact same transform the slicer one works better for some reason
    #there are a number of 'defaults' in Slicer that are improving performance. Adjustments would take much too long
    #DirCheck(original_dir, asNifti_dir)
    print("Done!")
