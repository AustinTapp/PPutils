import os
import SimpleITK as sitk
import numpy as np

#to resize the samples while keeping them their original size for the purpose of suture segmentations
#downstream, images will be padded so that the largest size is 512x512x256

def resize_image_isotropically(image_dir, output_path):
    files = os.listdir(image_dir)
    for file in files:
        image = sitk.ReadImage(os.path.join(image_dir, file))
        size = image.GetSize()
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        orientation = image.GetDirection()

        scaling_factor = [spacing[0] / 1.0, spacing[1] / 1.0, spacing[2] / 1.0]
        target_size = [int(size[0] * scaling_factor[0]),
                       int(size[1] * scaling_factor[1]),
                       int(size[2] * scaling_factor[2])]

        resampler = sitk.ResampleImageFilter()
        resampler.SetInterpolator(sitk.sitkLanczosWindowedSinc)
        resampler.SetOutputSpacing([1.0, 1.0, 1.0])
        resampler.SetSize(target_size)
        resampler.SetOutputOrigin(origin)
        resampler.SetOutputDirection(orientation)

        resampled_image = resampler.Execute(image)

        resampled_image_array = sitk.GetArrayFromImage(resampled_image)
        resampled_image_array[resampled_image_array < -690] = -3024
        resampled_image = sitk.GetImageFromArray(resampled_image_array)

        resampled_image.SetOrigin(origin)
        resampled_image.SetDirection(orientation)

        sitk.WriteImage(resampled_image, os.path.join(output_path, file))


if __name__ == '__main__':
    data_dir = "E:\\Data\\CNH_Paired\\NoBedCTs"
    output = "E:\\Data\\CNH_Paired\\ResampledCTs"

    resize_image_isotropically(data_dir, output)

    print("Done!")
