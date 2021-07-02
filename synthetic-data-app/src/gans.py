import csv
import os

import torch
from ctgan import CTGANSynthesizer
from dpwgan import CategoricalDataset
from dpwgan.utils import create_categorical_gan
from faker import Faker
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sdv.tabular import TVAE
from table_evaluator import TableEvaluator
from tqdm import tqdm

from .figures import figure_evaluation, save_figure
from .utils import get_dataframe_from_csv, get_data_from_param_file


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


def synthetic_generation(model, dataset, param_file, corresp_files, result_dir, app):
    initial_df = get_dataframe_from_csv(dataset)
    df = initial_df.copy()

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
        app.logger.info('*** CTGAN generation ***')
        samples.append(ctgan_generation(df, categories, nb_epochs, nb_samples))
        samples_files.append(os.path.join(result_dir, 'ctgan-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'ctgan-summary.pdf'))
    if model == 'tvae' or model == 'all':
        app.logger.info('*** TVAE generation ***')
        samples.append(tvae_generation(df, nb_samples))
        samples_files.append(os.path.join(result_dir, 'tvae-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'tvae-summary.pdf'))
    if model == 'wgan' or model == 'all':
        app.logger.info('*** WGAN generation ***')
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

        summary = PdfPages(summary_file)
        table_evaluator = TableEvaluator(df, sample, cat_cols=categories)
        figure_evaluation(table_evaluator, summary)

        if names != ['']:
            sample.insert(1, names[0], 0)
            faker = Faker()
            app.logger.info('*** Faker for {} sample ***'.format(current_model))
            for n in tqdm(range(nb_samples)):
                sample.loc[sample.index[n], names[0]] = faker.last_name()

        for corresp_file in corresp_files:
            reader = csv.reader(open(corresp_file, "r"), delimiter=',')
            data = list(reader)
            ref = []
            values = []
            for d in data:
                ref.append(d[0])
                values.append(d[1:])

            sample.insert(3, ref[0], 0)
            app.logger.info('*** Correspondence for {} sample ***'.format(current_model))
            for n in tqdm(range(nb_samples)):
                for p in range(1, len(values)):
                    if sample[values[0][0]][n] in values[p]:
                        sample.loc[sample.index[n], ref[0]] = ref[p]

        sample.to_csv(sample_file, index=False)

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


def synthetic_evaluation(real_dataset, param_file, synthetic_dataset, result_dir, app):
    initial_real_df = get_dataframe_from_csv(real_dataset)
    real_df = initial_real_df.copy()
    initial_synthetic_df = get_dataframe_from_csv(synthetic_dataset)
    synthetic_df = initial_synthetic_df.copy()

    reader = csv.reader(open(param_file, "r"), delimiter=',')
    data = list(reader)

    names = get_data_from_param_file('names', data)
    categories = get_data_from_param_file('categories', data)
    correlees = get_data_from_param_file('correlees', data)
    to_drop = get_data_from_param_file('drop', data)
    unnamed = get_data_from_param_file('unnamed', data, unique=True)
    to_compare = get_data_from_param_file('compare', data)

    if names != ['']:
        real_df.drop(names, axis=1, inplace=True)
        synthetic_df.drop(names, axis=1, inplace=True)
    if correlees != ['']:
        real_df.drop(correlees, axis=1, inplace=True)
        synthetic_df.drop(correlees, axis=1, inplace=True)
    if to_drop != ['']:
        real_df.drop(to_drop, axis=1, inplace=True)

    if unnamed.lower() == 'drop':
        real_df = real_df.loc[:, ~real_df.columns.str.match('Unnamed')]
        synthetic_df = synthetic_df.loc[:, ~synthetic_df.columns.str.match('Unnamed')]

    summary_file = os.path.join(result_dir, app.config['SUMMARY_PDF'])

    summary = PdfPages(summary_file)
    table_evaluator = TableEvaluator(real_df, synthetic_df, cat_cols=categories)
    figure_evaluation(table_evaluator, summary)

    df_to_compare = initial_real_df[to_compare]
    sample_to_compare = initial_synthetic_df[to_compare]
    comparison = df_to_compare.merge(sample_to_compare, how='outer', indicator=True)
    identical = comparison[comparison['_merge'] == 'both']

    similarity = identical.shape[0] / (real_df.shape[0] * synthetic_df.shape[0])
    similarity_fig = plt.figure(figsize=(15, 4))
    similarity_title = '\n\nSimilarity with the original dataset depending on :\n{} ' \
                       '\n\n= {}%'.format(', '.join(to_compare), similarity)
    similarity_fig.suptitle(similarity_title, fontsize=32)
    save_figure(similarity_fig, summary)
    summary.close()
