# To generate a new secret key : python
# >>> import random, string
# >>> "".join([random.choice(string.printable) for _ in range(24)])
import os
import warnings

from sklearn.exceptions import ConvergenceWarning

warnings.simplefilter("ignore", category=DeprecationWarning)
warnings.simplefilter("ignore", category=FutureWarning)
warnings.simplefilter("ignore", category=ConvergenceWarning)
warnings.simplefilter("ignore", category=UserWarning)
warnings.simplefilter("ignore", category=RuntimeWarning)

if os.environ.get('SECRET_KEY') is None:
    SECRET_KEY = 'AI\x0bn&#Tg|LS\x0bpJq)0J*5\x0bu!P'
else:
    SECRET_KEY = os.environ.get('SECRET_KEY')

if os.environ.get('WTF_CSRF_SECRET_KEY') is None:
    WTF_CSRF_SECRET_KEY = 'jZa|dwE)rCW!rqVXQ1I%S0Cu'
else:
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY')

RESOURCES = 'resources'

RESULTS = 'results'

SYNTHETIC_DATA = 'synthetic_data.zip'

SUMMARY_PDF = 'summary.pdf'
