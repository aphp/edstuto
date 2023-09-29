import numpy as np
import pandas as pd


def normal_drawing(mu, sigma):
    def f(row):
        return np.random.normal(mu, sigma)
    return f


def gen_bio_table(
    df_visit,
    id_generator,
    df_person=None,
    df_med=None,
    list_measurement=[('bmi', 'kg.cm^-2', 0.7, normal_drawing(25, 3))],
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
    df_bio = df_visit[
        ["visit_occurrence_id", "visit_start_datetime", "person_id"]
    ].rename(columns={"visit_start_datetime": "measurement_datetime"})

    if df_person is not None:
        df_bio = pd.merge(
            df_bio,
            df_person,
            on="person_id",
            how="inner"
        )

    if df_med is not None:
        df_bio = pd.merge(
            df_bio,
            df_med[["visit_occurrence_id", "drug_source_value"]],
            on="visit_occurrence_id",
            how="left"
        )

    df_bio_all = []
    for bio_concept, unit, ratio, drawing_func in list_measurement:
        df_bio_all.append(
            df_bio.assign(
                measurement_id=lambda pp: pp['visit_occurrence_id'].apply(
                    lambda x: id_generator.run('measurement_id')),
                concept_source_value=lambda pp: bio_concept,
                transformed_value=lambda pp: pp.apply(drawing_func, axis=1),
                transformed_unit=lambda pp: unit
            )
            .sample(frac=ratio)
        )
    df_bio_all = pd.concat(df_bio_all, axis=0)

    df_bio_all = df_bio_all[
        ["measurement_id", "visit_occurrence_id", "measurement_datetime",
         "concept_source_value", "transformed_value", "transformed_unit"]
    ]

    # Shuffle dataframe to reset order
    df_bio_all = df_bio_all.sample(frac=1).reset_index(drop=True)

    return df_bio_all
