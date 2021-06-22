import os
import re
import time
import uuid
import zipfile

import PyPDF2
from flask import Flask, session, flash, render_template, redirect, url_for, make_response, send_from_directory
from flask_wtf import CSRFProtect
from sassutils.wsgi import SassMiddleware

from .forms import ParamFileForm, ParamFieldsForm
from .gans import synthetic_generation
from .utils import clean_create_dir, save_file, create_param_file, zip_files

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'src': {'sass_path': 'static/scss', 'css_path': 'static/css', 'strip_extension': True}
})
csrf = CSRFProtect(app)


@app.route('/')
def index():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()
    flash_management()
    return render_template('index.html', name='index', file_form=file_form, fields_form=fields_form)


@app.route('/prepare', methods=['POST'])
def prepare():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()
    if not (file_form.validate_on_submit() or fields_form.validate_on_submit()):
        session['form_error'] = True
        return redirect(url_for('index'))
    else:
        if 'generation_id' in session:
            all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
            all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
            generation_id = session['generation_id']
            clean_create_dir(generation_id, all_resources_dir)
            os.rmdir(os.path.join(all_resources_dir, generation_id))
            clean_create_dir(generation_id, all_results_dir)
            os.rmdir(os.path.join(all_results_dir, generation_id))
        generation_id = ''.join([time.strftime('%H%M%S'), str(uuid.uuid4().hex)])
        session['generation_id'] = generation_id
        return redirect(url_for('generate'), code=307)


@app.route('/generate', methods=['POST'])
def generate():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()

    all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
    all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
    generation_id = session['generation_id']

    resources_dir = clean_create_dir(generation_id, all_resources_dir)
    result_dir = clean_create_dir(generation_id, all_results_dir)

    corresp_files = []

    if file_form.validate_on_submit():
        model = file_form.file_form_model.data
        dataset = save_file(file_form.file_form_dataset.data, resources_dir)
        param_file = save_file(file_form.file_form_param.data, resources_dir)
        if file_form.file_form_corresp.data[0] != '':
            for file in file_form.file_form_corresp.data:
                try:
                    corresp_files.append(save_file(file, resources_dir))
                finally:
                    continue
    else:
        model = fields_form.fields_form_model.data
        dataset = save_file(fields_form.fields_form_dataset.data, resources_dir)
        samples = fields_form.fields_form_samples.data
        epochs = fields_form.fields_form_epochs.data
        names = fields_form.fields_form_names.data
        categories = fields_form.fields_form_categories.data
        correlees = fields_form.fields_form_correlees.data
        drop = fields_form.fields_form_drop.data
        unnamed = fields_form.fields_form_unnamed.data
        compare = fields_form.fields_form_compare.data
        param_file = create_param_file(samples, epochs, names, categories,
                                       correlees, drop, unnamed, compare, resources_dir)
        if fields_form.fields_form_corresp.data[0] != '':
            for file in fields_form.fields_form_corresp.data:
                try:
                    corresp_files.append(save_file(file, resources_dir))
                finally:
                    continue

    synthetic_generation(model, dataset, param_file, corresp_files, result_dir)
    clean_create_dir(generation_id, all_resources_dir)
    os.rmdir(os.path.join(all_resources_dir, generation_id))
    zip_files(result_dir, app.config['SYNTHETIC_DATA'])

    session['sample_ready'] = True
    return redirect(url_for('index'))


@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'generation_id' in session:
        generation_id = session['generation_id']
        all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
        for dirname in os.listdir(all_results_dir):
            if dirname == generation_id:
                result_dir = os.path.join(all_results_dir, generation_id)
                for filename in os.listdir(result_dir):
                    if filename == app.config['SYNTHETIC_DATA']:
                        # TODO : faire une méthode dans utils pour ce qu'il y a ci-dessous
                        pdf_merger = PyPDF2.PdfFileMerger()
                        with zipfile.ZipFile(os.path.join(result_dir, filename)) as zipfolder:
                            for summary_file in zipfolder.namelist():
                                if re.match('.*summary\\.pdf', summary_file):
                                    for file in result_dir:
                                        if file == summary_file:
                                            os.remove(file)
                                            break
                                    zipfolder.extract(summary_file, result_dir)
                                    target_file = os.path.join(result_dir, summary_file)
                                    pdf_merger.append(target_file)
                                    os.remove(target_file)
                        for file in os.listdir(result_dir):
                            if file == app.config['SUMMARY_PDF']:
                                os.remove(file)
                                continue
                        binary_file = os.path.join(result_dir, app.config['SUMMARY_PDF'])
                        pdf_merger.write(binary_file)
                        pdf_merger.close()
                        with open(binary_file, 'rb') as b:
                            pdf_bytes = b.read()
                        os.remove(binary_file)
                        preview_file = make_response(pdf_bytes)
                        preview_file.headers['Content-Type'] = 'application/pdf'
                        preview_file.headers['Content-Disposition'] = 'inline; filename=summary.pdf'
                        return preview_file

        if generation_not_completed(generation_id):
            return redirect(url_for('index'))

        session['id_invalid'] = True
        return redirect(url_for('index'))
    else:
        session['id_missing'] = True
        return redirect(url_for('index'))


@app.route('/result', methods=['POST'])
def result():
    if 'generation_id' in session:
        generation_id = session['generation_id']
        all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
        for dirname in os.listdir(all_results_dir):
            if dirname == generation_id:
                result_dir = os.path.join(all_results_dir, generation_id)
                for filename in os.listdir(result_dir):
                    if filename == app.config['SYNTHETIC_DATA']:
                        return send_from_directory(result_dir, filename, as_attachment=True)

        if generation_not_completed(generation_id):
            return redirect(url_for('index'))

        session['id_invalid'] = True
        return redirect(url_for('index'))
    else:
        session['id_missing'] = True
        return redirect(url_for('index'))


def generation_not_completed(generation_id):
    all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
    for dirname in os.listdir(all_resources_dir):
        if dirname == generation_id:
            session['generation_not_completed'] = True
            return True
    return False


def flash_management():
    if 'form_error' in session:
        flash('There was an error in your form.\\nPlease make sure to fill in all fields correctly.', 'error')
        session.pop('form_error', None)
    if 'id_missing' in session:
        flash('Generation ID is missing.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_missing', None)
    if 'id_invalid' in session:
        flash('Generation ID is invalid.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_invalid', None)
    if 'generation_not_completed' in session:
        flash('Your sample is not yet completed.\\nPlease come back later to preview or download it.', 'warning')
        session.pop('generation_not_completed', None)
    elif 'generation_id' in session:
        in_progress = False
        all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
        generation_id = session['generation_id']
        for dirname in os.listdir(all_resources_dir):
            if dirname == generation_id:
                flash('Your sample is being generated.\\nIt might take some time, you can come back later.', 'info')
                session.pop('generation_in_progress', None)
                in_progress = True
        if not in_progress:
            all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
            for dirname in os.listdir(all_results_dir):
                if dirname == generation_id:
                    session['sample_ready'] = True
    if 'sample_ready' in session:
        flash('You result zip folder is available.\\nYou can download it or preview its summary below.', 'success')
        session.pop('sample_ready', None)
