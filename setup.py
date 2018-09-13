from setuptools import setup

setup(
    name="yarma",
    version="0.1.0",
    description="Yet Another Rabbit Monitoring Agent",
    author="Itxaka Serrano Garcia",
    author_email="igarcia@suse.com",
    url="https://github.com/Itxaka/yarma",
    license="GPL2.0",
    packages=["yarma"],
    entry_points={
        "console_scripts": [
            "yarma = yarma.yarma:main",
        ],
    },
    install_requires=[],
    tests_require=[],
    package_data={"": ["LICENSE", "README.md"]},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Environment :: Console"
    ],
)
