import itertools
import os
import yaml

from data_generator.pipelines import (
    gen_admin_tables,
    gen_condition_table,
    gen_med_table,
    gen_bio_table,
    uniform_drawing,
    gen_comorb_table,
    idGenerator,
)
import numpy as np
import pandas as pd
from ast import literal_eval
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

config = pd.read_csv(
    os.path.join(dir_path, "..", "config", "config_ex4.csv"),
    sep=";",
    converters={
        "age": literal_eval,
        "bmi": literal_eval,
        "crp": literal_eval,
        "urea": literal_eval,
        "hb": literal_eval,
    },
)


def bio_drawing(bio_concept, age_range, gender, case):
    mu, sigma = config.loc[
        (config.age == age_range) & (config.gender == gender) & (config.case == case)
    ][bio_concept].squeeze()

    def f(row):
        return round(np.random.normal(mu, sigma), 2)

    return f


def comorb_drawing(comorb_name, age_range, gender, case):
    pct = config.loc[
        (config.age == age_range) & (config.gender == gender) & (config.case == case)
    ][comorb_name].squeeze()

    return uniform_drawing(pct / 100)


dict_param = {
    "control": {"final_survival_ratio": 0.5, "death_saturation_day": 10},
    "drugA": {"final_survival_ratio": 0.55, "death_saturation_day": 15},
    "drugB": {"final_survival_ratio": 0.55, "death_saturation_day": 10},
}

list_age_range = [(0, 5), (5, 18), (18, 25), (25, 65), (65, 100)]
list_gender = [("f"), ("m")]
list_case = [("control"), ("drugB")]
list_diabetes_cim10 = ["E10", "E11", "E12"]
list_atcd_cancer_cim10 = ["Z851", "Z852", "Z853"]
np.random.seed(42)
# n_patient_per_cat = 50

id_generator = idGenerator()

df_person, df_visit, df_cond, df_med, df_bio = [], [], [], [], []
for age_range, gender, case in itertools.product(
    list_age_range, list_gender, list_case
):

    params = (
        config.loc[
            (config.age == age_range)
            & (config.gender == gender)
            & (config.case == case)
        ]
        .squeeze()
        .to_dict()
    )

    n_patient_per_cat = params["n_patient_per_cat"]

    df_person_tmp, df_visit_tmp = gen_admin_tables(
        n=n_patient_per_cat,
        id_generator=id_generator,
        age_range=age_range,
        gender_list=gender,
        final_survival_ratio=params["final_survival_ratio"],
        death_saturation_day=params["death_saturation_day"],
    )
    df_med_tmp, _, _ = gen_med_table(df_visit_tmp, df_person_tmp, case, id_generator)
    # ICD10 codes associated to the principal disease
    df_cim10_tmp = gen_condition_table(
        df_visit_tmp, id_generator, list_good_cim10=conf["list_flu_cim10"]
    )
    # ICD10 codes associated to comorbidities
    df_comorb_tmp = gen_comorb_table(
        df_visit_tmp,
        id_generator,
        df_person_tmp,
        df_med_tmp,
        list_comorb=[
            (
                list_atcd_cancer_cim10,
                1,
                comorb_drawing("cancer", age_range, gender, case),
            ),
            (
                list_diabetes_cim10,
                1,
                comorb_drawing("diabete", age_range, gender, case),
            ),
        ],
    )
    df_cim10_tmp = pd.concat([df_cim10_tmp, df_comorb_tmp], axis=0)

    # Add bio measures
    df_bio_tmp = gen_bio_table(
        df_visit_tmp,
        id_generator,
        df_person_tmp,
        df_med_tmp,
        list_measurement=[
            ("bmi", "kg.cm^-2", 1, bio_drawing("bmi", age_range, gender, case)),
            ("crp", "mg/L", 1, bio_drawing("crp", age_range, gender, case)),
            ("urea", "mmol/L", 1, bio_drawing("urea", age_range, gender, case)),
            ("hb", "g/dL", 1, bio_drawing("hb", age_range, gender, case)),
        ],
    )

    df_person.append(df_person_tmp)
    df_visit.append(df_visit_tmp)
    df_cond.append(df_cim10_tmp)
    df_med.append(df_med_tmp)
    df_bio.append(df_bio_tmp)

pd.concat(df_cond, axis=0).to_pickle("exercises/exercise5/data/df_condition.pkl")
pd.concat(df_med, axis=0).to_pickle("exercises/exercise5/data/df_med.pkl")
pd.concat(df_visit, axis=0).to_pickle("exercises/exercise5/data/df_visit.pkl")
pd.concat(df_person, axis=0).to_pickle("exercises/exercise5/data/df_person.pkl")
pd.concat(df_bio, axis=0).to_pickle("exercises/exercise5/data/df_bio.pkl")
