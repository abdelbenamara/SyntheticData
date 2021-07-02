import os
import time
import uuid

from flask import Flask, session, render_template, redirect, url_for, make_response, send_from_directory
from flask_wtf import CSRFProtect
from sassutils.wsgi import SassMiddleware

from .forms import GenerationParamFileForm, GenerationParamFieldsForm, \
    EvaluationParamFileForm, EvaluationParamFieldsForm
from .gans import synthetic_generation, synthetic_evaluation
from .utils import clean_create_dir, save_file, create_generation_param_file, create_evaluation_param_file, zip_files, \
    get_bytes_from_all_pdf_in_zip, generation_not_completed, flash_management

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'src': {'sass_path': 'static/scss', 'css_path': 'static/css', 'strip_extension': True}
})
csrf = CSRFProtect(app)

ALL_RESOURCES_DIR = os.path.join(app.instance_path, app.config['RESOURCES'])
ALL_RESULTS_DIR = os.path.join(app.instance_path, app.config['RESULTS'])


@app.route('/')
def index():
    generation_file_form = GenerationParamFileForm()
    generation_fields_form = GenerationParamFieldsForm()
    evaluation_file_form = EvaluationParamFileForm()
    evaluation_fields_form = EvaluationParamFieldsForm()
    flash_management(ALL_RESOURCES_DIR, ALL_RESULTS_DIR, app.config['SUMMARY_PDF'], session)
    return render_template('index.html', name='index', generation_file_form=generation_file_form,
                           generation_fields_form=generation_fields_form, evaluation_file_form=evaluation_file_form,
                           evaluation_fields_form=evaluation_fields_form)


@app.route('/prepare', methods=['POST'])
def prepare():
    generation_file_form = GenerationParamFileForm()
    generation_fields_form = GenerationParamFieldsForm()
    evaluation_file_form = EvaluationParamFileForm()
    evaluation_fields_form = EvaluationParamFieldsForm()
    if not (generation_file_form.validate_on_submit() or generation_fields_form.validate_on_submit()
            or evaluation_file_form.validate_on_submit() or evaluation_fields_form.validate_on_submit()):
        session['form_error'] = True
        return redirect(url_for('index'))
    else:
        if 'session_id' in session:
            session_id = session['session_id']
            clean_create_dir(session_id, ALL_RESOURCES_DIR)
            os.rmdir(os.path.join(ALL_RESOURCES_DIR, session_id))
            clean_create_dir(session_id, ALL_RESULTS_DIR)
            os.rmdir(os.path.join(ALL_RESULTS_DIR, session_id))
        session_id = ''.join([time.strftime('%H%M%S'), str(uuid.uuid4().hex)])
        session['session_id'] = session_id
        if generation_file_form.validate_on_submit() or generation_fields_form.validate_on_submit():
            return redirect(url_for('generate'), code=307)
        else:
            return redirect(url_for('evaluate'), code=307)


@app.route('/generate', methods=['POST'])
def generate():
    generation_file_form = GenerationParamFileForm()
    generation_fields_form = GenerationParamFieldsForm()

    session_id = session['session_id']

    resources_dir = clean_create_dir(session_id, ALL_RESOURCES_DIR)
    result_dir = clean_create_dir(session_id, ALL_RESULTS_DIR)

    corresp_files = []

    if generation_file_form.validate_on_submit():
        model = generation_file_form.generation_file_model.data
        dataset = save_file(generation_file_form.generation_file_dataset.data, resources_dir)
        param_file = save_file(generation_file_form.generation_file_param.data, resources_dir)
        if generation_file_form.generation_file_corresp.data[0] != '':
            for file in generation_file_form.generation_file_corresp.data:
                try:
                    corresp_files.append(save_file(file, resources_dir))
                finally:
                    continue
    else:
        model = generation_fields_form.generation_fields_model.data
        dataset = save_file(generation_fields_form.generation_fields_dataset.data, resources_dir)
        samples = generation_fields_form.generation_fields_samples.data
        epochs = generation_fields_form.generation_fields_epochs.data
        names = generation_fields_form.generation_fields_names.data
        categories = generation_fields_form.generation_fields_categories.data
        correlees = generation_fields_form.generation_fields_correlees.data
        drop = generation_fields_form.generation_fields_drop.data
        unnamed = generation_fields_form.generation_fields_unnamed.data
        compare = generation_fields_form.generation_fields_compare.data
        param_file = create_generation_param_file(samples, epochs, names, categories,
                                                  correlees, drop, unnamed, compare, resources_dir)
        if generation_fields_form.generation_fields_corresp.data[0] != '':
            for file in generation_fields_form.generation_fields_corresp.data:
                try:
                    corresp_files.append(save_file(file, resources_dir))
                finally:
                    continue

    synthetic_generation(model, dataset, param_file, corresp_files, result_dir, app)
    clean_create_dir(session_id, ALL_RESOURCES_DIR)
    os.rmdir(os.path.join(ALL_RESOURCES_DIR, session_id))
    zip_files(result_dir, app.config['SYNTHETIC_DATA'])

    session['sample_ready'] = True
    return redirect(url_for('index'))


