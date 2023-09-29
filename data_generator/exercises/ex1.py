import itertools
import os
import yaml

from data_generator.pipelines import (
    gen_admin_tables,
    gen_condition_table,
    gen_med_table,
    idGenerator,
)
import numpy as np
import pandas as pd

dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

dict_param = {
    "control": {
        "final_survival_ratio": 0.5,
        "death_saturation_day": 10,
        "censoring_ratio": 0.002,
    },
    "drugA": {
        "final_survival_ratio": 0.55,
        "death_saturation_day": 15,
        "censoring_ratio": 0.002,
    },
    "drugB": {
        "final_survival_ratio": 0.55,
        "death_saturation_day": 10,
        "censoring_ratio": 0.002,
    },
}


def clean_effects(params):
    if case in ["drugB"] and "f" in gender and age_range == (18, 25):
        params["final_survival_ratio"] = 0.68
    elif case in ["drugB", "drugA"] and age_range == (18, 25):
        params["final_survival_ratio"] = 0.63
    elif case in ["drugB"] and age_range == (5, 18):
        params["final_survival_ratio"] = 0.6
    elif (case in ["drugA"] and age_range == (5, 18) and "m" in gender) | (
        case in ["drugB"] and age_range == (65, 100) and "f" in gender
    ):
        params["final_survival_ratio"] = 0.58
    if case == "drugA" and gender == ("f") and age_range == (65, 100):
        params["censoring_ratio"] = 0.01
    return params


n_patient_per_cat = 50
list_age_range = [(5, 18), (18, 25), (25, 65), (65, 100)]
list_gender = [["f"], ["m"]]
np.random.seed(42)

id_generator = idGenerator()

df_person = []
df_visit = []
df_cond = []
df_med = []
df_transco_visit = []
df_dedup = []
for age_range, gender in itertools.product(list_age_range, list_gender):
    for case, params in dict_param.items():

        params = params.copy()
        if case == "drugA" and "f" in gender and age_range == (5, 18):
            params = dict_param["control"].copy()
        params = clean_effects(params)

        df_person_tmp, df_visit_tmp = gen_admin_tables(
            n=n_patient_per_cat,
            id_generator=id_generator,
            age_range=age_range,
            nan_age_proba=0,
            bad_age_proba=0,
            bad_visit_date_proba=0.01,
            gender_list=gender.copy(),
            gender_noise=False,
            source_list=(("EHR 1", 9), ("EHR 2", 1)),
            final_survival_ratio=params["final_survival_ratio"],
            censoring_ratio=params["censoring_ratio"],
            death_saturation_day=params["death_saturation_day"],
        )
        df_cim10_tmp = gen_condition_table(
            df_visit_tmp,
            id_generator=id_generator,
            list_good_cim10=conf["list_flu_cim10"],
        )

        # generate patients with various visits and reasons for admission
        for _ in range(1):
            df_person_tmpbis, df_visit_tmpbis = gen_admin_tables(
                n=n_patient_per_cat,
                id_generator=id_generator,
                age_range=age_range,
                nan_age_proba=0,
                bad_age_proba=0,
                bad_visit_date_proba=0.01,
                gender_list=gender.copy(),
                gender_noise=False,
                source_list=(("EHR 1", 9), ("EHR 2", 1)),
                final_survival_ratio=params["final_survival_ratio"],
                death_saturation_day=params["death_saturation_day"],
            )
            df_cim10_tmpbis = gen_condition_table(
                df_visit_tmpbis,
                id_generator=id_generator,
                list_good_cim10=conf["list_random_cim10"],
            )
            df_cim10_tmp = pd.concat([df_cim10_tmp, df_cim10_tmpbis], axis=0)
            df_person_tmp = pd.concat([df_person_tmp, df_person_tmpbis], axis=0)
            df_visit_tmp = pd.concat([df_visit_tmp, df_visit_tmpbis], axis=0)

        df_med_tmp, _, _ = gen_med_table(
            df_visit_tmp, df_person_tmp, case, id_generator
        )

        df_person.append(df_person_tmp)
        df_visit.append(df_visit_tmp)
        df_cond.append(df_cim10_tmp)
        df_med.append(df_med_tmp)

pd.concat(df_cond, axis=0).to_pickle("exercises/exercise1/data/df_condition.pkl")
pd.concat(df_med, axis=0).to_pickle("exercises/exercise1/data/df_med.pkl")
pd.concat(df_visit, axis=0).to_pickle("exercises/exercise1/data/df_visit.pkl")
pd.concat(df_person, axis=0).to_pickle("exercises/exercise1/data/df_person.pkl")
