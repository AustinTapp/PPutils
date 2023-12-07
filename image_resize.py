import os
import SimpleITK as sitk

#to resize the samples while keeping them their original size for the purpose of suture segmentations
#downstream, images will be padded so that the largest size is 512x512x256


def resize_image(image_dir, output_dir, target):
    nifti_files = [file for file in os.listdir(image_dir) if file.endswith(".nii") or file.endswith(".nii.gz")]

    for file in nifti_files:
        file_path = os.path.join(image_dir, file)
        img = sitk.ReadImage(file_path)

        original_size = img.GetSize()
        target_size = target

        resize_factors = [float(target_size[i]) / original_size[i] for i in range(len(original_size))]

        resized_img = sitk.Resample(
            img, target_size, sitk.Transform(), sitk.sitkLanczosWindowedSinc,
            img.GetOrigin(), resize_factors, img.GetDirection(), 0.0,
            img.GetPixelIDValue()
        )

        output_path = os.path.join(output_dir, file)
        sitk.WriteImage(resized_img, output_path)
        print(f"Resized and saved: {output_path}")

if __name__ == '__main__':
    size = (256, 256, 256)

    MR_dir = "C:\\Users\\Austin Tapp\\Documents\\SynDiffSynthRad\\data\\task1_brain_restruct\\MR"
    MR_output = "C:\\Users\\Austin Tapp\\Documents\\SynDiffSynthRad\\data\\task1_brain_restruct_resize\\MR"
    resize_image(MR_dir, MR_output, size)

    CT_dir = "C:\\Users\\Austin Tapp\\Documents\\SynDiffSynthRad\\data\\task1_brain_restruct\\CT"
    CT_output = "C:\\Users\\Austin Tapp\\Documents\\SynDiffSynthRad\\data\\task1_brain_restruct_resize\\CT"
    resize_image(CT_dir, CT_output, size)

    print("Done!")