@app.route('/evaluate', methods=['POST'])
def evaluate():
    evaluation_file_form = EvaluationParamFileForm()
    evaluation_fields_form = EvaluationParamFieldsForm()

    session_id = session['session_id']

    resources_dir = clean_create_dir(session_id, ALL_RESOURCES_DIR)
    result_dir = clean_create_dir(session_id, ALL_RESULTS_DIR)

    if evaluation_file_form.validate_on_submit():
        real_dataset = save_file(evaluation_file_form.evaluation_file_dataset.data, resources_dir)
        param_file = save_file(evaluation_file_form.evaluation_file_param.data, resources_dir)
        synthetic_dataset = save_file(evaluation_file_form.evaluation_file_synthetic.data, resources_dir)
    else:
        real_dataset = save_file(evaluation_fields_form.evaluation_fields_dataset.data, resources_dir)
        names = evaluation_fields_form.evaluation_fields_names.data
        correlees = evaluation_fields_form.evaluation_fields_correlees.data
        categories = evaluation_fields_form.evaluation_fields_categories.data
        drop = evaluation_fields_form.evaluation_fields_drop.data
        unnamed = evaluation_fields_form.evaluation_fields_unnamed.data
        compare = evaluation_fields_form.evaluation_fields_compare.data
        param_file = create_evaluation_param_file(names, categories, correlees, drop, unnamed, compare, resources_dir)
        synthetic_dataset = save_file(evaluation_fields_form.evaluation_fields_synthetic.data, resources_dir)

    synthetic_evaluation(real_dataset, param_file, synthetic_dataset, result_dir, app)
    clean_create_dir(session_id, ALL_RESOURCES_DIR)
    os.rmdir(os.path.join(ALL_RESOURCES_DIR, session_id))

    session['evaluation_ready'] = True
    return redirect(url_for('index'))


@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'session_id' in session:
        session_id = session['session_id']
        for dirname in os.listdir(ALL_RESULTS_DIR):
            if dirname == session_id:
                result_dir = os.path.join(ALL_RESULTS_DIR, session_id)
                for filename in os.listdir(result_dir):
                    if filename == app.config['SYNTHETIC_DATA']:
                        pdf_bytes = get_bytes_from_all_pdf_in_zip(result_dir, filename, app.config['SUMMARY_PDF'])
                        preview_file = make_response(pdf_bytes)
                        preview_file.headers['Content-Type'] = 'application/pdf'
                        preview_file.headers['Content-Disposition'] = 'inline; filename=summary.pdf'
                        return preview_file

        if generation_not_completed(ALL_RESOURCES_DIR, session_id, session):
            return redirect(url_for('index'))

        session['id_invalid'] = True
        return redirect(url_for('index'))
    else:
        session['id_missing'] = True
        return redirect(url_for('index'))


@app.route('/result', methods=['POST'])
def result():
    if 'session_id' in session:
        session_id = session['session_id']
        for dirname in os.listdir(ALL_RESULTS_DIR):
            if dirname == session_id:
                result_dir = os.path.join(ALL_RESULTS_DIR, session_id)
                for filename in os.listdir(result_dir):
                    if filename == app.config['SYNTHETIC_DATA'] or filename == app.config['SUMMARY_PDF']:
                        return send_from_directory(result_dir, filename, as_attachment=True)

        if generation_not_completed(ALL_RESOURCES_DIR, session_id, session):
            return redirect(url_for('index'))

        session['id_invalid'] = True
        return redirect(url_for('index'))
    else:
        session['id_missing'] = True
        return redirect(url_for('index'))
