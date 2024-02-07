import os
import SimpleITK as sitk
import warnings
import numpy as np

def rescale_intensity_to_reference(input, reference):
    # Get the intensity range of the reference image
    min_ref, max_ref = reference.min(), reference.max()

    # Rescale the input image to match the intensity range of the reference image
    rescaled_array = (input - input.min()) / (input.max() - input.min())
    rescaled_array = rescaled_array * (max_ref - min_ref) + min_ref

    return rescaled_array

def toTemplateRegistration(images, template, new_dir):
    T1_file = None
    try:
        files = [f for f in os.listdir(images) if f.endswith('nii.gz')]
        for file in files:
            if 'T1' in file and 'Seg' not in file:
                T1_file = os.path.join(images, file)

        template_image = sitk.ReadImage(template)
        new_image = sitk.ReadImage(T1_file)

        RigidElastix = sitk.ElastixImageFilter()

        RigidElastix.SetFixedImage(template_image)
        RigidElastix.SetMovingImage(new_image)
        RigidElastix.LogToConsoleOff()
        rigid_map = RigidElastix.ReadParameterFile("Parameters_Rigid.txt")

        rigid_map['ResultImageFormat'] = ['nii']
        rigid_map['ResultImagePixelType'] = ['float']
        rigid_map['BSplineInterpolationOrder'] = ['3']
        rigid_map['FinalBSplineInterpolationOrder'] = ['0']

        RigidElastix.SetParameterMap(rigid_map)
        RigidElastix.Execute()
        Final_Image = RigidElastix.GetResultImage()

        Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(T1_file))
        Final_Image_array = sitk.GetArrayFromImage(Final_Image)

        Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
        Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

        Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
        Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())

        sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, T1_file.split("\\")[-2] + T1_file.split("-")[-1]))

        #transform the rest
        for file in files:
            file = os.path.join(images, file)

            to_image_transform = RigidElastix.GetTransformParameterMap()
            seg_image = sitk.ReadImage(file)

            transformix = sitk.TransformixImageFilter()
            transformix.SetTransformParameterMap(to_image_transform)
            transformix.SetMovingImage(seg_image)
            transformix.LogToConsoleOff()
            transformix.Execute()

            Final_Image = transformix.GetResultImage()

            Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(file))
            Final_Image_array = sitk.GetArrayFromImage(Final_Image)

            Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
            Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

            Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
            Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())
            if 'Seg' in file.split("\\")[-1]:
                sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, file.split("\\")[-2] + '_seg.nii.gz'))
            else:
                sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, file.split("\\")[-2] + file.split("-")[-1]))

    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


def AlignToTemplate(data_dir, new_dir, template):
    isExist = os.path.exists(new_dir)
    if not isExist:
        os.makedirs(new_dir)
    image_filenames = [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]
    for folder in image_filenames:
        folder_path = os.path.join(data_dir, folder)
        toTemplateRegistration(folder_path, template, new_dir)
        print(f"converted {folder}")
    return 0


if __name__ == '__main__':
    data_dir = "E:\\Data\\Brain\\CNseg\\Test"
    new_dir = "E:\\Data\\Brain\\CNseg\\Test\\CoRegTest"
    template = "C:\\Users\Austin Tapp\\Documents\\ImagePreProcessUtils\\PPutils\\ReferenceMRIs\\ICBM_T1_MRI_template.nii"

    AlignToTemplate(data_dir, new_dir, template)
    print("Done!")
