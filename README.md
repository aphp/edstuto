<div align="center">
<p align="center">
  <a><img src="logo_tuto.svg" alt="EDS-TeVa"></a>
</p>

# EDS-Tuto
</div>

## About

In this tutorial we introduce some issues related to the analysis of real world data that are made available for research in **clinical data warehouses**. It is targeted towards data scientists that master the basics of Python programming and data analysis. The tutorial is decomposed in a series of small exercises and a final project. Whereas small exercises illustrate specific issues, the final project mimics an end-to-end research study that may be reported in a scientific article.

Data is fake, and this project can consequently be freely shared without impacting patients’ privacy. A fake data generator is made available and can be tuned to illustrate various use cases. Its development has been freely inspired by the characteristics and issues observed while analyzing data of the Greater Paris University Hospitals.

The 2022 session for CentraleSupelec worked on the 0.0.1 version.

## Getting started

### Environment and kernel creation

Python, JupyterLab and an environment manager are recommended. You may choose for instance [Anaconda](https://docs.anaconda.com/anaconda/install/index.html).

First clone the project locally :
`git clone https://github.com/aphp/edstuto.git`

If you use Conda as an environment manager, create a new Python environment with the required packages:
1. `conda create -n eds-tuto python=3.7`
2. `conda activate eds-tuto`
3. `pip install -r requirements.txt`

Create and name a Jupyter kernel related to this virtual environment:
4. `python -m ipykernel install --user --name eds_tutorial`
A kernel named eds_tuto is now available in your jupyterlab!

Start JupyterLab using:
5. `jupyter lab`
JupyterLab will open automatically in your browser.

NB: For VS Code users, in order to see clearly the plots, it is recommended to enable the Theme Matplotlib Plots in your setting > Extensions > Jupyter.

### Scientific libraries installation

The following scientific libraries developed in the context of Paris’ clinical data warehouse may moreover be leveraged to facilitate the resolution of some exercises:
- [eds-scikit](https://pypi.org/project/eds-scikit/): a set of tools to assist data scientists working on a clinical data warehouse (structured data).
- [edsnlp](https://pypi.org/project/edsnlp/): a set of spaCy components that are used to extract information from clinical notes written in French (unstructured data).
- [edsteva](https://pypi.org/project/edsteva/): a set of tools to measure indicators describing data quality and its temporal variation (quality indicators).

## Acknowledgement

We would like to thank [Assistance Publique – Hôpitaux de Paris](https://www.aphp.fr/)
and [AP-HP Foundation](https://fondationrechercheaphp.fr/) for funding this project.
