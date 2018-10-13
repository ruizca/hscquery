import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='hscquery',
    version='0.1',
    author='Angel Ruiz',
    author_email='angel.ruizca@gmail.com',
    description='Module for accesing the HSC-SSP database',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pypa/sampleproject',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Database :: Front-Ends',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
)
