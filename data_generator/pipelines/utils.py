import datetime
import numpy as np
import pandas as pd


def apply_timeliness_per_hosp(df_to_process, date_col, timeliness_date_per_hospital):
    """
    Delete data for hospitals with timeliness_dates.

    Parameters
    ----------
    df_to_process: pandas.df,
        table for which deleting data. Must contain 'care_site_id' column (tips: if not, pre-join with visit_occurrence_id).
    date_col: str,
        column name of the relevant date to consider in df_to_process
    timeliness_date_per_hospital: dict,
        date until which data if not made available.
    Returns
    -------
    df_to_process: pandas.df,
        initial df with delete data
    """
    list_idx = []
    for i, row in df_to_process.iterrows():
        if row[date_col].date() <= timeliness_date_per_hospital[row["care_site_id"]]:
            list_idx.append(i)
    df_to_process = df_to_process.iloc[list_idx]
    return df_to_process


class idGenerator:
    def __init__(self):
        self.taboo = {}
        self.ids = {}

    def run(self, key):
        if key not in self.taboo:
            i = 0
            self.taboo[key] = 1
            self.ids[key] = np.arange(80_000_000, 90_000_000)
            np.random.shuffle(self.ids[key])
        else:
            i = self.taboo[key]
            self.taboo[key] += 1
        # Return random 8-digits id
        return int(self.ids[key][i])


def apply_deployment_per_hosp(df_to_process, df_visit, deployment_date_per_hospital):
    """
    Delete data for hospitals with deployment date.

    Parameters
    ----------
    df_to_process: pandas.df,
        df for which deleting data.
    df_visit: pandas.df,
        visit_occurrence table.
    deployment_date_per_hospital: dict,
        date at which data if fully available (5% of missing data compare to 90% before)

    Returns
    -------
    df_to_process: pandas.df,
        processed df.
    """
    visit_cols = ["visit_occurrence_id", "visit_start_datetime"]
    del_care_site_id = False
    if "care_site_id" not in df_to_process.columns:
        visit_cols.append("care_site_id")
        del_care_site_id = True
    df_to_process = df_to_process.merge(
        df_visit[visit_cols],
        on="visit_occurrence_id",
        how="inner",
    )
    list_idx = []
    for i, row in df_to_process.iterrows():
        if row["care_site_id"] in deployment_date_per_hospital:
            if (
                row["visit_start_datetime"].date()
                >= deployment_date_per_hospital[row["care_site_id"]]
                or np.random.random() < 0.05
            ):
                list_idx.append(i)
        elif np.random.random() < 0.9:
            list_idx.append(i)
    df_to_process = (
        df_to_process.iloc[list_idx]
        .drop(columns=["visit_start_datetime"])
        .reset_index(drop=True)
    )
    if del_care_site_id:
        df_to_process = df_to_process.drop(columns=["care_site_id"])
    return df_to_process


def apply_hosp_anomaly(df_to_process, date_col, value_col, hospital_anomaly):
    """
    Replace condition_source_value by np.nan for anomalies in hospital_anomaly.

    Parameters
    ----------
    df_to_process: pandas.df,
        table for which deleting data. Must contain 'care_site_id' column (tips: if not, pre-join with visit_occurrence_id).
    date_col: str,
        column name of the relevant date to consider in df_to_process
    value_col: str,
        column on which the anomaly has an impact
    hospital_anomaly; list,
        list of tuple (hospital_id, (anomaly_start_date, anomaly_end_date))

    Returns
    -------
    df_to_process: pandas.df,
        flawed condition_occurrence table.
    """
    for hospital, anomaly_range in hospital_anomaly:
        min_date, max_date = anomaly_range
        df_to_process = pd.concat(
            [
                df_to_process.query(
                    f"care_site_id == @hospital and ({date_col}<=@max_date and {date_col}>=@min_date)"
                ).assign(**{value_col: lambda pp: np.nan}),
                df_to_process.query(
                    f"care_site_id == @hospital and ({date_col}>@max_date or {date_col}<@min_date)"
                ),
                df_to_process.query("care_site_id != @hospital"),
            ],
            axis=0,
        ).reset_index(drop=True)
    return df_to_process


def survival_exp(final_survival_ratio=0.4, n_days=20, saturation=15):
    """
    Return decreasing exp curve information.

    :param final_survival_ratio: float, y offset
    :param n_days: int, number of drawn points
    :param saturation: int, inflexion point
    :return: np array of float, y values of the exp curve
    :return: alpha, float, exp coeff
    :return: start, float, x offset
    """
    alpha = (
        0.5
        if saturation == 5
        else 0.3
        if saturation == 10
        else 0.2
        if saturation == 15
        else 0.15
    )
    start = np.log(1 - final_survival_ratio) / alpha
    x = np.arange(0, n_days)
    y = [np.exp(-alpha * (el - start)) + final_survival_ratio for el in x]
    return np.array(y), alpha, start


def return_survival_exp(y, alpha, beta, start):
    """
    Get x-value for a y-value and a given exp.

    :param y: float, y-value
    :param alpha: float, exp coeff
    :param beta: float, y offset
    :param start: float, x offset
    :return:
    """
    return -(1 / alpha) * np.log(y - beta) + start


def draw_random_date(start_date, end_date):
    """
    Draw a date between start_date and end_date in a uniform fashion.

    :param start_date: datetime.date, min date
    :param end_date: datetime.date, max date
    :return: datetime.date
    """
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = int(np.random.uniform(0, days_between_dates))
    random_date = start_date + datetime.timedelta(days=random_number_of_days)
    return random_date


def draw_exp_random_date(
    alpha,
    start_date,
    end_date,
):
    """
    Draw a date between start_date and end_date in an exponentially increasing fashion.

    :param alpha: float, exp coeff.
    :param start_date: datetime.date, min date
    :param end_date: datetime.date, max date
    :return: datetime.date
    """
    days_between_dates = (end_date - start_date).days
    y = np.array([np.exp(alpha * el) for el in np.arange(0, days_between_dates)])
    n_days = int(abs(np.argmin(abs(y - np.random.uniform(low=1, high=max(y))))))
    random_date = start_date + datetime.timedelta(days=n_days)
    return random_date
