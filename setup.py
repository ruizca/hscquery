from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='hscquery',
    version='0.1',
    author='Angel Ruiz',
    author_email='angel.ruizca@gmail.com',
    description='Module for accesing the HSC-SSP database',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ruizca/hscquery',
    install_requires=['astropy'],
    py_modules=['hscquery'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Database :: Front-Ends',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
    ],
)
