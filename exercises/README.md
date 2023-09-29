# Exercises

## Introduction

This folder contains exercises that illustrate various aspects related to the analysis of data that may be collected 
in hospitals' clinical data warehouses (CDW). Each exercise introduces specific data categories and notions. 
All exercises leverage a common archetypal use case that is described below. For each exercise synthetic data and 
an incomplete analysis notebook are made available. Completing properly the notebook to correct for various biases and 
pitfalls is required in order to reach a meaningful result.

## Problem statement

Let’s imagine that we are in the year 2025, three years after the outbreak of a deadly epidemic caused by the flu virus. 
This epidemic has affected equally both males and females of all ages. Two drugs have been approved since 2021 
by regulators in order to cure patients suffering from the flu. 
The regulators' approvals for these drugs were obtained after randomized controlled trials (RCT) had been conducted 
on a population aged between 18 and 65 years old composed mainly of males. 
The RCTs demonstrated a significant decrease of hospital mortality in the 3 weeks following admission caused 
by a flu infection. Following the approval, the drugs have been prescribed to a larger population that includes young 
(less than 18 years old) and old (more than 65 years old) patients of all social conditions, either males or females. 
Unfortunately, due to production shortage not all the eligible population has been treated.

In order to fulfill post-marketing surveillance of these two drugs, a study leveraging data collected routinely in hospitals 
(*i.e.*, real world data) has been ordered. The first objective of this study is to **confirm the benefit of the two drugs** (drug A and drug B). 
The second objective is to **assess whether one of the two drugs performs better on the populations that were not considered in the RCTs** 
(*i.e.*, females, children, elderly people).

## Randomized Controlled Trials vs Real-World Evidence

The highest level of evidence (*i.e.*, the strongest statistical proof) is usually achieved by leveraging data collected in Randomized Controlled Trials (RCT). RCTs indeed avoid common biases by randomization and ensure a high quality of data by manual collection. Unfortunately, data collection in RCTs is expensive and often limited to a small population which representativeness is imperfect due to patients' inclusion workflows. Analyzing directly data that has already been routinely collected in the clinical softwares of a hospital for care (not for research) therefore appears interesting to limit the cost of data collection and to ensure the population's representativeness. This data is often referred to as **real world data** (RWD) (US [Food and Drug Administration](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence) defines it as *the data relating to patient health status and/or the delivery of health care routinely collected from a variety of sources*).

|   |  Randomized controlled trials |  Observational studies on real world data |  
|---|---|---|
| Population size  |  - | +  |
| Population representativity  | -  | +  |
| Data quality  | +  |  - |
| Cost of data collection |  - | +  |
| Biases during data collection | + | - |
| Cost of data processing | +  | -  |


## Leverage EHR data

Although analyzing RWD appears promising, it requires to overcome important challenges. Data collected in a hospital's **Electronic Health Records** (EHR) is often of lower quality than data collected during a RCT. In particular, a heterogeneous usage or configuration of clinical softwares may lead to spurious or missing data. Managing patients' administrative identities in a clinical information system is for instance a longstanding challenge, as spelling mistakes when entering a patient's name may lead to the duplication of EHRs for a given patient. Other administrative reasons that are not directly related to a patient's medical condition may also affect data quality (*e.g.*, spurious administrative ending of a hospitalization stay followed by the beginning of a new one at the end of a financial year). All these pitfalls are due to the fact that data has been primarily collected for a purpose that is not research, and an important preprocessing appears therefore necessary to make data suitable for research.


## Study design

We assume that patients admitted at the hospital for flu infection can be classified in three exclusive cohorts 
(a patient is in one and only one of the three cohorts):
- **cohort A:** patients that received drug A
- **cohort B:** patients that received drug B
- **control cohort:** patients that did not receive any drug 

For the sake of simplicity, we moreover assume that patients were assigned randomly by clinicians to either cohort A, 
cohort B or control cohort (this random allocation was justified by the drug production shortage. 
This assumption would probably not be realistic if real use cases were considered).

We also assume that a patient who leaves hospital alive survives at least 20 days after the start of his hospitalization,
meaning that exiting a hospital does not mean that no death information are available anymore (and that actually it is for 20 days).

**Primary objective**: In order to measure the effects of the two drugs we plot Kaplan-Meier-estimated survival curves 
related to the three cohorts. We compare cohort A and cohort B with the control cohort using log-rank tests.

**Secondary objective**: In order to measure the effects of the two drugs on specific sub-populations, 
we realize the same analysis (*i.e.*, plot the Kaplan-Meier curves and realize log-rank tests) after having stratified 
the population along age (5-17, 18-24, 25-64, 65- year-old) and sex (male, female). 


## List of exercises

The following exercises present some categories of data that can be found in a clinical data warehouse, 
along with the methods and tools that can be leveraged to analyze them.

- **Exercise 1: A first illustration of real world data's analysis**
  - Data categories: patients' identities, demographic data, administrative data, claim data, structured medication data
  - Tools/methods: data exploration, detection of flawed data, pre-processing of administrative data
- **Exercise 2: An isolated data is no worth**
  - Data categories: linkage keys
  - Tools/methods: deterministic and probabilistic linkage algorithms
- **Exercise 3: The complex temporality of real world data**
  - Data categories: data quality indicators
  - Tools/methods: correction of data timeliness and of the software deployment bias
- **Exercise 4: Clinical notes and natural language processing**
  - Data categories: clinical notes
  - Tools/methods: notes pre-processing, natural language processing algorithms (rule-based)
- **Exercise 5: Biostatistics**
  - Data categories: demographic data, claim data (diseases and comorbidities), medication and biological data
  - Tools/methods: groups comparison and linear regressions (univariate and bivariate)
