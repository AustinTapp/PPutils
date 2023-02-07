import os
import pydicom
import numpy as np
from PIL import Image

if __name__ == '__main__':
    #directory with all DICOM folders data
    data_dir = "C:\\Users\\Austin Tapp\\Downloads\\dcms"
    #data_dir = "C:\\Users\\Liz\\Downloads\\DICOMs"

    #get subfolders (each patient folder)
    list_subfolders_with_paths = [f.path for f in os.scandir(data_dir) if f.is_dir()]
    for i in range(len(list_subfolders_with_paths)):
        #look at the files within the subfolder
        patient_files_in_subfolder = [f.path for f in os.scandir(list_subfolders_with_paths[i])]
        for j in range(len(patient_files_in_subfolder)):
            #ignore files with a small size (headers)
            file_size = os.path.getsize(patient_files_in_subfolder[j])
            if file_size > 20000:
                #we think it is a DCM file not the header, convert to JPG
                dcm = pydicom.dcmread(patient_files_in_subfolder[j])
                jpeg = dcm.pixel_array
                jpeg = (jpeg / 65535 * 255).astype(np.uint8)
                jpeg = Image.fromarray(jpeg, "L")
                jpeg = jpeg.convert("RGB")
                jpeg.save(patient_files_in_subfolder[j]+".jpg", "JPEG", quality=100)

                #convert to PNG
                png = dcm.pixel_array
                png = Image.fromarray(png, "I;16")
                png.save(patient_files_in_subfolder[j]+".png", "PNG", optimize=True)
