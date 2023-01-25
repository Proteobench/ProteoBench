from setuptools import find_packages, setup

setup(
    name='proteobench',
    version='0.1',
    license='apache-2.0',
    description='proteobench',
    author_email='Robbin.Bouwmeester@UGent.be',
    packages=find_packages(),
    include_package_data=True,
    keywords=[
        'Proteomics', 'peptides', 'retention time', 'mass spectrometry'
    ],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Development Status :: 4 - Beta"
    ],
    python_requires='>=3.6',
)