- **Exercise 6: The importance of a priori knowledge**
  - Data categories: a priori knowledge (originating from clinical and IT experts)
  - Tools/methods: manual correction of biases


## Data Available

The data made available for these exercises follow the scheme presented in the course introduction.
Here's a short description of each table :  

### II.1 Patients' identities and demographic data

Patients identities and their demographic features (gender, dates of birth, etc.) are stored in a single table *df_person*. Ideally each patient that has been treated in a hospital has a single identity related to them in the clinical information system, and this identity should be shared across all hospitals. 
The *df_person* table contains:
- **person_id** : a unique identifier for each identity
- **birth_datetime**: date of birth
- **death_datetime**: date of death if the patient died during a hospitalization stay
- **gender_source_value**: gender as mentioned in the clinical software
- **cdm_source**: name of the clinical software

We assume that a de-duplication algorithm designed for research has moreover been applied to all the identities that are registered in the clinical data warehouse to automatically detect duplicates. Its results are made available as a *df_dedup* dataframe that contains the following columns:
- **unique_person_id** : identifier of the unique identities obtained after de-duplication
- **person_id** : identifier of a record before de-duplication that corresponds to the same patient as the unique_person_identifier 


### II.2 Administrative data related to patients' pathways

Administrative data are collected during a patient's hospitalization stay for many purposes among which the management of the hospital. Indeed, hospital managers are required to follow the exact location of patients (care unit name and location), along with the entrance and exit datetime of such units. The administrative description of a patient's pathway in a hospital may be used for research as it describes the temporality of a disease evolution and treatment. Many levels of description may be considered (hospitals, buildings, rooms, medical units, etc.), but we focus in this project on the simplest one: visits in hospitals.

This administrative data is made available as a *df_visit* dataframe that contains the following columns:
- **visit_occurrence_id** : identifier of a visit
- **care_site_id** : identifier of a care site
- **visit_start_datetime** : date of the beginning of the visit
- **visit_end_datetime** : date of the end of the visit
- **person_id** : identifier of the patient
- **visit_source_value** : type of visit (only hospitalization stays in this project)


### II.3 Claim data related to patients' condition (diagnosis)

Claim data is collected for hospitals reimbursement purposes. Specific information systems have been developed and deployed to collect and send data to the relevant reimbursement agencies (*e.g.* in France the *Programme de Médicalisation du Système d'Information, PMSI*). 

Claim data should : 
- Describe the medical conditions of patients that have been admitted to a given hospital.
- Indicate treatments and procedures provided in such hospital. 

Patients' medical conditions are often described using the International Classification of Diseases (ICD, or *Classification Internationale des Maladies - CIM* in French). To be easily processed by reimbursement agencies, claim data is structured (*i.e.*, it is collected as tabular data not as free text, images or signals).

In this exercise, we consider the *df_condition* dataframe with data imported from the claim information system. The dataframe contains the following columns:
- **visit_occurrence_id** : identifier of the visit
- **person_id** : identifier of the patient
- **condition_occurrence_id** : identifier of the condition
- **condition_source_value** : value of the condition


In this exercise, we assume that an infection by the flu virus is coded as a condition with one of the following codes:
- J09
- J10
- J11


### II.4 Structured medication data

Hospitals keep track of the drugs that are administered during hospitalization stays of their patients. Such information is often collected in a dedicated software, and is available for research as structured data. Yet, the administration of some drugs is not available in these softwares (*e.g.*, drugs that have been administered out of the hospital before patient's entrance). Nevertheless for the sake of simplicity in this first exercise we make the strong assumption that information on the administration of drug A and drug B is fully available as structured data. Data is available in a *df_med* dataframe containing the following columns:
- **visit_occurrence_id** : identifier of the visit
- **drug_exposure_id** : identifier of the drug exposure
- **drug_source_value** : name of the drug
- **cdm_source** : name of the clinical software


### II.5 Clinical notes

Health professionals generate texts for each and every visit in hospital, and a lot of unstructured clinical reports are available in CDWs. They contain critical information about a patient's status, medical history, diagnoses and treatments suggested, etc. Therefore the processing of such texts with natural language processing (NLP) techniques is of paramount importance to populate structured tables delivered to researchers and analysts to enhance information available in tabular data. To that end, a *df_note* table is available with the following columns:

- **visit_occurrence_id**: identifier of the visit during which the note was written
- **note_id**: identifier of the clinical note
- **note_datetime**: date of note validation
- **cdm_source**: identifier of the EHR software
- **note_text**: raw text of the clinical note


### II.5 Biological data

Many biological analyses are performed when being at hospital, and are integrated from various softwares that differ between hospitals and sometimes between care units of a given hospital. Hence their processing represents a great challenge regarding integration and standardization, and a pre-processed table called `df_bio` is made available, containing the following columns:
- **measurement_id**: identifier of the lab analysis
- **visit_occurrence_id**: identifier of the visit during which the analysis was performed
- **measurement_datetime**: date of the analysis
- **concept_source_value**: name of the analysis (following specific ontologies)
- **transformed_value**: pre-processed value measured
- **transformed_unit**: unit associated

## Coding tips

The following common python packages may help you complete the exercises:
- [pandas](https://pandas.pydata.org/pandas-docs/stable/) : data processing
- [numpy](https://numpy.org/doc/stable/index.html) : array processing
- [lifelines](https://lifelines.readthedocs.io/en/latest/) : survival analyses
- [altair](https://altair-viz.github.io/) : data viz
- [spacy](https://spacy.io/) : NLP
- [scipy](https://docs.scipy.org/doc/scipy/index.html) : statistical tests
- [statsmodels](https://www.statsmodels.org/devel/index.html) : statistical models