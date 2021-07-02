from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import RadioField, MultipleFileField, StringField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired
from wtforms.widgets.html5 import NumberInput


class GenerationParamFileForm(FlaskForm):
    generation_file_model = RadioField(choices=[('ctgan', 'CTGAN'), ('tvae', 'TVAE'), ('wgan', 'WGAN'), ('all', 'ALL')],
                                       default='ctgan', validators=[InputRequired()])
    generation_file_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                        render_kw={'accept': 'text/csv'})
    generation_file_param = FileField(validators=[FileRequired(), FileAllowed(['txt'])],
                                      render_kw={'accept': 'text/plain'})
    generation_file_corresp = MultipleFileField(validators=[FileAllowed(['txt'])], render_kw={'accept': 'text/plain'})


class GenerationParamFieldsForm(FlaskForm):
    generation_fields_model = RadioField(
        choices=[('ctgan', 'CTGAN'), ('tvae', 'TVAE'), ('wgan', 'WGAN'), ('all', 'ALL')],
        default='ctgan', validators=[InputRequired()])
    generation_fields_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                          render_kw={'accept': 'text/csv'})
    generation_fields_samples = IntegerField('Samples', validators=[InputRequired()], widget=NumberInput(min=1, step=1))
    generation_fields_epochs = IntegerField('Epochs', validators=[InputRequired()], widget=NumberInput(min=1, step=1))
    generation_fields_names = StringField('Names')
    generation_fields_categories = StringField('Categories')
    generation_fields_correlees = StringField('Correlees')
    generation_fields_drop = StringField('Drop')
    generation_fields_unnamed = RadioField('Unnamed', choices=[('drop', 'Drop'), ('keep', 'Keep')],
                                           default='drop', validators=[InputRequired()])
    generation_fields_compare = StringField('Compare', validators=[InputRequired()])
    generation_fields_corresp = MultipleFileField(validators=[FileAllowed(['txt'])], render_kw={'accept': 'text/plain'})


class EvaluationParamFileForm(FlaskForm):
    evaluation_file_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                        render_kw={'accept': 'text/csv'})
    evaluation_file_param = FileField(validators=[FileRequired(), FileAllowed(['txt'])],
                                      render_kw={'accept': 'text/plain'})
    evaluation_file_synthetic = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                          render_kw={'accept': 'text/csv'})


class EvaluationParamFieldsForm(FlaskForm):
    evaluation_fields_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                          render_kw={'accept': 'text/csv'})
    evaluation_fields_names = StringField('Names')
    evaluation_fields_categories = StringField('Categories')
    evaluation_fields_correlees = StringField('Correlees')
    evaluation_fields_drop = StringField('Drop')
    evaluation_fields_unnamed = RadioField('Unnamed', choices=[('drop', 'Drop'), ('keep', 'Keep')],
                                           default='drop', validators=[InputRequired()])
    evaluation_fields_compare = StringField('Compare', validators=[InputRequired()])
    evaluation_fields_synthetic = FileField(validators=[FileRequired(), FileAllowed(['csv'])],
                                            render_kw={'accept': 'text/csv'})
