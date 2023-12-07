import os
import shutil
import SimpleITK as sitk
import vtk

def clean(directory):
    count = 0
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            files_in_folder = os.listdir(folder_path)
            if len(files_in_folder) < 4:
                new_dir_path = "D:\\IFA\\IFA_failed"
                os.rename(folder_path, os.path.join(new_dir_path, folder))
                count += 1
    return count


def invert(directory):
    count = 0
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".tfm"):
                    tfm_file_path = os.path.join(folder_path, file)
                    tfm = sitk.ReadTransform(tfm_file_path)
                    inverse = tfm.GetInverse()
                    new_file_path = os.path.join(folder_path, "TemplateToSubjectTransform.mat")
                    sitk.WriteTransform(inverse, new_file_path)
                    count += 1
    return count


def rename(directory):
    count = 0
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file == "output.vtk":
                    old_file_path = os.path.join(folder_path, file)
                    new_file_path = os.path.join(folder_path, "Malformations_AtlasProjection_75.vtk")
                    try:
                        os.rename(old_file_path, new_file_path)
                    except FileExistsError:
                        shutil.move(old_file_path, new_file_path)
                    count += 1
    return count

def correct(directory):
    count = 0
    tfm = vtk.vtkTransform()
    tfm.SetMatrix((-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0))
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file == "Malformations_AtlasProjection_75.vtk":
                    reader = vtk.vtkPolyDataReader()
                    reader.SetFileName(os.path.join(folder_path, file))
                    reader.Update()
                    original_mesh = reader.GetOutput()

                    transformed_mesh = vtk.vtkTransformPolyDataFilter()
                    transformed_mesh.SetInputData(original_mesh)
                    transformed_mesh.SetTransform(tfm)
                    transformed_mesh.Update()
                    output_mesh = transformed_mesh.GetOutput()

                    writer = vtk.vtkPolyDataWriter()
                    writer.SetFileName(os.path.join(folder_path, file))
                    writer.SetInputData(output_mesh)
                    writer.Write()
                    count += 1
    return count

def move(directory, new_dir):
    count = 0
    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        new_folder_path = os.path.join(new_dir, folder)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file == "LandmarksSubject.fcsv":
                    old_file_path = os.path.join(folder_path, file)
                    shutil.copy(old_file_path, os.path.join(new_folder_path, "LandmarksSubject.fcsv"))
                if file == "Malformations_AtlasProjection_75.vtk":
                    old_file_path = os.path.join(folder_path, file)
                    shutil.copy(old_file_path, os.path.join(new_folder_path, "Malformations_AtlasProjection_75.vtk"))
                if file == "TemplateToSubjectTransform.mat":
                    old_file_path = os.path.join(folder_path, file)
                    shutil.copy(old_file_path, os.path.join(new_folder_path, "TemplateToSubjectTransform.mat"))
                count += 1
    return count



if __name__ == '__main__':
    data_dir = "E:\\Data\\IFA\\IFA_data\\Metopic\\Processed"
    new = "D:\\IFA\\IFA"
    #move = move(data_dir, new)

    #print("done")
    #emptys = clean(data_dir)
    #print(f"{emptys} directories removed.")

    inversions = invert(data_dir)
    print(f"{inversions} transforms corrected.")

    rename = rename(data_dir)
    print(f"{rename} output meshes renamed.")

    correct = correct(data_dir)
    print(f"{correct} output meshes corrected.")

