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
from dateutil.relativedelta import relativedelta

dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

dict_param = {
    "control": {"final_survival_ratio": 0.5, "death_saturation_day": 10},
    "drugA": {"final_survival_ratio": 0.58, "death_saturation_day": 15},
    "drugB": {"final_survival_ratio": 0.58, "death_saturation_day": 10},
}

study_date = datetime.date.fromisoformat(conf["t_end"])
n_patient_per_cat = 100
list_age_range = [(0, 5), (5, 18), (18, 25), (25, 65), (65, 100)]
list_gender = [("f"), ("m")]
np.random.seed(42)

id_generator = idGenerator()

df_person, df_visit, df_cond, df_med = [], [], [], []
for age_range, gender in itertools.product(list_age_range, list_gender):
    for case, params in dict_param.items():
        params = params.copy()
        if case == "drugA" and gender == ("f") and age_range == (5, 18):
            params = dict_param["control"].copy()

        if case == "drugA" and gender == ("f") and age_range == (18, 25):
            params["final_survival_ratio"] = 0.6

        df_person_tmp, df_visit_tmp = gen_admin_tables(
            n=n_patient_per_cat,
            id_generator=id_generator,
            age_range=age_range,
            gender_list=gender,
            final_survival_ratio=params["final_survival_ratio"],
            death_saturation_day=params["death_saturation_day"],
        )
        df_cim10_tmp = gen_condition_table(
            df_visit_tmp,
            id_generator,
            list_good_cim10=conf["list_flu_cim10"],
            timeliness_date_per_hospital={
                "Clinique L.Pasteur": study_date - datetime.timedelta(days=45),
                "GHU A.Fleming": study_date - datetime.timedelta(days=45),
                "Hopital M.Bres": study_date - datetime.timedelta(days=45),
                "Centre F.Sinoussi": study_date - datetime.timedelta(days=45),
            },
        )
        df_med_tmp, _, _ = gen_med_table(
            df_visit_tmp,
            df_person_tmp,
            case,
            id_generator,
            deployment_date_per_hospital={
                "Clinique L.Pasteur": study_date - relativedelta(months=64),
                "GHU A.Fleming": study_date - relativedelta(months=60),
                "Hopital M.Bres": study_date - relativedelta(months=24),
            },
            timeliness_date_per_hospital={
                "Clinique L.Pasteur": study_date - datetime.timedelta(days=2),
                "GHU A.Fleming": study_date - datetime.timedelta(days=2),
                "Hopital M.Bres": study_date - datetime.timedelta(days=2),
                "Centre F.Sinoussi": study_date - datetime.timedelta(days=2),
            },
        )
        df_person.append(df_person_tmp)
        df_visit.append(df_visit_tmp)
        df_cond.append(df_cim10_tmp)
        df_med.append(df_med_tmp)

pd.concat(df_cond, axis=0).to_pickle("exercises/exercise3/data/df_condition.pkl")
pd.concat(df_med, axis=0).to_pickle("exercises/exercise3/data/df_med.pkl")
pd.concat(df_visit, axis=0).to_pickle("exercises/exercise3/data/df_visit.pkl")
pd.concat(df_person, axis=0).to_pickle("exercises/exercise3/data/df_person.pkl")
