import csv
import os

import pandas as pd
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

from .figures import figure_evaluation


def synthetic_generation(model, dataset, param_file, corresp_files, result_dir):
    initial_df = pd.read_csv(dataset)
    if len(initial_df.columns.values.tolist()) == 1:
        initial_df = pd.read_csv(dataset, delimiter=';')
    df = initial_df.copy()
    reader = csv.reader(open(param_file, "r"), delimiter=',')
    data = list(reader)

    nb_samples = int(data[0][1])
    nb_epochs = int(data[1][1])
    names = data[2][1:]
    categories = data[3][1:]
    correlees = data[4][1:]
    to_drop = data[5][1:]
    unnamed = data[6][1]
    to_compare = data[7][1:]

    df.drop(names, axis=1, inplace=True)
    df.drop(correlees, axis=1, inplace=True)
    df.drop(to_drop, axis=1, inplace=True)

    if unnamed.lower() != 'keep':
        df = df.loc[:, ~df.columns.str.match('Unnamed')]

    samples = []
    samples_files = []
    summary_files = []
    if model not in ['ctgan', 'tvae', 'wgan', 'all']:
        raise ModelError(model, 'There is no gan method defined for this model.')
    if model == 'ctgan' or model == 'all':
        samples.append(ctgan_generation(df, categories, nb_epochs, nb_samples))
        samples_files.append(os.path.join(result_dir, 'ctgan-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'ctgan-summary.pdf'))
    if model == 'tvae' or model == 'all':
        samples.append(tvae_generation(df, nb_samples))
        samples_files.append(os.path.join(result_dir, 'tvae-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'tvae-summary.pdf'))
    if model == 'wgan' or model == 'all':
        samples.append(wgan_generation(df, nb_epochs, nb_samples))
        samples_files.append(os.path.join(result_dir, 'wgan-samples.csv'))
        summary_files.append(os.path.join(result_dir, 'wgan-summary.pdf'))

    for (sample, sample_file, summary_file) in zip(samples, samples_files, summary_files):
        table_evaluator = TableEvaluator(df, sample, cat_cols=categories)
        figure_evaluation(table_evaluator)

        summary = PdfPages(summary_file)
        for f in plt.get_fignums():
            plt.figure(f)
            plt.savefig(summary, format='pdf')
            plt.close()

        sample.insert(1, names[0], 0)
        faker = Faker()
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
        fig = plt.figure(figsize=(15, 3))
        similarity_title = '\nSimilarity with the original dataset depending on\n{} ' \
                           '\n\n= {}%'.format(', '.join(to_compare), similarity)
        fig.suptitle(similarity_title, fontsize=32)
        plt.savefig(summary, format='pdf')
        plt.close()
        summary.close()


def ctgan_generation(dataframe, category, nb_epochs, nb_samples):
    ctgan = CTGANSynthesizer(verbose=True, epochs=nb_epochs)
    ctgan.fit(dataframe, category)

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


class ModelError(NameError):
    """Exception raised for unknown gan model.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
