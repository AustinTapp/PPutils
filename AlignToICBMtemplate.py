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
        rigid_map['FinalBSplineInterpolationOrder'] = ['0']

        RigidElastix.SetParameterMap(rigid_map)
        RigidElastix.Execute()
        Final_Image = RigidElastix.GetResultImage()

        Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(image))
        Final_Image_array = sitk.GetArrayFromImage(Final_Image)

        Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
        Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

        Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
        Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())

        sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, image.split("\\")[-1]))

        #transform the suture segmentation

        CT_to_T1_image_transform = RigidElastix.GetTransformParameterMap()
        seg = image.split('\\')[-1]
        seg = seg.split('_')[1]
        seg = f"C:\\Users\\pmilab\\Documents\\ImagePreProcessUtils\\labelsTr\\ss_{seg}.nii.gz"
        seg_image = sitk.ReadImage(seg)

        transformix = sitk.TransformixImageFilter()
        transformix.SetTransformParameterMap(CT_to_T1_image_transform)
        transformix.SetMovingImage(seg_image)
        transformix.Execute()

        Final_Image = transformix.GetResultImage()

        Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(seg))
        Final_Image_array = sitk.GetArrayFromImage(Final_Image)

        Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
        Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

        Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
        Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())

        sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, seg.split("\\")[-1]))
        print('d')

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

    data_dir = "E:\\Data\\T1s\\1"
    new_dir = "E:\\Data\\T1s\\CoReg"
    template = "C:\\Users\Austin Tapp\\Documents\\ImagePreProcessUtils\\PPutils\\ReferenceMRIs\\ICBM_T1_MRI_template.nii"

    AlignToTemplate(data_dir, new_dir, template)
    print("Done!")
