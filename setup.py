from setuptools import setup, find_packages

setup(name='logparser',
      version='0.1.0',
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'logparser=logparser.logparser:main',
          ],
      },
      install_requires=[
          'argparse',
          'boto3',
          'botocore',
          'futures'
      ],
      packages=find_packages(),)
