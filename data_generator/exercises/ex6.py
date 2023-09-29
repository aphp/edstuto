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
import datetime

dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

dict_param = {
    "control": {"final_survival_ratio": 0.5, "death_saturation_day": 10},
    "drugA": {"final_survival_ratio": 0.55, "death_saturation_day": 15},
    "drugB": {"final_survival_ratio": 0.55, "death_saturation_day": 10},
}

list_age_range = [(0, 5), (5, 18), (18, 25), (25, 65), (65, 100)]
list_gender = [("f"), ("m")]
np.random.seed(42)
n_patient_per_cat = 50

id_generator = idGenerator()

df_person, df_visit, df_cond, df_med = [], [], [], []
for age_range, gender in itertools.product(list_age_range, list_gender):
    for case, params in dict_param.items():
        if case == "drugA" and gender == ("f") and age_range == (5, 18):
            params = dict_param["control"]

        df_person_tmp, df_visit_tmp = gen_admin_tables(
            n=n_patient_per_cat,
            id_generator=id_generator,
            age_range=age_range,
            gender_list=gender,
            final_survival_ratio=params["final_survival_ratio"],
            death_saturation_day=params["death_saturation_day"],
            hospital_anomaly=[
                (
                    "GHU A.Fleming",
                    (datetime.date(2021, 1, 1), datetime.date(2021, 4, 13)),
                )
            ],
        )
        df_cim10_tmp = gen_condition_table(
            df_visit_tmp, id_generator, list_good_cim10=conf["list_flu_cim10"]
        )
        df_med_tmp, _, _ = gen_med_table(
            df_visit_tmp, df_person_tmp, case, id_generator
        )
        df_person.append(df_person_tmp)
        df_visit.append(df_visit_tmp)
        df_cond.append(df_cim10_tmp)
        df_med.append(df_med_tmp)

pd.concat(df_cond, axis=0).to_pickle("exercises/exercise6/data/df_condition.pkl")
pd.concat(df_med, axis=0).to_pickle("exercises/exercise6/data/df_med.pkl")
pd.concat(df_visit, axis=0).to_pickle("exercises/exercise6/data/df_visit.pkl")
pd.concat(df_person, axis=0).to_pickle("exercises/exercise6/data/df_person.pkl")
