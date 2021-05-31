import os
import time
import uuid

from flask import Flask, session, flash, render_template, redirect, url_for, send_from_directory
from flask_wtf import CSRFProtect
from sassutils.wsgi import SassMiddleware

from .forms import ParamFileForm, ParamFieldsForm
from .gans import synthetic_generation
from .utils import clean_create_dir, save_file, create_param_file, zip_files

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'app': {'sass_path': 'static/scss', 'css_path': 'static/css', 'strip_extension': True}
})
csrf = CSRFProtect(app)


@app.route('/')
def index():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()
    if 'form_error' in session:
        flash('There was an error in your form.\\nPlease make sure to fill in all fields correctly.', 'error')
        session.pop('form_error', None)
    if 'id_missing' in session:
        flash('Generation ID is missing.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_missing', None)
    if 'id_invalid' in session:
        flash('Generation ID is invalid.\\nPlease generate a new sample to fix this issue.', 'error')
        session.pop('id_invalid', None)
    if 'id_not_finished' in session:
        flash('Please try to download your sample later.\\nSynthetic data generation might take some time.', 'info')
        session.pop('id_processing', None)
    if 'id_finished' in session:
        flash('Congratulations, your sample is ready !\\nYou can now preview or download it below.', 'success')
        session.pop('id_finished', None)
    return render_template('index.html', name='index', file_form=file_form, fields_form=fields_form)


@app.route('/prepare', methods=['POST'])
def prepare():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()
    if not (file_form.validate_on_submit() or fields_form.validate_on_submit()):
        session['form_error'] = True
        return redirect(url_for('index'))
    else:
        if 'generationID' in session:
            all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
            all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
            generation_id = session['generationID']
            clean_create_dir(generation_id, all_resources_dir)
            os.rmdir(os.path.join(all_resources_dir, generation_id))
            clean_create_dir(generation_id, all_results_dir)
            os.rmdir(os.path.join(all_results_dir, generation_id))
        generation_id = ''.join([time.strftime('%H%M%S'), str(uuid.uuid4().hex)])
        session['generationID'] = generation_id
        return redirect(url_for('generate'), code=307)


@app.route('/generate', methods=['POST'])
def generate():
    file_form = ParamFileForm()
    fields_form = ParamFieldsForm()

    all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
    all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
    generation_id = session['generationID']

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
    zip_files(result_dir, app.config['RESULT_FOLDER'])

    session['id_finished'] = True
    return redirect(url_for('index'))


@app.route('/preview', methods=['GET', 'POST'])
def preview():
    # TODO : ouvrir le zip de résultat dans le code et afficher les '*-summary.pdf' (dans une iframe ?)
    return 0


@app.route('/result', methods=['POST'])
def result():
    if 'generationID' in session:
        generation_id = session['generationID']
        all_results_dir = os.path.join(app.instance_path, app.config['RESULTS'])
        for dirname in os.listdir(all_results_dir):
            if dirname == generation_id:
                result_dir = os.path.join(all_results_dir, generation_id)
                for filename in os.listdir(result_dir):
                    if filename == app.config['RESULT_FOLDER']:
                        return send_from_directory(result_dir, filename, as_attachment=True)

        all_resources_dir = os.path.join(app.instance_path, app.config['RESOURCES'])
        for dirname in os.listdir(all_resources_dir):
            if dirname == generation_id:
                session['id_not_finished'] = True
                return redirect(url_for('index'))

        session['id_invalid'] = True
        return redirect(url_for('index'))
    else:
        session['id_missing'] = True
        return redirect(url_for('index'))
