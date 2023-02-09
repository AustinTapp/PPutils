import os
import SimpleITK as sitk
import warnings

def CTtoMRregistration(ct_file, t1_file, output_file, register_dir):
    ct_image = sitk.ReadImage(ct_file)
    t1_image = sitk.ReadImage(t1_file)

    elastix_image_filter = sitk.ElastixImageFilter()
    elastix_image_filter.SetFixedImage(t1_image)
    elastix_image_filter.SetMovingImage(ct_image)

    # Run the registration
    elastix_image_filter.Execute()

    # Get the registered CT image
    registered_ct_image = elastix_image_filter.GetResultImage()

    # Write the registered CT image to the output file
    sitk.WriteImage(registered_ct_image, os.path.join(register_dir, output_file))

def CTtoT1(data_dir, CTs, MRs):
    registered_toMRI_folder = os.path.join(data_dir, "CTtoT1")
    isExist = os.path.exists(registered_toMRI_folder)
    if not isExist:
        os.makedirs(registered_toMRI_folder)

    ct_filenames = [f for f in os.listdir(CTs)]
    t1_filenames = [f for f in os.listdir(MRs)]
    t1_filename_dict = {f.split("_")[0]: f for f in t1_filenames}

    for ct_filename in ct_filenames:
        filename = ct_filename.split("_")[0]
        t1_filename = t1_filename_dict.get(filename)
        if t1_filename:
            ct_file = os.path.join(CTs, ct_filename)
            t1_file = os.path.join(MRs, t1_filename)
            output_file = filename + "_noBed_MRregistered.nii.gz"
            CTtoMRregistration(ct_file, t1_file, output_file, registered_toMRI_folder)

    return registered_toMRI_folder


def CTtoMRTemplate(data_dir, CTs, MRs):
    registered_toMRI_folder = os.path.join(data_dir, "CTtoT1")
    isExist = os.path.exists(registered_toMRI_folder)
    if not isExist:
        os.makedirs(registered_toMRI_folder)

    ct_filenames = [f for f in os.listdir(CTs)]
    t1_filenames = [f for f in os.listdir(MRs)]
    t1_filename_dict = {f.split("_")[0]: f for f in t1_filenames}

    for ct_filename in ct_filenames:
        filename = ct_filename.split("_")[0]
        t1_filename = t1_filename_dict.get(filename)
        if t1_filename:
            ct_file = os.path.join(CTs, ct_filename)
            t1_file = os.path.join(MRs, t1_filename)
            output_file = filename + "_noBed_MR_TempRegistered.nii.gz"
            CTtoMRTemplateregistration(ct_file, t1_file, output_file, registered_toMRI_folder)

    return registered_toMRI_folder


def CTtoMRTemplateregistration(ct_file, t1_file, output_file, register_dir):
    ct_image = sitk.ReadImage(ct_file)
    t1_image = sitk.ReadImage(t1_file)

    elastix_image_filter = sitk.ElastixImageFilter()
    elastix_image_filter.SetFixedImage(t1_image)
    elastix_image_filter.SetMovingImage(ct_image)

    # Run the registration
    elastix_image_filter.Execute()

    # Get the registered CT image
    registered_ct_image = elastix_image_filter.GetResultImage()

    # Write the registered CT image to the output file
    sitk.WriteImage(registered_ct_image, os.path.join(register_dir, output_file))


if __name__ == '__main__':
    data_dir = "D:\\Data\\CNH_Pair_Test"
    resampled_dir = os.path.join(data_dir, "Resampled")
    NoBedCTs_dir = os.path.join(data_dir, "NoBedCTs")
    MRItotemplate_dir = os.path.join(data_dir, "toTemplateMRIs")

    #to the original MRI
    toMRI_dir = CTtoT1(data_dir, NoBedCTs_dir, resampled_dir)

    #use the tranform of the MRI to the TEMPLATE and apply that to the CT (which is now in MRI space)
    CTtoMRTemplate(toMRI_dir, MRItotemplate_dir)

    #DirCheck(original_dir, asNifti_dir)
    print("Done!")
