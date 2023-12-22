import os
import SimpleITK as sitk
import warnings
import pandas

import pandas as pd

def read_excel_and_create_dict(file_path, key_column, value_column):
    df = pd.read_excel(file_path)
    data_dict = dict(zip(df[key_column], df[value_column]))
    return data_dict


def find_template_match(target_integer, sequence):
    ref_path = "C:\\Users\\Austin Tapp\\Documents\\ImagePreProcessUtils\\PPutils\\ReferenceMRIs"
    folders = [folder for folder in os.listdir(ref_path) if os.path.isdir(os.path.join(ref_path, folder))]
    for folder in folders:
        start_range = folder.split('_')[0]
        end_range = folder.split('_')[-1].split('yo')[0]
        if int(start_range) <= target_integer <= int(end_range):
            for file in os.listdir(os.path.join(ref_path, folder)):
                if f'{sequence.lower()}' in file:
                    return os.path.join(ref_path, folder, file)


def rescale_intensity_to_reference(input, reference):
    # Get the intensity range of the reference image
    min_ref, max_ref = reference.min(), reference.max()

    # Rescale the input image to match the intensity range of the reference image
    rescaled_array = (input - input.min()) / (input.max() - input.min())
    rescaled_array = rescaled_array * (max_ref - min_ref) + min_ref

    return rescaled_array


def toTemplateRegistration(image, template, new_dir, segmentation):
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

        sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, image.split("\\")[-2] + image.split("-")[-1]))

        if segmentation:        #transform the suture segmentation
            to_image_transform = RigidElastix.GetTransformParameterMap()
            seg_image = sitk.ReadImage(segmentation)

            transformix = sitk.TransformixImageFilter()
            transformix.SetTransformParameterMap(to_image_transform)
            transformix.SetMovingImage(seg_image)
            transformix.LogToConsoleOff()
            transformix.Execute()

            Final_Image = transformix.GetResultImage()

            Original_Image_array = sitk.GetArrayFromImage(sitk.ReadImage(segmentation))
            Final_Image_array = sitk.GetArrayFromImage(Final_Image)

            Final_Image_array_Rescaled = rescale_intensity_to_reference(Final_Image_array, Original_Image_array)
            Final_Image_Rescaled = sitk.GetImageFromArray(Final_Image_array_Rescaled)

            Final_Image_Rescaled.SetOrigin(Final_Image.GetOrigin())
            Final_Image_Rescaled.SetDirection(Final_Image.GetDirection())

            sitk.WriteImage(Final_Image_Rescaled, os.path.join(new_dir, image.split("\\")[-2] + "_seg.nii.gz"))

    except RuntimeError as e:
        warnings.warn(str(e))
    return 0


def AlignToTemplate(data_dir, new_dir, template, multiage):
    isExist = os.path.exists(new_dir)
    if not isExist:
        os.makedirs(new_dir)
    image_filenames = [f for f in os.listdir(data_dir)]
    for folder in image_filenames:
        folder_path = os.path.join(data_dir, folder)
        files = [f for f in os.listdir(folder_path) if f.endswith('nii.gz') and not f.startswith('Seg')]
        seg = [f for f in os.listdir(folder_path) if f.startswith('Seg') and f.endswith('nii.gz')]
        for file in files:
            segmentation = os.path.join(data_dir, folder_path, seg[0])
            if multiage == True:
                file_path = os.path.join(data_dir, folder_path, file)
                demographics = "E:\\Data\\Brain\\CNseg\\Segmentations\\IXI.xls"
                key_column_name = 'IXI_ID'
                value_column_name = 'AGE'
                data_dict = read_excel_and_create_dict(demographics, key_column_name, value_column_name)
                age = int(data_dict[int(folder)])
                sequence = file.split('-')[-1].split('.')[0]
                if f'{sequence}' in segmentation: segmentation = os.path.join(data_dir, folder_path, segmentation)
                else: segmentation = None
                if sequence == 'MRA': sequence = 'T1'
                else: sequence = sequence
                template = find_template_match(age, sequence)
                toTemplateRegistration(file_path, template, new_dir, segmentation)
                print(f"converted {file}")
            else:
                file_path = os.path.join(data_dir, file)
                toTemplateRegistration(file_path, template, new_dir, segmentation)
                print(f"converted {file}")
    return 0


if __name__ == '__main__':

    data_dir = "E:\\Data\\Brain\\CNseg\\Segmentations"
    new_dir = "E:\\Data\\Brain\\CNseg\\Segmentations\\CoReg"
    template = "C:\\Users\Austin Tapp\\Documents\\ImagePreProcessUtils\\PPutils\\ReferenceMRIs"
    multiage = True

    AlignToTemplate(data_dir, new_dir, template, multiage)
    print("Done!")
