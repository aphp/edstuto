import pandas as pd
import numpy as np
from .utils import *


def transcoding(df_med, df_visit, df_person, transco, nan_in_det_ratio):
    """
    Replace visit_occurrence_id in df_med by other ids simulating a difference of identifications for visits in
    the medication EHR and the administrative EHR.

    Parameters
    ----------
    df_med: pandas.df
    df_visit: pandas.df
    df_person: pandas.df
    transco: str,
        type of transcoding (hard or probabilistic)
    nan_in_det_ratio: float,
        ratio of nan in df_transco

    Returns
    -------
    df_med: pandas.df,
        df_med with modified visit_occurrence_id
    df_transco_visit_hard: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med.
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id''])
    df_transco_visit_proba: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med. 'Prob' is the probability of good linkage.
        (the probability at which the linked visit_occurrence_id is one resulting to death).
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id', 'prob'])
        None if transco=="hard".
    """
    df_transco_visit_hard, df_transco_visit_proba = None, None
    if transco is not None:
        # create df_transco_visit_hard
        if transco in ["hard", "probabilistic"]:
            df_transco_visit_hard = df_med[["visit_occurrence_id", "transco"]].rename(
                columns={
                    "visit_occurrence_id": "EHR1_visit_id",
                    "transco": "EHRmed_visit_id",
                }
            )
            if nan_in_det_ratio != 0:
                df_transco_visit_hard = df_transco_visit_hard.assign(
                    EHRmed_visit_id=lambda pp: pp["EHRmed_visit_id"].apply(
                        lambda x: np.nan if np.random.random() < nan_in_det_ratio else x
                    )
                )

            df_transco_visit_proba = df_med[["visit_occurrence_id", "transco"]].rename(
                columns={
                    "visit_occurrence_id": "EHR1_visit_id",
                    "transco": "EHRmed_visit_id",
                }
            )

        # create df_transco_visit_proba
        if transco == "probabilistic":
            # init
            # "prob" is not uniform (40% of linkage prob are drawn in [0.9, 1], 60% in [0, 0.9])
            df_transco_visit_proba = df_transco_visit_proba.assign(
                prob=lambda pp: [
                    np.random.uniform(0.9, 1.0)
                    if np.random.random() <= 0.4
                    else np.random.uniform(0.0, 0.9)
                    for _ in range(len(df_transco_visit_proba))
                ]
            )

            # replace ids by the ones of visit resulting to death
            list_available_id = (
                df_visit.merge(df_person, on="person_id", how="inner")
                .query("death_datetime==death_datetime")
                .visit_occurrence_id.unique()
            )
            if len(list_available_id) == 0:
                list_available_id = df_visit.visit_occurrence_id.unique()
            list_available_id = df_visit.visit_occurrence_id.unique()

            # flaw linkage depends on 'prob'
            df_transco_visit_proba["EHR1_visit_id"] = df_transco_visit_proba.apply(
                lambda row: np.random.choice(
                    [row["EHR1_visit_id"], np.random.choice(list_available_id, 1)[0]],
                    1,
                    p=[row["prob"], 1 - row["prob"]],
                )[0],
                axis=1,
            )
        df_med = df_med.drop(columns=["visit_occurrence_id"]).rename(
            columns={"transco": "EHRmed_visit_id"}
        )
    else:
        df_med = df_med.drop(columns=["transco"])

    return df_med, df_transco_visit_hard, df_transco_visit_proba


def gen_med_table(
    df_visit,
    df_person,
    drug_source_value,
    id_generator,
    nan_in_det_ratio=0,
    transco=None,
    deployment_date_per_hospital=None,
    timeliness_date_per_hospital=None,
    proportion=1.0,
):
    """
    :param df_visit:
    :param df_person:
    :param drug_source_value: str,
        drug source code.
    :id_generator idGenerator: obj,
        used to generate PKs in tables.
    :param transco: str,
        type of transcoding
    :param deployment_date_per_hospital: dict,
        date at which data if fully available (5% of missing data compare to 90% before)
    :param timeliness_date_per_hospital: dict,
        date until which data if not made available.
    :param proportion: float,
        ratio of nan "drug_source_value" (between 0 and 1)

    :return:
    df_med: pandas.df,
        "drug_exposure" table
    df_transco_visit_hard: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med.
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id''])
    df_transco_visit_proba: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med. 'Prob' is the probability of good linkage.
        (the probability at which the linked visit_occurrence_id is one resulting to death).
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id', 'prob'])
        None if transco=="hard".
    """

    if drug_source_value == "control":
        df_med = pd.DataFrame(
            columns=[
                "visit_occurrence_id",
                "drug_exposure_id",
                "drug_source_value",
                "transco",
                "drug_exposure_start_date",
            ]
        )
    else:
        df_med = df_visit.drop_duplicates()[
            ["visit_occurrence_id", "visit_start_datetime"]
        ].rename(columns={"visit_start_datetime": "drug_exposure_start_date"})
        df_med = df_med.assign(
            drug_exposure_id=lambda pp: [
                id_generator.run("drug_exposure_id") for _ in range(len(df_med))
            ],
            cdm_source=lambda pp: "EHR med",
            drug_source_value=lambda pp: [
                drug_source_value
                if proportion == 1
                else np.random.choice(
                    [drug_source_value, np.nan], 1, p=[proportion, 1 - proportion]
                )[0]
                for _ in range(len(df_med))
            ],
            transco=lambda pp: [
                id_generator.run("drug_transco") for _ in range(len(df_med))
            ],
        ).assign(
            drug_source_value=lambda pp: pp["drug_source_value"].replace(
                {"nan": np.nan}
            )
        )

    if deployment_date_per_hospital:
        df_med = apply_deployment_per_hosp(
            df_med, df_visit, deployment_date_per_hospital
        )

    if timeliness_date_per_hospital:
        df_med = apply_timeliness_per_hosp(
            df_med.merge(
                df_visit[["visit_occurrence_id", "care_site_id"]],
                on="visit_occurrence_id",
                how="inner",
            ),
            "drug_exposure_start_date",
            timeliness_date_per_hospital,
        ).drop(columns=["care_site_id"])

    df_med, df_transco_visit_hard, df_transco_visit_proba = transcoding(
        df_med, df_visit, df_person, transco, nan_in_det_ratio
    )

    df_med = df_med.drop(columns=["drug_exposure_start_date"])

    # Shuffle dataframe to reset order
    df_med = df_med.sample(frac=1).reset_index(drop=True)

    return df_med, df_transco_visit_hard, df_transco_visit_proba
