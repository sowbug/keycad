import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="keycad",
    version="0.0.1",
    author="Mike Tsao",
    author_email="https://github.com/sowbug",
    description="Generates KiCad PCBs for custom computer keyboards.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sowbug/keycad",
    packages=setuptools.find_packages(),
    package_data={
        "kle_layouts": ["*.json"],
    },
    entry_points = {
        'console_scripts': ['keycad=keycad.keycad:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "skidl >= 0.0.29", "kinjector >= 0.0.6", "kinet2pcb >= 0.1.0"
    ],
)
