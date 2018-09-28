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
    # not invented here syndrome in its full glory
    # why use standard libs when you can just create your own for everything!!
    install_requires=["oslo.messaging==5.10.2", "oslo.config==3.17.1",
                      "oslo.middleware==3.19.1", "oslo.service==1.16.1",
                      "oslo.log==3.16.1", "oslo.concurrency==3.14.1",
                      "amqp==1.4.9", "kombu==3.0.35",
                      "pika==0.10.0", "pika-pool==0.1.3"],
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
