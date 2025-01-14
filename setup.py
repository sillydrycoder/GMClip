from setuptools import setup, find_packages

setup(
    name="block-editor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.6.0",
        "numpy>=1.26.0",
        "pydub==0.25.1",
        "opencv-python>=4.8.0",
    ],
    entry_points={
        'console_scripts': [
            'block-editor=block_editor.__main__:main',
        ],
    },
    author="Aj",
    description="A sophisticated video editing tool for segmenting and labeling video content",
    long_description=open("exponent.txt").read(),
    long_description_content_type="text/markdown",
    keywords="video editor, video segmentation, content creation",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Non-Linear Editor",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)