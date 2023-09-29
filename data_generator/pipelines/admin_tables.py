import numpy as np
import datetime
from sklearn.preprocessing import normalize
import pandas as pd
from dateutil.relativedelta import relativedelta
from .utils import *
import os
import yaml
import dateutil


dir_path = os.path.dirname(os.path.realpath(__file__))
conf = yaml.safe_load(open(os.path.join(dir_path, "..", "conf.yaml")))

n_days_survival = conf["max_stay_duration"]

def gen_gender(gender_list, gender_noise=False, nan_age_proba=None):
    """
    Generate a gender info.

    Parameters
    ----------
    gender_list: list[str],
        list of possible gender.
    gender_noise: bool,
        if True, add 'male' and 'female' to the gender possibilities
    nan_age_proba: float (default None)
        if not None, replace nan_age_proba% of results by np.nan
    Returns
    -------
    - gender: str

    """
    control_gender_list = [el for el in gender_list if el not in ["male", "female"]]
    if len(control_gender_list) > 2:
        raise AttributeError("no more than 2 gender options are accepted")
    if len(control_gender_list) != len(
        [el for el in control_gender_list if el in ["m", "f"]]
    ):
        raise AttributeError(
            f"gender options {control_gender_list} must be in ['m', 'f']"
        )
    if gender_noise:
        if "m" in gender_list and "male" not in gender_list:
            gender_list.append("male")
        if "f" in gender_list and "female" not in gender_list:
            gender_list.append("female")
    if nan_age_proba is not None:
        remaining_proba = 1.0 - nan_age_proba
        n_gender = len(gender_list)
        p_gender = [remaining_proba / n_gender] * n_gender + [nan_age_proba]
        gender = np.random.choice(list(gender_list) + [np.nan], 1, p=p_gender)[0]
    else:
        gender = np.random.choice(list(gender_list))
    return gender


def gen_visit_start_datetime(
    study_start_date, epidemic_duration_months, censoring_ratio=None
):
    """
    Draw on start_datetime.

    Parameters
    ----------
    study_start_date: datetime.date,
        date from which start_datetime is drawn.
    epidemic_duration_months: int,
        number of months of the epidemic.
    censoring_ratio: float (default: None)
        exp. factor in the increasing exp. used to draw start dates. If None, a random date is drawn uniformly.

    Returns
    -------
    start_datetime: datetime.datetime
    """
    if censoring_ratio is not None:
        visit_start_datetime = draw_exp_random_date(
            censoring_ratio,
            study_start_date
            - dateutil.relativedelta.relativedelta(months=epidemic_duration_months),
            study_start_date,
        )
    else:
        visit_start_datetime = draw_random_date(
            study_start_date
            - dateutil.relativedelta.relativedelta(months=epidemic_duration_months),
            study_start_date,
        )
    return visit_start_datetime


def gen_care_site_id(
    list_hospital, hospital_proba=None, age_range_per_hospital=None, age=None
):
    """
    Draw care_site_id.

    Parameters
    ----------
    list_hospital: list[str],
        list of str in which sampling ids.
    hospital_proba: list[float],
        list of float between 0 and 1 summing to 1 (each value is the probability to draw the hospital with the same index in list_hospital).
    age_range_per_hospital: dict,
        age_range tuple for each hospital id.
    age: int,
        age of the patient.

    Returns
    -------
    care_site_id: str
    """

    def draw_hospital():
        if hospital_proba is None:
            return np.random.choice(list_hospital, 1)[0]
        else:
            return np.random.choice(list_hospital, 1, p=hospital_proba)[0]

    care_site_id = draw_hospital()
    if age_range_per_hospital is not None:
        while (
            care_site_id in age_range_per_hospital
            and age <= age_range_per_hospital[care_site_id][1]
            and age >= age_range_per_hospital[care_site_id][0]
            and np.random.random() >= 0.05
        ):
            care_site_id = draw_hospital()

    return care_site_id


