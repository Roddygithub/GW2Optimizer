from setuptools import setup, find_packages

setup(
    name="gw2optimizer",
    version="1.0.0",
    description="GW2 WvW Team Optimizer with AI",
    author="Roddy",
    author_email="",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if not line.startswith("#") and line.strip()
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
