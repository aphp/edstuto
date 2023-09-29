import itertools
import os
import yaml

from data_generator.pipelines import (
    gen_admin_tables,
    gen_condition_table,
    gen_med_table,
    gen_note_table,
    gen_nlp_extracted_table,
    idGenerator,
)
import numpy as np
import pandas as pd

dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

# list of synonyms of the two drugs
drugA_terms = ["drugA", "pneumo-drug", "SpinA"]
drugB_terms = ["drugB", "noso-plat", "testmedB"]

# list of sentences for drug administration and prescription.
list_drug_sentence = [
    "{} a été administré au patient.",
    "{} prescrit.",
    "La patient a été exposé au traitement {}",
    "Traitement au {}",
    "Le {} a été prescrit au patient",
    "2 plaquettes de {}",
]
list_negative_sentence = [
    "Aucun médicament anti-covid n'a été administré au patient.",
    "Le patient n'a suivi aucun protocol médicamenteux.",
    "La patient n'a pas été exposé aux traitements {}",
    "{} non prescrit.",
    "{} et {} non disponibles au moment de la prise en charge du patient.",
]

dict_param = {
    "control": {
        "final_survival_ratio": 0.5,
        "death_saturation_day": 10,
        "terms": drugA_terms + drugB_terms,
        "sentences": list_negative_sentence,
        "proportion_well_classified": 1,
    },
    "drugA": {
        "final_survival_ratio": 0.55,
        "death_saturation_day": 15,
        "terms": drugA_terms,
        "sentences": list_drug_sentence,
        "proportion_well_classified": 0.5,
    },
    "drugB": {
        "final_survival_ratio": 0.55,
        "death_saturation_day": 10,
        "terms": drugB_terms,
        "sentences": list_drug_sentence,
        "proportion_well_classified": 0.5,
    },
}

list_age_range = [(0, 5), (5, 18), (18, 25), (25, 65), (65, 100)]
list_gender = [("f"), ("m")]
np.random.seed(42 * 2)
n_patient_per_cat = 100

id_generator = idGenerator()

df_person, df_visit, df_cond, df_note, df_note_nlp, df_med, df_med_all = (
    [],
    [],
    [],
    [],
    [],
    [],
    [],
)
for age_range, gender in itertools.product(list_age_range, list_gender):
    for case, params in dict_param.items():

        params = params.copy()
        if case == "drugA" and gender == ("f") and age_range == (5, 18):
            for p in ["final_survival_ratio", "death_saturation_day"]:
                params[p] = dict_param["control"][p]
        # @todo : durty : counter-balance random effects
        if age_range == (18, 25) and case in ["drugA", "drugB"]:
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
            id_generator=id_generator,
            list_good_cim10=conf["list_flu_cim10"],
        )
        df_note_tmp = gen_note_table(
            df_visit_tmp,
            params["terms"],
            params["sentences"],
            id_generator=id_generator,
            duplicate_note_per_visit_ratio={2: 0.3},
        )
        df_note_nlp_tmp, _, _ = gen_nlp_extracted_table(
            df_visit_tmp, df_person_tmp, case, id_generator
        )

        df_med_tmp, _, _, = gen_med_table(
            df_visit_tmp,
            df_person_tmp,
            case,
            id_generator,
            proportion=params["proportion_well_classified"],
        )
        df_med_tmp = df_med_tmp.dropna(subset=["drug_source_value"]).reset_index(
            drop=True
        )

        (
            df_med_all_tmp,
            _,
            _,
        ) = gen_med_table(df_visit_tmp, df_person_tmp, case, id_generator)

        df_person.append(df_person_tmp)
        df_visit.append(df_visit_tmp)
        df_cond.append(df_cim10_tmp)
        df_note.append(df_note_tmp)
        df_note_nlp.append(df_note_nlp_tmp)
        df_med.append(df_med_tmp)
        df_med_all.append(df_med_all_tmp)

pd.concat(df_cond, axis=0).to_pickle("exercises/exercise4/data/df_condition.pkl")
pd.concat(df_note, axis=0).to_pickle("exercises/exercise4/data/df_note.pkl")
pd.concat(df_note_nlp, axis=0).to_pickle("exercises/exercise4/data/df_note_nlp.pkl")
pd.concat(df_visit, axis=0).to_pickle("exercises/exercise4/data/df_visit.pkl")
pd.concat(df_person, axis=0).to_pickle("exercises/exercise4/data/df_person.pkl")
pd.concat(df_med, axis=0).to_pickle("exercises/exercise4/data/df_med.pkl")
pd.concat(df_med_all, axis=0).to_pickle("exercises/exercise4/data/df_med_all.pkl")
