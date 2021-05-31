import os
import shutil
import zipfile
from os.path import basename

from werkzeug.utils import secure_filename


def clean_create_dir(target_dir_name, parent_dir):
    dir_path = os.path.join(parent_dir, target_dir_name)
    for dirname in os.listdir(parent_dir):
        if dirname == target_dir_name:
            shutil.rmtree(dir_path)
            break
    os.mkdir(dir_path)
    return dir_path


def save_file(file, target_dir):
    filename = secure_filename(file.filename)
    file_path = os.path.join(target_dir, filename)
    file.save(file_path)
    return file_path


def create_param_file(samples, epochs, names, categories, correlees, drop, unnamed, compare, target_dir):
    file_path = os.path.join(target_dir, 'param_file.txt')
    file = open(file_path, "w")
    file.write(''.join(('samples,', str(samples), '\n')))
    file.write(''.join(('epochs,', str(epochs), '\n')))
    file.write(''.join(('names,', names, '\n')))
    file.write(''.join(('categories,', categories, '\n')))
    file.write(''.join(('correlees,', correlees, '\n')))
    file.write(''.join(('drop,', drop, '\n')))
    file.write(''.join(('unnamed,', unnamed, '\n')))
    file.write(''.join(('compare,', compare, '\n')))
    file.close()
    return file_path


def zip_files(target_dir, target_zip_folder):
    zipfolder = zipfile.ZipFile(os.path.join(target_dir, target_zip_folder), 'w', compression=zipfile.ZIP_STORED)
    for filename in os.listdir(target_dir):
        if filename == target_zip_folder:
            continue
        file = os.path.join(target_dir, filename)
        zipfolder.write(file, basename(filename))
        os.remove(file)
    zipfolder.close()
