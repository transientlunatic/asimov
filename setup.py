from setuptools import setup

# with open('README.rst') as readme_file:
#     readme = readme_file.read()

# with open('HISTORY.rst') as history_file:
#     history = history_file.read()

with open("requirements.txt") as requires_file:
    requirements = requires_file.read().split("\n")

requirements = [requirement for requirement in requirements if not ("+" in requirement)]
    
test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='ligo-asimov',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="""A Python package for managing and interacting with data analysis jobs.""",
    #long_description=readme + '\n\n' + history,
    author="Daniel Williams",
    author_email='daniel.williams@ligo.org',
    url='https://github.com/transientlunatic/supervisor',
    packages=['asimov'],
    package_dir={'asimov': 'asimov'},
    entry_points={
        'console_scripts': [
            'olivaw=asimov.olivaw:olivaw',
            'locutus=asimov.locutus:cli'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=True,
    keywords='supervisor, pe, ligo, asimov',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