def gen_end_datetime(
    study_start_date,
    visit_start_datetime,
    final_survival_ratio,
    y_survival_curve,
    care_site_id,
    list_hospital_with_no_death=(),
):
    """
    Draw visit_end_datetime.

    Parameters
    ----------
    study_start_date: datetime.date,
        date at which visits are starting.
    visit_start_datetime: datetime.date
    final_survival_ratio: float,
        final offset of the survival curve.
    y_survival_curve: float,
        exp. factor of the survival curve.
    care_site_id: str
    list_hospital_with_no_death: list[str],
        list of hospital for which final_survival_ratio_loc is one (no death).

    Returns
    -------
    visit_end_datetime: datetime.datetime
    """
    # change "final_survival_ratio_loc" if the bias "no death for this care site" is set
    if care_site_id in list_hospital_with_no_death:
        final_survival_ratio_loc = 1.0
    else:
        final_survival_ratio_loc = final_survival_ratio

    if np.random.random() < 1 - final_survival_ratio_loc:  # if death happens
        # init variables such that we enter the following "while" loop
        death_day, death_date = n_days_survival + 1, study_start_date
        # the number od
        while death_day > n_days_survival and death_date >= study_start_date:
            # draw the y value in the survival curve (between 1-x=start-, and final_survival_ratio_loc-x=end-)
            rand_survival = np.random.uniform(final_survival_ratio_loc, 1.0)
            # get the nb of day between visit_start_date and death, as the x-axis value of the 'rand_survival' y-axis value
            death_day = int(np.argmin(abs(y_survival_curve - rand_survival)))
            # death_date = visit_start_date + death_day
            death_date = visit_start_datetime + datetime.timedelta(days=death_day)
        visit_end_datetime = death_date
    else:  # death does not happen
        # no death date
        death_date = np.nan
        # draw random number of stay day
        stay_days = np.random.randint(1, n_days_survival + 1)
        # visit end = visit start + stay_days
        visit_end_datetime = visit_start_datetime + datetime.timedelta(days=stay_days)
        # if visit_end_datetime is later than study_start_date, visit_end_datetime is then unknown
        # (and will be censored in the survival analysis)
        if visit_end_datetime >= study_start_date:
            visit_end_datetime = np.nan

    return death_date, visit_end_datetime


def gen_birth_datetime(age, bad_age_proba, visit_start_datetime, random_date_age):
    """
    Draw birth_datetime.

    Parameters
    ----------
    age: int,
        age of the patient
    bad_age_proba: float,
        proba of replacing a relevant birth_datetime by a flawed random_date_age
    visit_start_datetime: datetime.date,
        visit date
    random_date_age: datetime.date,
         flawed date.

    Returns
    -------
    birth_datetime: datetime.datetime
    """
    if np.random.random() < bad_age_proba:
        birth_datetime = random_date_age
    else:
        birth_datetime = draw_random_date(
            visit_start_datetime - relativedelta(years=age + 1),
            visit_start_datetime - relativedelta(years=age),
        )
    return birth_datetime


def gen_source(source_list):
    """
    Draw EHR source (for the person).

    Parameters
    ----------
    source_list: list[str],
        list of possible sources.

    Returns
    -------
    source: str,
        EHR name.
    """
    cat_source_list = [el[0] for el in source_list]
    p_source_list = normalize(
        np.array([el[1] for el in source_list]).reshape((1, -1)), "l1"
    )[0]
    person_source = np.random.choice(cat_source_list, 1, p=p_source_list)[0]
    return person_source

