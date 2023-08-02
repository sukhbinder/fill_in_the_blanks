from setuptools import find_packages, setup

setup(
    name="blanks",
    version="1.0",
    packages=find_packages(),
    license="Private",
    description="Study Revision with Spaced Repetetion for Kids on Mac",
    author="sukhbinder",
    author_email="sukh2010@yahoo.com",
    entry_points={
        'console_scripts': ['fillin = fill_in.app:main',
                            'review =  fill_in.cliapp:main',
                            ]
    },

    install_requires=["pandas","colorama",
    "pywin32 >= 1.0;platform_system=='Windows'"],
)
