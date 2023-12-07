import os
import SimpleITK as sitk
import numpy as np

def find_largest_image(directory):
    largest_size_x = 0
    largest_size_y = 0
    largest_size_z = 0
    largest_size_overall = 0

    largest_image_x = None
    largest_image_y = None
    largest_image_z = None
    largest_overall = None

    dimension_count = 0
    num_channel_count = 0

    # Get a list of all files in the directory
    files = os.listdir(directory)

    for file in files:
        if file == 'overview':
            continue
        file_path = os.path.join(directory, file)
        image = sitk.ReadImage(file_path)

        # Get the size of the image
        size = image.GetSize()
        dimension = image.GetDimension()
        num_channels = image.GetNumberOfComponentsPerPixel()

        # Check if the image has a dimension of 3 and 3 channels
        if dimension != 3:
            print(f"Image {file_path} does not have a dimension of 3")
            dimension_count += 1

        if num_channels != 1:
            print(f"Image {file_path} does not have 1 channels")
            num_channel_count += 1

        # Compare the sizes in each dimension
        if size[0] > largest_size_x:
            largest_size_x = size[0]
            largest_image_x = file_path

        if size[1] > largest_size_y:
            largest_size_y = size[1]
            largest_image_y = file_path

        if size[2] > largest_size_z:
            largest_size_z = size[2]
            largest_image_z = file_path

        if (size[0] * size[1] * size[2]) > largest_size_overall:
            largest_size_overall = (size[0] * size[1] * size[2])
            largest_overall = file_path

    return largest_image_x, largest_size_x, largest_image_y, largest_size_y, largest_image_z, largest_size_z, \
           largest_overall, num_channel_count, dimension_count


def find_smallest_image(directory):
    smallest_size_x = float('inf')
    smallest_size_y = float('inf')
    smallest_size_z = float('inf')
    smallest_size_overall = float('inf')

    smallest_image_x = None
    smallest_image_y = None
    smallest_image_z = None
    smallest_overall = None

    dimension_count = 0
    num_channel_count = 0

    # Get a list of all files in the directory
    files = os.listdir(directory)

    for file in files:
        if file == 'overview':
            continue
        file_path = os.path.join(directory, file)
        image = sitk.ReadImage(file_path)

        # Get the size of the image
        size = image.GetSize()
        dimension = image.GetDimension()
        num_channels = image.GetNumberOfComponentsPerPixel()

        # Check if the image has a dimension of 3 and 1 channel
        if dimension != 3:
            print(f"Image {file_path} does not have a dimension of 3")
            dimension_count += 1

        if num_channels != 1:
            print(f"Image {file_path} does not have 1 channel")
            num_channel_count += 1

        # Compare the sizes in each dimension
        if size[0] < smallest_size_x:
            smallest_size_x = size[0]
            smallest_image_x = file_path

        if size[1] < smallest_size_y:
            smallest_size_y = size[1]
            smallest_image_y = file_path

        if size[2] < smallest_size_z:
            smallest_size_z = size[2]
            smallest_image_z = file_path

        if (size[0] * size[1] * size[2]) < smallest_size_overall:
            smallest_size_overall = (size[0] * size[1] * size[2])
            smallest_overall = file_path

    return smallest_image_x, smallest_size_x, smallest_image_y, smallest_size_y, smallest_image_z, smallest_size_z, \
           smallest_overall, num_channel_count, dimension_count

def pixel_spacing(directory):
    files = os.listdir(directory)
    spacing = None
    spacing_x = []
    spacing_y = []
    spacing_z = []

    for file in files:
        if 'T1' in file:
            file_path = os.path.join(directory, file)
            image = sitk.ReadImage(file_path)
            spacing = image.GetSpacing()
            spacing_x.append(spacing[0])
            spacing_y.append(spacing[1])
            spacing_z.append(spacing[2])
        else:
            continue

    spacing_x_mean = np.mean(spacing_x)
    spacing_x_std = np.std(spacing_x)

    spacing_y_mean = np.mean(spacing_y)
    spacing_y_std = np.std(spacing_y)

    spacing_z_mean = np.mean(spacing_z)
    spacing_z_std = np.std(spacing_z)

    spacing = [spacing_x_mean, spacing_x_std, spacing_y_mean, spacing_y_std, spacing_z_mean, spacing_z_std]
    return spacing


if __name__ == '__main__':
    # Specify the directory containing the volumes
    directory = "E:\\Data\\CNH_Paired\\asNifti"

    spacing = pixel_spacing(directory)
    print(spacing)

    # Find the largest image in each dimension
    largest_image_x, largest_size_x, largest_image_y, largest_size_y, largest_image_z, largest_size_z,\
    largest_overall, num_channel_count, dimension_count = find_largest_image(directory)

    # Find the smallest image in each dimension
    smallest_image_x, smallest_size_x, smallest_image_y, smallest_size_y, smallest_image_z, smallest_size_z, \
    smallest_overall, num_channel_count, dimension_count = find_smallest_image(directory)

    if largest_image_x is not None:
        print(f"Largest image in X dimension: {largest_image_x} at {largest_size_x}")
    if smallest_image_x is not None:
        print(f"Smallest image in X dimension: {smallest_image_x} at {smallest_size_x}")
    else:
        print("No images found in the directory for the X dimension.")

    if largest_image_y is not None:
        print(f"Largest image in Y dimension: {largest_image_y} at {largest_size_y}")
    if smallest_image_y is not None:
        print(f"Smallest image in Y dimension: {smallest_image_y} at {smallest_size_y}")
    else:
        print("No images found in the directory for the Y dimension.")

    if largest_image_z is not None:
        print(f"Largest image in Z dimension: {largest_image_z} at {largest_size_z}")
    if smallest_image_z is not None:
        print(f"Smallest image in Z dimension: {smallest_image_z} at {smallest_size_z}")
    else:
        print("No images found in the directory for the Z dimension.")

    if num_channel_count is not None:
        print(f"Number of images without 3 channels: {num_channel_count}")
    else:
        print("All images found have 3 channels")

    if dimension_count is not None:
        print(f"Number of images without 3 dimensions: {dimension_count}")
    else:
        print("All images found have 3 dimensions")

    print(f"the largest overall image is {largest_overall}")
    print(f"the smallest overall image is {smallest_overall}")
