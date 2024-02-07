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

def toTemplateRegistration(image, template, new_dir):
    try:
        template_image = sitk.ReadImage(template)
        new_image = sitk.ReadImage(image)

        RigidElastix = sitk.ElastixImageFilter()

        RigidElastix.SetFixedImage(template_image)
        RigidElastix.SetMovingImage(new_image)
        RigidElastix.LogToConsoleOff()
        rigid_map = RigidElastix.ReadParameterFile("Parameters_Rigid.txt")

        rigid_map['ResultImageFormat'] = ['nii']
        rigid_map['ResultImagePixelType'] = ['float']
        rigid_map['BSplineInterpolationOrder'] = ['3']
        rigid_map['FinalBSplineInterpolationOrder'] = ['3']
        #change FinalBSpline to 0 when doing segmentations, then change back for image registration

        RigidElastix.SetParameterMap(rigid_map)
        RigidElastix.Execute()
        Final_Image = RigidElastix.GetResultImage()

        Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(image))
        Final_Image_array = sitk.GetArrayFromImage(Final_Image)

        Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
        Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

        Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
        Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())

        name = image.split('\\')[-1]
        name = name.split('_')[0]

        sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, "ss_" + name + "_0000.nii.gz"))

    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


def AlignToTemplate(data_dir, new_dir, template):
    isExist = os.path.exists(new_dir)
    if not isExist:
        os.makedirs(new_dir)
    image_filenames = [f for f in os.listdir(data_dir)]
    for file in image_filenames:
        file_path = os.path.join(data_dir, file)
        toTemplateRegistration(file_path, template, new_dir)
        print(f"converted {file}")
    return 0


if __name__ == '__main__':

    data_dir = "E:\\Data\\CNH_Paired\\CTsForSutureSegmentationRename"
    new_dir = "E:\\Data\\CNH_Paired\\CTsForSutureSegs"
    template = "E:\\Data\\CNH_Paired\\CTtemplate.nii.gz"

    AlignToTemplate(data_dir, new_dir, template)
    print("Done!")
