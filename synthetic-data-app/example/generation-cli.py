import csv
import os
import warnings

import pandas as pd
import seaborn as sns
import torch
from ctgan import CTGANSynthesizer
from dpwgan import CategoricalDataset
from dpwgan.utils import create_categorical_gan
from dython.nominal import associations, numerical_encoding
from faker import Faker
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sdv.tabular import TVAE
from sklearn.decomposition import PCA
from sklearn.exceptions import ConvergenceWarning
from table_evaluator import TableEvaluator
from table_evaluator.viz import cdf, plot_mean_std
from tqdm import tqdm

warnings.simplefilter("ignore", category=DeprecationWarning)
warnings.simplefilter("ignore", category=FutureWarning)
warnings.simplefilter("ignore", category=ConvergenceWarning)
warnings.simplefilter("ignore", category=UserWarning)
warnings.simplefilter("ignore", category=RuntimeWarning)


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


def save_figure(fig: plt.Figure, summary: PdfPages):
    plt.figure(fig)
    plt.savefig(summary, format='pdf')
    plt.close()


def figure_axes(real: pd.DataFrame, nr_cols, title):
    nr_charts = len(real.columns)
    nr_rows = max(1, nr_charts // nr_cols)
    nr_rows = nr_rows + 1 if nr_charts % nr_cols != 0 else nr_rows

    max_len = 0
    # Increase the length of plots if the labels are long
    if not real.select_dtypes(include=['object']).empty:
        lengths = []
        for d in real.select_dtypes(include=['object']):
            lengths.append(max([len(x.strip()) for x in real[d].unique().tolist()]))
        max_len = max(lengths)

    row_height = 6 + (max_len // 30)
    fig, ax = plt.subplots(nr_rows, nr_cols, figsize=(16, row_height * nr_rows))
    fig.suptitle(title, fontsize=16)
    axes = ax.flatten()
    return fig, axes


def fig_mean_std(summary: PdfPages, real: pd.DataFrame, fake: pd.DataFrame):
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle('Absolute Log Mean and STDs of numeric data\n', fontsize=16)
    plot_mean_std(real, fake, ax=ax)
    save_figure(fig, summary)


def fig_cumsums(summary: PdfPages, real: pd.DataFrame, fake: pd.DataFrame, nr_cols=4):
    title = 'Cumulative Sums per feature'
    fig, axes = figure_axes(real, nr_cols, title)
    for i, col in enumerate(real.columns):
        r = real[col]
        f = fake.iloc[:, real.columns.tolist().index(col)]
        cdf(r, f, col, 'Cumsum', ax=axes[i])
    plt.tight_layout(rect=(0, 0.02, 1, 0.98))  # noqa
    save_figure(fig, summary)


def fig_distributions(summary: PdfPages, real: pd.DataFrame, fake: pd.DataFrame, categorical_columns, nr_cols=3):
    title = 'Distribution per feature'
    fig, axes = figure_axes(real, nr_cols, title)
    for i, col in enumerate(real.columns):
        if col not in categorical_columns:
            try:
                sns.histplot(real[col], ax=axes[i], label='Real', kde=True)
                sns.histplot(fake[col], ax=axes[i], color='darkorange', label='Fake', kde=True)
            except RuntimeError:
                axes[i].clear()
                sns.histplot(real[col], ax=axes[i], label='Real', kde=False)
                sns.histplot(fake[col], ax=axes[i], color='darkorange', label='Fake', kde=False)
            axes[i].set_autoscaley_on(True)
            axes[i].legend()
        else:
            real = real.copy()
            fake = fake.copy()
            real['kind'] = 'Real'
            fake['kind'] = 'Fake'
            concat = pd.concat([fake, real])
            palette = sns.color_palette(
                [(0.8666666666666667, 0.5176470588235295, 0.3215686274509804),
                 (0.2980392156862745, 0.4470588235294118, 0.6901960784313725)])
            x, y, hue = col, "proportion", "kind"
            ax = (concat[x]
                  .groupby(concat[hue])
                  .value_counts(normalize=True)
                  .rename(y)
                  .reset_index()
                  .pipe((sns.barplot, "data"), x=x, y=y, hue=hue, ax=axes[i], saturation=0.8, palette=palette))
            ax.set_xticklabels(axes[i].get_xticklabels(), rotation='vertical')
    plt.tight_layout(rect=(0, 0.02, 1, 0.98))  # noqa
    save_figure(fig, summary)


def fig_correlation_difference(summary: PdfPages, real: pd.DataFrame, fake: pd.DataFrame, plot_diff, cat_cols, annot):
    assert isinstance(real, pd.DataFrame), f'`real` parameters must be a Pandas DataFrame'
    assert isinstance(fake, pd.DataFrame), f'`fake` parameters must be a Pandas DataFrame'
    cmap = sns.diverging_palette(220, 10, as_cmap=True)  # noqa

    if cat_cols is None:
        cat_cols = real.select_dtypes(['object', 'category'])
    if plot_diff:
        fig, ax = plt.subplots(1, 3, figsize=(24, 7))
    else:
        fig, ax = plt.subplots(1, 2, figsize=(20, 8))

    real_corr = associations(real, nominal_columns=cat_cols, plot=False, theil_u=True,
                             mark_columns=True, annot=annot, ax=ax[0], cmap=cmap)['corr']
    fake_corr = associations(fake, nominal_columns=cat_cols, plot=False, theil_u=True,
                             mark_columns=True, annot=annot, ax=ax[1], cmap=cmap)['corr']

    if plot_diff:
        diff = abs(real_corr - fake_corr)
        sns.set(style="white")
        sns.heatmap(diff, ax=ax[2], cmap=cmap, vmax=.3, square=True, annot=annot, center=0,
                    linewidths=.5, cbar_kws={"shrink": .5}, fmt='.2f')

    titles = ['Real', 'Fake', 'Difference'] if plot_diff else ['Real', 'Fake']
    for i, label in enumerate(titles):
        title_font = {'size': '18'}
        ax[i].set_title(label, **title_font)
    plt.tight_layout()
    save_figure(fig, summary)


def fig_pca(summary: PdfPages, real: pd.DataFrame, fake: pd.DataFrame, categorical_columns):
    real = numerical_encoding(real, nominal_columns=categorical_columns)
    fake = numerical_encoding(fake, nominal_columns=categorical_columns)
    pca_r = PCA(n_components=2)
    pca_f = PCA(n_components=2)

    real_t = pca_r.fit_transform(real)
    fake_t = pca_f.fit_transform(fake)

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('First two components of PCA', fontsize=16)
    sns.scatterplot(ax=ax[0], x=real_t[:, 0], y=real_t[:, 1])
    sns.scatterplot(ax=ax[1], x=fake_t[:, 0], y=fake_t[:, 1])
    ax[0].set_title('Real data')
    ax[1].set_title('Fake data')
    save_figure(fig, summary)


def figure_evaluation(table_evaluator, summary: PdfPages):
    real = table_evaluator.real
    fake = table_evaluator.fake
    cat_cols = table_evaluator.categorical_columns

    fig_mean_std(summary, real, fake)
    fig_cumsums(summary, real, fake)
    fig_distributions(summary, real, fake, cat_cols)
    fig_correlation_difference(summary, real, fake, True, cat_cols, False)
    fig_pca(summary, real, fake, cat_cols)


def ctgan_generation(dataframe, categories, nb_epochs, nb_samples):
    ctgan = CTGANSynthesizer(verbose=True, epochs=nb_epochs)
    ctgan.fit(dataframe, categories)

    samples = ctgan.sample(nb_samples)

    return samples


def tvae_generation(dataframe, nb_samples):
    tvae = TVAE()
    tqdm(tvae.fit(dataframe))

    samples = tvae.sample(nb_samples)

    return samples


def wgan_generation(dataframe, nb_epochs, nb_samples):
    torch.manual_seed(123)

    noise_dim = 10
    hidden_dim = 20
    sigma = 1

    categorical_dataset = CategoricalDataset(dataframe)
    data_tensor = categorical_dataset.to_onehot_flat()

    dpwgan = create_categorical_gan(noise_dim, hidden_dim, categorical_dataset.dimensions)
    dpwgan.train(data=data_tensor,
                 epochs=nb_epochs,
                 n_critics=5,
                 batch_size=128,
                 learning_rate=1e-3,
                 weight_clip=1 / hidden_dim,
                 sigma=sigma)
    flat_synth_data = dpwgan.generate(nb_samples)
    samples = categorical_dataset.from_onehot_flat(flat_synth_data)

    return samples


# main method
def synthetic_generation(model, dataset, param_file, corresp_files, result_dir):
    # get a pandas dataframe from dataset file
    initial_df = get_dataframe_from_csv(dataset)
    df = initial_df.copy()

    # get parameters from parameters file
    reader = csv.reader(open(param_file, "r"), delimiter=',')
    data = list(reader)

    nb_samples = int(get_data_from_param_file('samples', data, unique=True))
    nb_epochs = int(get_data_from_param_file('epochs', data, unique=True))
    names = get_data_from_param_file('names', data)
    categories = get_data_from_param_file('categories', data)
    correlees = get_data_from_param_file('correlees', data)
    to_drop = get_data_from_param_file('drop', data)
    unnamed = get_data_from_param_file('unnamed', data, unique=True)
    to_compare = get_data_from_param_file('compare', data)

    # adjust dataframe to fit synthetic generation
    if names != ['']:
        df.drop(names, axis=1, inplace=True)
    if correlees != ['']:
        df.drop(correlees, axis=1, inplace=True)
    if to_drop != ['']:
        df.drop(to_drop, axis=1, inplace=True)

    if unnamed.lower() == 'drop':
        df = df.loc[:, ~df.columns.str.match('Unnamed')]

    samples = []
    samples_files = []
    summary_files = []

    if model == 'ctgan' or model == 'all':
        print('*** CTGAN generation ***')
        samples.append(ctgan_generation(df, categories, nb_epochs, nb_samples))
        samples_files.append(os.path.join(result_dir, 'ctgan-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'ctgan-summary.pdf'))
    if model == 'tvae' or model == 'all':
        print('*** TVAE generation ***')
        samples.append(tvae_generation(df, nb_samples))
        samples_files.append(os.path.join(result_dir, 'tvae-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'tvae-summary.pdf'))
    if model == 'wgan' or model == 'all':
        print('*** WGAN generation ***')
        samples.append(wgan_generation(df, nb_epochs, nb_samples))
        samples_files.append(os.path.join(result_dir, 'wgan-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'wgan-summary.pdf'))

    for (sample, sample_file, summary_file) in zip(samples, samples_files, summary_files):
        if 'ctgan' in sample_file:
            current_model = 'CTGAN'
        elif 'tvae' in sample_file:
            current_model = 'TVAE'
        else:
            current_model = 'WGAN'

        # evaluate sample compared to original prepared dataframe
        summary = PdfPages(summary_file)
        table_evaluator = TableEvaluator(df, sample, cat_cols=categories)
        figure_evaluation(table_evaluator, summary)

        # insert fake names with Faker library
        if names != ['']:
            sample.insert(1, names[0], 0)
            faker = Faker()
            print('*** Faker for {} sample ***'.format(current_model))
            for n in tqdm(range(nb_samples)):
                sample.loc[sample.index[n], names[0]] = faker.last_name()

        # insert correlated data
        for corresp_file in corresp_files:
            reader = csv.reader(open(corresp_file, "r"), delimiter=',')
            data = list(reader)
            ref = []
            values = []
            for d in data:
                ref.append(d[0])
                values.append(d[1:])

            sample.insert(3, ref[0], 0)
            print('*** Correspondence for {} sample ***'.format(current_model))
            for n in tqdm(range(nb_samples)):
                for p in range(1, len(values)):
                    if sample[values[0][0]][n] in values[p]:
                        sample.loc[sample.index[n], ref[0]] = ref[p]

        sample.to_csv(sample_file, index=False)

        # get number of rows that have identical values in columns to compare
        df_to_compare = initial_df[to_compare]
        sample_to_compare = sample[to_compare]
        comparison = df_to_compare.merge(sample_to_compare, how='outer', indicator=True)
        identical = comparison[comparison['_merge'] == 'both']

        similarity = identical.shape[0] / (df.shape[0] * nb_samples)
        similarity_fig = plt.figure(figsize=(15, 4))
        similarity_title = '\nModel used : {}\n\nSimilarity with the original dataset depending on :\n{} ' \
                           '\n\n= {}%'.format(current_model, ', '.join(to_compare), similarity)
        similarity_fig.suptitle(similarity_title, fontsize=32)
        save_figure(similarity_fig, summary)
        summary.close()


# script for cli
input_model = input('Enter a model (ctgan, tvae, wgan or all) : ').lower()
input_dataset = input('Enter a path to a dataset (e.g. /home/path/to/my_dataset.csv) : ')
input_param_file = input('Enter a path to a parameters file (e.g. /home/path/to/my_parameters_file.txt) : ')
is_corresp = True
input_is_corresp = 'Q'
while input_is_corresp.lower() != 'y' and input_is_corresp.lower() != 'n':
    input_is_corresp = input('Do you have a correspondence file ? [Y/n] : ')
if input_is_corresp.lower() == 'n':
    is_corresp = False
input_corresp_files = []
while is_corresp:
    input_corresp = input('Enter a path to a correspondence file (e.g. /home/path/to/my_correspondence_file.txt) : ')
    input_corresp_files.append(input_corresp)
    input_is_corresp = 'Q'
    while input_is_corresp.lower() != 'y' and input_is_corresp.lower() != 'n':
        input_is_corresp = input('Do you have an other correspondence file ? [Y/n] : ')
    if input_is_corresp.lower() == 'n':
        is_corresp = False

current_dir = os.path.dirname(os.path.realpath(__file__))
synthetic_generation(input_model, input_dataset, input_param_file, input_corresp_files, current_dir)
print('*** Generation done ***')
