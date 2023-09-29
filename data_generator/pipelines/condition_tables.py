import datetime
import pandas as pd
import numpy as np
import yaml
import os
from .utils import *


dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))


def uniform_drawing(p):
    def f(row):
        return np.random.uniform() < p

    return f

def apply_error_per_hosp(df_cond, code_error_per_hospital, list_random_cim10):
    """
    Flaw "condition_source_value" column in df_cond.

    Parameters
    ----------
    df_cond: pandas.df,
        condition_occurrence table.
    code_error_per_hospital: dict,
        proba of miscoding for each hospital_id.
    list_random_cim10: list[str],
        list of flawed cim10.

    Returns
    -------
    df_cond: pandas.df,
        flawed condition_occurrence table.
    """
    if code_error_per_hospital != 0:
        df_cond = df_cond.assign(
            condition_source_value=lambda pp: pp.apply(
                lambda row: np.random.choice(
                    [
                        row["condition_source_value"],
                        np.random.choice(list_random_cim10, 1)[0],
                    ],
                    1,
                    p=[
                        1 - code_error_per_hospital[row["care_site_id"]],
                        code_error_per_hospital[row["care_site_id"]],
                    ],
                )[0]
                if row["care_site_id"] in code_error_per_hospital
                else row["condition_source_value"],
                axis=1,
            ).drop(columns=["care_site_id"])
        )
    return df_cond


def gen_condition_table(
    df_visit,
    id_generator,
    list_good_cim10,
    hospital_anomaly=[],
    deployment_date_per_hospital=None,
    progressive_cim10=True,
    timeliness_date_per_hospital=None,
    code_error_per_hospital=0,
):
    """
    Generate condition (diagnosis) data.

    :param df_visit: pandas df,
        minimal "visit_occurrence" table (OMOP schema)
    :id_generator idGenerator: obj,
        used to generate PKs in tables.
    :param list_good_cim10: list[str],
        list of cim10 code used to fill 'source_code_value'.
    :param hospital_anomaly: list,
        list of tuple (hospital_id, (anomaly_start_date, anomaly_end_date))
    :param deployment_date_per_hospital: dict,
        date at which data if fully available (5% of missing data compare to 90% before)
    :param progressive_cim10: bool,
        if Ture cim10 codes in list_good_cim10 are used in a chronological manner.
    :param timeliness_date_per_hospital: dict,
        date until which data if not made available.
    :param code_error_per_hospital: float,
        probability at which replacing meaningful CIM10 by random CIM10.


    :return: df_cond, pandas df,
        minimal "condition_occurrence" table (OMOP schema)
    """

    list_random_cim10 = conf["list_random_cim10"]
    df_cond = df_visit.drop_duplicates()[
        ["visit_occurrence_id", "person_id", "visit_start_datetime", "care_site_id"]
    ].rename(columns={"visit_start_datetime": "condition_start_datetime"})

    def gen_condition(date):
        if progressive_cim10:
            if len(list_good_cim10) != 3:
                # @todo: cannot handled more thant 3 progressive cim10 !!!
                raise NotImplementedError(
                    "A list of more than 3 progressive cim10 is not handled yet"
                )
            if date <= pd.Timestamp(2024, 11, 1):
                return list_good_cim10[0]
            elif date <= pd.Timestamp(2025, 2, 1):
                return list_good_cim10[1]
            elif date <= pd.Timestamp(2025, 8, 1):
                start_date, end_date = pd.to_datetime(datetime.date(2025, 2, 1)), date
                max_days = (datetime.date(2025, 8, 1) - datetime.date(2025, 2, 1)).days
                num_days = (end_date - start_date).days / max_days
                p = num_days / max_days
                return np.random.choice(list_good_cim10[-2:], 1, p=[1 - p, p])[0]
            else:
                return list_good_cim10[-1]
        else:
            return np.random.choice(list_good_cim10, 1)[0]

    df_cond = df_cond.assign(
        condition_occurrence_id=lambda pp: [
            id_generator.run("condition_occurrence_id") for _ in range(len(df_cond))
        ],
        condition_source_value=lambda pp: pp.condition_start_datetime.apply(
            lambda x: gen_condition(x)
        ),
    )
    df_cond = apply_error_per_hosp(df_cond, code_error_per_hospital, list_random_cim10)

    df_cond = apply_hosp_anomaly(
        df_cond, "condition_start_datetime", "condition_source_value", hospital_anomaly
    )

    if deployment_date_per_hospital:
        df_cond = apply_deployment_per_hosp(
            df_cond, df_visit, deployment_date_per_hospital
        )

    if timeliness_date_per_hospital:
        df_cond = apply_timeliness_per_hosp(
            df_cond, "condition_start_datetime", timeliness_date_per_hospital
        )

    df_cond = df_cond.drop(columns=["condition_start_datetime", "care_site_id"])

    return df_cond


def gen_comorb_table(
    df_visit,
    id_generator,
    df_person=None,
    df_med=None,
    list_comorb=[(["code1"], 1, uniform_drawing(0.3))],
):
    """
    Draw bio measurement table, based on given visits, bio concepts and their assignment functions.

    Parameters
    ----------
    :param df_visit: pandas.df
    :param id_generator:
    :param df_person: Optional(pandas.df)
        Dataframe containing patient information, may be used for value assignment. Optional.
    :param df_med: Optional(pandas.df)
        Dataframe containing drug information, may be used for value assignment. Optional.
    :param list_measurement: list,
        List of tuple (bio_concept, unit, ratio, drawing_func)
        - bio_concept: str, name of the biological concept measured
        - unit: unit of the measurement
        - ratio: ratio of kept values (i.e 1-pct_missing)
        - drawing_func : function callable on rows to assign biological values given the wanted conditions. Normal drawing by default.

    Returns
    -------
    :param df_bio: pandas.df
        DataFrame gathering the biological values associated to the input visits.
    """
    df_comorb = df_visit.drop_duplicates()[
        ["visit_occurrence_id", "person_id", "visit_start_datetime"]
    ].rename(columns={"visit_start_datetime": "condition_start_datetime"})

    if df_person is not None:
        df_comorb = pd.merge(df_comorb, df_person, on="person_id", how="inner")

    if df_med is not None:
        df_comorb = pd.merge(
            df_comorb,
            df_med[["visit_occurrence_id", "drug_source_value"]],
            on="visit_occurrence_id",
            how="left",
        )

    df_comorb_all = []
    # Artificially creates the code for every patient, and modify the `transformed_value` only for kept occurrences
    # The `drawing func` must return a bool, True for kept occurrences
    for list_codes, ratio, drawing_func in list_comorb:
        df_comorb_all.append(
            df_comorb.assign(
                condition_occurrence_id=lambda pp: pp["visit_occurrence_id"].apply(
                    lambda x: id_generator.run("condition_occurrence_id")
                ),
                condition_source_value=lambda pp: np.random.choice(list_codes, 1)[0],
                transformed_value=lambda pp: pp.apply(drawing_func, axis=1),
            )
            .query("transformed_value==True")
            .drop(columns=["transformed_value"])
            .sample(frac=ratio)
        )
    df_comorb_all = pd.concat(df_comorb_all, axis=0)

    df_comorb_all = df_comorb_all[
        [
            "visit_occurrence_id",
            "person_id",
            "condition_occurrence_id",
            "condition_source_value",
        ]
    ]

    # Shuffle dataframe to reset order
    df_comorb_all = df_comorb_all.sample(frac=1).reset_index(drop=True)

    return df_comorb_all
