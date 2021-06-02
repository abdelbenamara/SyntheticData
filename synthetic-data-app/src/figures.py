import pandas as pd
import seaborn as sns

from dython.nominal import associations, numerical_encoding
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from table_evaluator.viz import cdf, plot_mean_std


def figure_mean_std(real: pd.DataFrame, fake: pd.DataFrame):
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle('Absolute Log Mean and STDs of numeric data\n', fontsize=16)
    plot_mean_std(real, fake, ax=ax)


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
    return axes


def figure_cumsums(real: pd.DataFrame, fake: pd.DataFrame, nr_cols=4):
    title = 'Cumulative Sums per feature'
    axes = figure_axes(real, nr_cols, title)
    for i, col in enumerate(real.columns):
        r = real[col]
        f = fake.iloc[:, real.columns.tolist().index(col)]
        cdf(r, f, col, 'Cumsum', ax=axes[i])
    plt.tight_layout(rect=(0, 0.02, 1, 0.98))  # noqa


def figure_distributions(real: pd.DataFrame, fake: pd.DataFrame, categorical_columns, nr_cols=3):
    title = 'Distribution per feature'
    axes = figure_axes(real, nr_cols, title)
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


def figure_correlation_difference(real: pd.DataFrame, fake: pd.DataFrame, plot_diff, cat_cols, annot):
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


def figure_pca(real: pd.DataFrame, fake: pd.DataFrame, categorical_columns):
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


def figure_evaluation(table_evaluator):
    real = table_evaluator.real
    fake = table_evaluator.fake
    cat_cols = table_evaluator.categorical_columns

    figure_mean_std(real, fake)
    figure_cumsums(real, fake)
    figure_distributions(real, fake, cat_cols)
    figure_correlation_difference(real, fake, True, cat_cols, False)
    figure_pca(real, fake, cat_cols)
