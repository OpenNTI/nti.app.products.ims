import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
    "z3c.autoinclude.plugin": [
        'target = nti.app.products',
    ],
}

setup(
    name='nti.app.products.ims',
    version=VERSION,
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI IMS Product Integration",
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    license='Proprietary',
    keywords='pyramid preference',
    classifiers=[
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['nti', 'nti.app', 'nti.app.products'],
    install_requires=[
        'setuptools',
        'nti.ims'
    ],
    entry_points=entry_points
)