def duplicate_patient_visit(df_patient, df_visit, id_generator, duplication_ratio=0.3):
    """
    Transcode some 'person_id' of 'person' into a "df_dedup".

    Parameters
    ----------
    df_patient: pandas df,
        "person" table.
    duplication_ratio: float (in [0,1]):
        ratio of patients with shifted id.

    Returns
    -------
    - df_patient: pandas.df,
        'person' table with some transcoded person_id.
    - df_dedup: pandas.df,
        person_id transcoding table (schema = ['person_id', 'unique_person_id'])
    """
    df_dedup = (
        df_patient.query("death_datetime != death_datetime")[["person_id"]]
        .copy()
        .rename(columns={"person_id": "unique_person_id"})
    )
    df_dedup_dead = (
        df_patient.query("death_datetime == death_datetime")[["person_id"]]
        .copy()
        .rename(columns={"person_id": "unique_person_id"})
    )
    df_dedup_dead["person_id"] = df_dedup_dead["unique_person_id"]

    df_dedup["person_id"] = df_dedup["unique_person_id"].apply(
        lambda x: [x]
        if np.random.random() >= duplication_ratio
        else [x, id_generator.run("person_id")]
    )
    df_dedup = df_dedup.explode("person_id")
    df_dedup_all = pd.concat([df_dedup, df_dedup_dead])

    df_patient = (
        df_patient.merge(
            df_dedup_all, left_on="person_id", right_on="unique_person_id", how="inner"
        )
        .rename(columns={"person_id_y": "person_id"})
        .drop(columns=["unique_person_id", "person_id_x"])
    )

    df_visit = (
        df_visit.merge(
            df_dedup_all, left_on="person_id", right_on="unique_person_id", how="inner"
        )
        .rename(columns={"person_id_y": "person_id"})
        .drop(columns=["unique_person_id", "person_id_x"])
    )

    df_visit["visit_occurrence_id"] = df_visit["visit_occurrence_id"].apply(
        lambda x: id_generator.run("visit_occurrence_id")
    )
    return df_patient, df_visit, df_dedup


def deduplicate_patient(df_person, df_dedup, transco, hard_sucess_ratio=0.3):
    """
    Parameters
    ----------
    df_person: pandas.df,
        a dataframe with 'person_id' as patient id.
    df_dedup: pandas.df,
        person_id transcoding table (schema = ['person_id', 'unique_person_id'])
    transco: str,
        type of transcoding (hard or probabilistic)
    hard_sucess_ratio :float (in [0,1]):
        ratio of success of the determinist approach

    Returns
    -------
    df_dedup_hard: pandas.df,
        person_id transcoding table for determinist method with a sucess rate of hard_sucess_ratio
        (schema = ['person_id', 'unique_person_id'])
    df_dedup_proba: pandas.df,
        person_id transcoding table. 'Prob' is the probability of good pairing.
        (schema: [person_id', 'unique_person_id''prob'])
        None if transco=="hard".
    """
    df_dedup_unique = df_dedup[df_dedup["person_id"] != df_dedup["unique_person_id"]]
    df_dedup_hard, df_dedup_proba = None, None
    if transco is not None:
        if transco in ["hard", "probabilistic"]:
            df_dedup_hard = df_dedup_unique.sample(frac=hard_sucess_ratio)
            df_dedup_proba = df_dedup_hard.copy()
            df_dedup_proba["prob"] = 1
        if transco == "probabilistic":
            # "prob" is not uniform (40% of pairing prob are drawn in [0.9, 1], 60% in [0, 0.9] amongs those not found in determinist way)
            df_dedup_proba = (
                pd.concat([df_dedup_proba, df_dedup_unique])
                .sort_values("prob")
                .drop_duplicates(["person_id", "unique_person_id"])
            )
            df_dedup_proba["prob"] = df_dedup_proba["prob"].apply(
                lambda x: x
                if x == 1
                else np.random.uniform(0.9, 1.0)
                if np.random.random() <= 0.4
                else np.random.uniform(0.0, 0.9)
            )
            # We should also add patients that are not deplucates with score < 0.4
            person_ids = df_person.person_id.unique().tolist()
            np.random.shuffle(person_ids)
            person_ids_1 = person_ids
            np.random.shuffle(person_ids)
            person_ids_2 = person_ids

            df_dedup_proba_false = pd.DataFrame(
                {"person_id": person_ids_1, "unique_person_id": person_ids_2}
            )
            df_dedup_proba_false["prob"] = 0
            df_dedup_proba_false_sample = df_dedup_proba_false.sample(frac=0.1)
            df_dedup_proba_false_sample["prob"] = df_dedup_proba_false_sample[
                "prob"
            ].apply(
                lambda x: np.random.uniform(0, 0.2)
                if np.random.random() <= 0.9
                else np.random.uniform(0.2, 0.5)
            )
            df_dedup_proba = pd.concat([df_dedup_proba, df_dedup_proba_false_sample])
            df_dedup_proba = df_dedup_proba.drop_duplicates(
                ["person_id", "unique_person_id"]
            ).reset_index(drop=True)
    return df_dedup_hard, df_dedup_proba


