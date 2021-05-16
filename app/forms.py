from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import RadioField, MultipleFileField, StringField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired
from wtforms.widgets.html5 import NumberInput


class ParamFileForm(FlaskForm):
    file_form_model = RadioField(choices=[('ctgan', 'CTGAN'), ('tvae', 'TVAE'), ('wgan', 'WGAN'), ('all', 'ALL')],
                                 default='ctgan', validators=[InputRequired()])
    file_form_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])], render_kw={'accept': 'text/csv'})
    file_form_param = FileField(validators=[FileRequired(), FileAllowed(['txt'])], render_kw={'accept': 'text/plain'})
    file_form_corresp = MultipleFileField(validators=[FileAllowed(['txt'])], render_kw={'accept': 'text/plain'})


class ParamFieldsForm(FlaskForm):
    fields_form_model = RadioField(choices=[('ctgan', 'CTGAN'), ('tvae', 'TVAE'), ('wgan', 'WGAN'), ('all', 'ALL')],
                                   default='ctgan', validators=[InputRequired()])
    fields_form_dataset = FileField(validators=[FileRequired(), FileAllowed(['csv'])], render_kw={'accept': 'text/csv'})
    fields_form_samples = IntegerField('Samples', validators=[InputRequired()], widget=NumberInput(min=1, step=1))
    fields_form_epochs = IntegerField('Epochs', validators=[InputRequired()], widget=NumberInput(min=1, step=1))
    fields_form_names = StringField('Names')
    fields_form_categories = StringField('Categories')
    fields_form_correlees = StringField('Correlees')
    fields_form_drop = StringField('Drop')
    fields_form_unnamed = RadioField('Unnamed', choices=[('drop', 'Drop'), ('keep', 'Keep')],
                                     default='drop', validators=[InputRequired()])
    fields_form_compare = StringField('Compare', validators=[InputRequired()])
    fields_form_corresp = MultipleFileField(validators=[FileAllowed(['txt'])], render_kw={'accept': 'text/plain'})
