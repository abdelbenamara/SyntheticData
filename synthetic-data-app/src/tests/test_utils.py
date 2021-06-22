import os

from werkzeug.datastructures import FileStorage

from .. import utils

TESTS_DIR = 'tmp_tests_dir'
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
TARGET_DIR = os.path.join(CURRENT_DIR, TESTS_DIR)


def test_clean_create_dir_to_use():
    utils.clean_create_dir(TESTS_DIR, CURRENT_DIR)
    assert os.path.isdir(TARGET_DIR)


def test_save_file():
    file = FileStorage(
        stream=open(os.path.join(CURRENT_DIR, 'resources/3_corresp_Geography_City.txt'), 'rb'),
        filename='test_save_file.txt')
    utils.save_file(file, TARGET_DIR)
    assert os.path.isfile(os.path.join(TARGET_DIR, file.filename))


def test_create_param_file():
    utils.create_param_file('10000', '300', 'Surname', 'Age,Gender,Exited,HasCrCard,IsActiveMember,City',
                            'Geography', 'RowNumber', 'drop', 'Age,Geography', TARGET_DIR)
    assert os.path.isfile(os.path.join(TARGET_DIR, 'param_file.txt'))


def test_zip_files():
    target_zip_folder = 'test_zip_files.zip'
    utils.zip_files(TARGET_DIR, target_zip_folder)
    assert os.path.isfile(os.path.join(TARGET_DIR, target_zip_folder))


def test_clean_create_dir_to_remove():
    utils.clean_create_dir(TESTS_DIR, CURRENT_DIR)
    os.rmdir(TARGET_DIR)
    assert not os.path.isdir(TARGET_DIR)
