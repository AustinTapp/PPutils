import numpy as np
import nibabel as nib

def scale_intensity(input_image, reference_image):
    # Load input image
    input_nifti = nib.load(input_image)
    input_data = input_nifti.get_fdata()

    # Load reference image
    reference_nifti = nib.load(reference_image)
    reference_data = reference_nifti.get_fdata()

    # Scale intensities
    scaled_data = (input_data - np.min(input_data)) / (np.max(input_data) - np.min(input_data))
    scaled_data = scaled_data * (np.max(reference_data) - np.min(reference_data)) + np.min(reference_data)

    # Create a new NIfTI image with scaled intensities
    scaled_nifti = nib.Nifti1Image(scaled_data, input_nifti.affine, input_nifti.header)

    # Save the scaled image
    scaled_output_image = "scaled_SynthRadmr.nii"
    nib.save(scaled_nifti, scaled_output_image)

    print("Scaled image saved as", scaled_output_image)


if __name__ == '__main__':
    input_image_path = "scaled_tfmSynthRadmr_sCT.nii"
    reference_image_path = "SynthRadGTct.nii"
    scale_intensity(input_image_path, reference_image_path)
