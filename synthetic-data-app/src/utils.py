import os
import re
import shutil
import zipfile
from os.path import basename

import PyPDF2
import pandas as pd
from flask import flash
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


def create_evaluation_param_file(names, categories, correlees, drop, unnamed, compare, target_dir, append=False):
    file_path = os.path.join(target_dir, 'param_file.txt')
    if append:
        file = open(file_path, "a")
    else:
        file = open(file_path, "w")
    file.write(''.join(('names,', names, '\n')))
    file.write(''.join(('categories,', categories, '\n')))
    file.write(''.join(('correlees,', correlees, '\n')))
    file.write(''.join(('drop,', drop, '\n')))
    file.write(''.join(('unnamed,', unnamed, '\n')))
    file.write(''.join(('compare,', compare, '\n')))
    file.close()
    return file_path


def create_generation_param_file(samples, epochs, names, categories, correlees, drop, unnamed, compare, target_dir):
    file_path = os.path.join(target_dir, 'param_file.txt')
    file = open(file_path, "w")
    file.write(''.join(('samples,', str(samples), '\n')))
    file.write(''.join(('epochs,', str(epochs), '\n')))
    file.close()
    return create_evaluation_param_file(names, categories, correlees, drop, unnamed, compare, target_dir, append=True)


def get_dataframe_from_csv(csv_file):
    dataframe = pd.read_csv(csv_file)
    if len(dataframe.columns.values.tolist()) == 1:
        dataframe = pd.read_csv(csv_file, delimiter=';')
    return dataframe


def get_data_from_param_file(data_type, data_list, unique=False):
    for i in range(len(data_list)):
        if data_list[i][0] == data_type:
            if unique:
                return data_list[i][1]
            else:
                return data_list[i][1:]
    if unique:
        return '0'
    else:
        return ['']


def zip_files(target_dir, target_zip_folder):
    zipfolder = zipfile.ZipFile(os.path.join(target_dir, target_zip_folder), 'w', compression=zipfile.ZIP_STORED)
    for filename in os.listdir(target_dir):
        if filename == target_zip_folder:
            continue
        file = os.path.join(target_dir, filename)
        zipfolder.write(file, basename(filename))
        os.remove(file)
    zipfolder.close()


def get_bytes_from_all_pdf_in_zip(parent_dir, zip_file, summary_pdf):
    pdf_merger = PyPDF2.PdfFileMerger()
    with zipfile.ZipFile(os.path.join(parent_dir, zip_file)) as zipfolder:
        for summary_file in zipfolder.namelist():
            if re.match('.*summary\\.pdf', summary_file):
                for file in parent_dir:
                    if file == summary_file:
                        os.remove(file)
                        break
                zipfolder.extract(summary_file, parent_dir)
                target_file = os.path.join(parent_dir, summary_file)
                pdf_merger.append(target_file)
                os.remove(target_file)
    for file in os.listdir(parent_dir):
        if file == summary_pdf:
            os.remove(file)
            continue
    binary_file = os.path.join(parent_dir, summary_pdf)
    pdf_merger.write(binary_file)
    pdf_merger.close()
    with open(binary_file, 'rb') as b:
        pdf_bytes = b.read()
    os.remove(binary_file)
    return pdf_bytes


def generation_not_completed(all_resources_dir, session_id, session):
    for dirname in os.listdir(all_resources_dir):
        if dirname == session_id:
            session['generation_not_completed'] = True
            return True
    return False


def flash_management(all_resources_dir, all_results_dir, summary_file, session):
    if 'form_error' in session:
        flash('There was an error in your form.\\nPlease make sure to fill in all fields correctly.', 'error')
        session.pop('form_error', None)
    if 'id_missing' in session:
        flash('Session ID is missing.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_missing', None)
    if 'id_invalid' in session:
        flash('Session ID is invalid.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_invalid', None)
    if 'generation_not_completed' in session:
        flash('Your sample is not yet completed.\\nPlease come back later to preview or download it.', 'warning')
        session.pop('generation_not_completed', None)
    elif 'session_id' in session:
        in_progress = False
        session_id = session['session_id']
        for dirname in os.listdir(all_resources_dir):
            if dirname == session_id:
                flash('Your sample is being generated.\\nIt might take some time, you can come back later.', 'info')
                session.pop('generation_in_progress', None)
                in_progress = True
        if not in_progress:
            for dirname in os.listdir(all_results_dir):
                if dirname == session_id:
                    for filename in os.listdir(os.path.join(all_results_dir, dirname)):
                        if filename == summary_file:
                            session['evaluation_ready'] = True
                        else:
                            session['sample_ready'] = True
    if 'sample_ready' in session:
        flash('You result zip folder is available.\\nYou can download it or preview its summary below.', 'success')
        session.pop('sample_ready', None)
    if 'evaluation_ready' in session:
        flash('You result pdf file is available.\\nYou can download it or preview it below.', 'success')
        session.pop('evaluation_ready', None)