def gen_admin_tables(
    n,
    id_generator,
    age_range=(0, 100),
    gender_list=("m", "f"),
    gender_noise=False,
    nan_age_proba=None,
    bad_age_proba=0,
    bad_visit_date_proba=0,
    source_list=tuple([("EHR 1", 1)]),
    censoring_ratio=None,
    death_saturation_day=15,
    list_hospital=conf["list_hospital"],
    hospital_proba=None,
    hospital_anomaly=(),
    final_survival_ratio=0.4,
    age_range_per_hospital=None,
    study_start_date=datetime.date.fromisoformat(conf["t_end"]),
    epidemic_duration_months=conf["epidemic_duration_months"],
    random_date_visit=draw_random_date(
        datetime.date(1800, 1, 1), datetime.date(1890, 1, 1)
    ),
    random_date_age=draw_random_date(
        datetime.date(1800, 1, 1), datetime.date(1890, 1, 1)
    ),
    list_hospital_with_no_death=(),
):
    """
    Draw randdf_dedupom administrative data.

    :param n: int,
        ratio of patient.
    :id_generator idGenerator: obj,
        used to generate PKs in tables.
    :param age_range: tuple of int,
        min and max age to filter patients.
    :param gender_list: list of str,
        must be in ['f', 'female, 'm', 'male']
    :param gender_noise: bool,
        if True, 'm' can be replaced by "male" and "f" by "female"
    :param nan_age_proba: float between 0 and 1,
        probability at which replacing the patient's birthdate by a nan
    :param bad_age_proba: float between 0 and 1,
        probability at which replacing the patient's birthdate by one specific random but unrealistic birthdate
    :param bad_visit_date_proba: float between 0 and 1,
        probability at which replacing the patient's visit date by one specific random but unrealistic date
    :param source_list: list of str,
        list of EHR software to fill the cdm_source column.
    :param censoring_ratio: float between 0 and 1,
        exp coeff in the exp infection curve (number of days at which the inflexion point occurs). If None, visit_start_date is drawn uniformly.
    :param death_saturation_day: int,
        exp coeff in the exp survival curve (number of days at which the inflexion point occurs)
    :param hospital_anomaly: list of tuple (hospital name-str-, datetime.date, ),
         interval of dates at which the specified hospital has no death date recorded.
    :param final_survival_ratio: float (between 0 and 1),
        ratio of final patient's survival.
    :param age_range_per_hospital: dict,
        age_range tuple for each hospital id.
    :param study_start_date: datetime.date,
        date from which start_datetime is drawn.
    :param epidemic_duration_months: int,
        number àf months of the epidemic.
    :param random_date_visit: datetime.date,
        random flowed data.
    :param random_date_age: datetime.date,
        random flowed data.
    :param list_hospital_with_no_death: list[str],
        list of hospital for which final_survival_ratio_loc is one (no death).

    :return:
        - df_person: pandas df,
            minimal "person" table (OMOP schema)
        - df_visit: pandas df,
            minimal "person" table (OMOP schema)
        - df_dedup: pandas df,
            columns are 'person_id' and 'unique_person_id'. None if split_inter_annual_visit is False.
    """
    (
        list_person_id,
        list_birth_datetime,
        list_death_datetime,
        list_gender_source_value,
        list_cdm_source,
    ) = ([], [], [], [], [])
    (
        list_visit_occurrence_id,
        list_care_site_id,
        list_visit_start_datetime,
        list_visit_end_datetime,
        list_person_id,
        list_visit_source_value,
    ) = ([], [], [], [], [], [])

    n_patient = int(n * (age_range[1] - age_range[0]))

    # plot survival curve
    y_survival_curve, _, _ = survival_exp(
        final_survival_ratio,
        n_days=n_days_survival,
        saturation=death_saturation_day,
    )

    for _ in range(n_patient):
        # id
        person_id = id_generator.run("person_id")
        visit_occurrence_id = id_generator.run("visit_occurrence_id")

        # gender
        gender = gen_gender(gender_list, gender_noise, nan_age_proba)

        #
        visit_start_datetime = gen_visit_start_datetime(
            study_start_date, epidemic_duration_months, censoring_ratio
        )

        # constant
        visit_source_value = "Hospitalisés"
        age = np.random.randint(*age_range)
        care_site_id = gen_care_site_id(
            list_hospital, hospital_proba, age_range_per_hospital, age
        )

        ##############
        death_date, visit_end_datetime = gen_end_datetime(
            study_start_date,
            visit_start_datetime,
            final_survival_ratio,
            y_survival_curve,
            care_site_id,
            list_hospital_with_no_death,
        )

        # birth
        birth_datetime = gen_birth_datetime(
            age, bad_age_proba, visit_start_datetime, random_date_age
        )
        if np.random.random() < bad_visit_date_proba:
            visit_start_datetime = random_date_visit

        # source
        person_source = gen_source(source_list)
        if person_source == "EHR 2":
            birth_datetime = np.nan

        list_person_id.append(person_id)
        list_birth_datetime.append(birth_datetime)
        list_death_datetime.append(death_date)
        list_gender_source_value.append(gender)
        list_cdm_source.append(person_source)
        list_visit_occurrence_id.append(visit_occurrence_id)
        list_care_site_id.append(care_site_id)
        list_visit_start_datetime.append(visit_start_datetime)
        list_visit_end_datetime.append(visit_end_datetime)
        list_visit_source_value.append(visit_source_value)

    df_person = pd.DataFrame(
        {
            "person_id": list_person_id,
            "birth_datetime": list_birth_datetime,
            "death_datetime": list_death_datetime,
            "gender_source_value": list_gender_source_value,
            "cdm_source": list_cdm_source,
        }
    )

    df_visit = pd.DataFrame(
        {
            "visit_occurrence_id": list_visit_occurrence_id,
            "care_site_id": list_care_site_id,
            "visit_start_datetime": list_visit_start_datetime,
            "visit_end_datetime": list_visit_end_datetime,
            "person_id": list_person_id,
            "visit_source_value": list_visit_source_value,
        }
    )

    df_person = apply_hosp_anomaly(
        df_person.merge(
            df_visit[["visit_start_datetime", "care_site_id", "person_id"]],
            on="person_id",
            how="inner",
        ),
        "visit_start_datetime",
        "death_datetime",
        hospital_anomaly,
    ).drop(columns=["visit_start_datetime", "care_site_id"])

    df_visit = df_visit.drop_duplicates(["person_id"])
    df_person["death_datetime"] = pd.to_datetime(df_person["death_datetime"])
    df_person["birth_datetime"] = pd.to_datetime(df_person["birth_datetime"])
    df_visit["visit_start_datetime"] = pd.to_datetime(df_visit["visit_start_datetime"])
    df_visit["visit_end_datetime"] = pd.to_datetime(df_visit["visit_end_datetime"])

    # Shuffle dataframe to reset order
    df_person = df_person.sample(frac=1).reset_index(drop=True)
    df_visit = df_visit.sample(frac=1).reset_index(drop=True)

    return df_person, df_visit
