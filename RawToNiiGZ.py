import os
import struct
import numpy as np
import SimpleITK as sitk

def convert(raw_file_path, width, height, data_type, endianness, output):
    with open(raw_file_path, 'rb') as raw_file:
        raw_data = raw_file.read()

    # Unpack the binary data into a flat list of floats
    pixel_values = struct.unpack(endianness + data_type * (len(raw_data) // struct.calcsize(data_type)), raw_data)

    # Reshape the flat list into a 2D array
    pixels = np.array(pixel_values).reshape((height, width))
    image = sitk.GetImageFromArray(pixels)
    sitk.WriteImage(image, output)

def process_folder(dir, d_type, endian):
    for folder in os.listdir(dir):
        folder_path = os.path.join(dir, folder)
        for file in ['Baseline', 'Target']:
            file_path = os.path.join(folder_path, file)
            for image_file in os.listdir(file_path):
                image_path = os.path.join(file_path, image_file)
                if os.path.isfile(image_path):
                    image_name = image_path.split("\\")[-1].split("_")
                    name = image_name[1] + "_" + image_name[3] + "_" + image_name[2] + ".nii.gz"
                    output = os.path.join("E:\\Data\\CT_MAR\\asNifti" , name)

                    width, height = (900, 1000) if 'sino' in image_file else (512, 512)
                    convert(image_path, width, height, d_type, endian, output)


if __name__ == '__main__':
    height = 512
    width = 512

    d_type = 'f'
    endianness = '<'  # Little endian

    directory = "E:\\Data\\CT_MAR\\images"
    process_folder(directory, d_type, endianness)

    #convert(directory, width, height, d_type, endianness,
            #output="E:\\Data\\CT_MAR\\images\\body1\\Baseline\\training_body_metalart_img1_512x512x1.nii.gz")


"""
Potential data types
'b': Signed char
'B': Unsigned char
'h': Short (2 bytes)
'H': Unsigned short (2 bytes)
'i': Int (4 bytes)
'I': Unsigned int (4 bytes)
'q': Long long (8 bytes)
'Q': Unsigned long long (8 bytes)
'f': Float (4 bytes)
'd': Double (8 bytes)
"""
