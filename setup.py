from setuptools import find_packages, setup


def get_lines(relative_path):
    with open(relative_path) as f:
        return f.readlines()


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eds-tutorial",
    version="0.0.1",
    author="Innovation and Data Unit, IT Department, AP-HP",
    description="Hands-on tutorial to analyze data of a clinical data warehouse.",
    python_requires=">=3.6",
    packages=find_packages(),
    # install_requires=get_lines("requirements.txt"),
)
