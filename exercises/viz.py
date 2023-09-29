import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from lifelines.statistics import logrank_test
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts
import altair as alt
from dateutil.relativedelta import relativedelta

kmf = KaplanMeierFitter()
kmf_c = KaplanMeierFitter()
# we assume that a patient who exits a hospital alife survives at least "survival_duration_days_if_survive" days since her admission date
survival_duration_days_if_survive = 20


def get_df_kaplan(
    df_person_tmp,
    df_visit_tmp,
    df_med_tmp,
    t_end_of_study,
    age_range=None,
    gender=None,
    max_stay_duration=survival_duration_days_if_survive,
):
    """
    Compute dataframe used to compute lifelines.KaplanMeierFitter results.

    :param df_person_tmp: pandas df,
        minimal "person" table (same schema than raw data df)
    :param df_visit_tmp: pandas df,
        minimal "visit_occurrence" table (same schema than raw data df)
    :param df_cond_tmp: pandas df,
        minimal "condition_occurrence" table (same schema than raw data df)
    :param df_med_tmp: pandas df,
        minimal "drug_prescription" table (same schema than raw data df)
    :param age_range: int tuple (size 2),
        min and max age to filter the population.
    :param gender: str,
        gender to filter the population.
    :param t_end_of_study: datetime.date,
        date after which no information can be trusted.
    :param max_stay_duration: int,
        max stay duration in days (if a patient has a visit_end_date, one can consider that the patient survives "max stay duration" days afterwards)

    :return: pandas df
    """
    df_visit_tmp = df_visit_tmp.query(
        "visit_start_datetime <= @t_end_of_study")

    # for each patient : duration, death or not (then no info anymore)
    df_admin = (
        df_person_tmp.merge(df_visit_tmp, on="person_id", how="inner")
        .merge(
            df_med_tmp[["drug_source_value", "visit_occurrence_id"]],
            on="visit_occurrence_id",
            how="left",
        )
        .fillna({"drug_source_value": "control"})
    )

    # filtering
    if age_range is not None:
        df_admin = df_admin.assign(
            age=lambda pp: pp[["visit_start_datetime", "birth_datetime"]].apply(
                lambda r: relativedelta(
                    r["visit_start_datetime"], r["birth_datetime"]
                ).years,
                axis=1,
            )
        ).query(f"age<{age_range[1]} and age>={age_range[0]}")
    if gender is not None:
        df_admin = df_admin.query(f"gender_source_value=='{gender}'")

    # build df for kaplan-meier plot
    # 'T': durations
    # 'E': binary, representing whether “death” was observed or not (alternatively an individual can be censored)

    # patients are considered dead if death_date is not null
    df_dead = df_admin.query("death_datetime == death_datetime").assign(
        T=lambda pp: (pp["death_datetime"] - pp["visit_start_datetime"]).apply(
            lambda x: int(x.days)
        ),
        E=lambda pp: 1,
    )

    # censored data: neither death_date nor visit_end_date
    df_not_finished = df_admin.query(
        "death_datetime != death_datetime and visit_end_datetime != visit_end_datetime"
    ).assign(
        T=lambda pp: (
            pd.to_datetime(t_end_of_study) - pp["visit_start_datetime"]
        ).apply(lambda x: int(x.days)),
        E=lambda pp: 0,
    )

    # fully observed livings: if no death_date but non null end_visit_date
    # reminder: we assume that a patient who exit an hospital alive survives at least "max_stay_duration" days
    df_alive = df_admin.query(
        "death_datetime != death_datetime and visit_end_datetime == visit_end_datetime"
    ).assign(
        T=lambda pp: max_stay_duration,
        E=lambda pp: 0,
    )

    # final concatenation
    df_kaplan = pd.concat([df_dead, df_not_finished, df_alive], axis=0)[
        ["T", "E", "drug_source_value"]
    ].rename(columns={"drug_source_value": "group"})
    df_kaplan["T"] = df_kaplan["T"].astype(int)
    return df_kaplan


def plot_primary_kaplan(
    df_person_kaplan,
    list_case,
    t_end_of_study,
):
    """
    Function that displays survival curves computed by the KaplanMeierFitter function from the lifeline package. 
    It compares the drugA and drugB effects to the control cohort.

    Parameters
    ----------
    :param df_person_kaplan: pandas df,
        DataFrame gathering the demographic data about the patients of interest.
        Must have the same structure as the initial `df_person` table (must contain especially `person_id`
        and potential `death_datetime`).
    :param list_case: list of tuples,
        List of studied case for the survival analysis.
        List of tuple (df_visit-pandas df-, df_med-pandas df-, name-str-) having :
            - df_visit : hospitalization DataFrame, with information on entry/exit dates
            - df_med : drug administration DataFrame, must contain ONLY the drugs of interest (i.e epidemic)
            - name : name of the studied case (for visualization purposes)
    :param t_end_of_study: datetime.date,
        Date of the end of the study, i.e after which no information can be trusted (censoring).

    Returns
    -------
    :return: None
        Plots the survival curves built by the Kaplan-Meier estimates.
    """
    fig, axs = plt.subplots(1, 2)
    fig.set_size_inches(10.5, 5.5)

    i = 0
    for df_visit_kaplan, df_med_kaplan, name in list_case:
        df_kaplan = get_df_kaplan(
            df_person_kaplan,
            df_visit_kaplan,
            df_med_kaplan,
            t_end_of_study=t_end_of_study,
        )
        dfA = df_kaplan.query('group=="drugA"')
        dfB = df_kaplan.query('group=="drugB"')
        if i == 0:
            dfc = df_kaplan.query('group=="control"')
            kmf_c.fit(dfc["T"], dfc["E"], label="control")
            kmf_c.plot_survival_function(ax=axs[1])
            kmf_c.plot_survival_function(ax=axs[0])
        kmf.fit(dfA["T"], dfA["E"], label=f"drugA - {name}")
        kmf.plot_survival_function(ax=axs[0])
        add_at_risk_counts(kmf, kmf_c, ax=axs[0], rows_to_show=['At risk'])
        kmf.fit(dfB["T"], dfB["E"], label=f"drugB - {name}")
        kmf.plot_survival_function(ax=axs[1])
        add_at_risk_counts(kmf, kmf_c, ax=axs[1], rows_to_show=['At risk'])

        i += 1

    axs[0].set_title("drugA - all population")
    axs[1].set_title("drugB - all population")
    # resultsA = logrank_test(
    #     dfA["T"], dfc["T"], event_observed_A=dfA["E"], event_observed_B=dfc["E"]
    # )
    # resultsB = logrank_test(
    #     dfB["T"], dfc["T"], event_observed_A=dfB["E"], event_observed_B=dfc["E"]
    # )
    # axs[0].set_title(
    #     f"drugA - all population\nlog-rank test p_value: {round(resultsA.p_value, 3)}"
    # )
    # axs[1].set_title(
    #     f"drugB - all population\nlog-rank test p_value: {round(resultsB.p_value, 3)}"
    # )
    axs[0].set_ylim([0, 1.05])
    axs[1].set_ylim([0, 1.05])
    axs[0].xaxis.set_major_locator(MaxNLocator(integer=True))
    axs[1].xaxis.set_major_locator(MaxNLocator(integer=True))

    for ax in axs.flat:
        ax.set(xlabel="days after admission", ylabel="probability of survival")

    plt.tight_layout()
    plt.show()


def plot_secondary_kaplan(
    df_person_kaplan,
    list_case,
    t_end_of_study,
    drug_name="drugA",
):
    """
    Function that displays survival curves computed by the KaplanMeierFitter function from the lifeline package. 
    Proceeds to a stratified analysis on gender and age, based on a given drug to analyse.

    Parameters
    ----------
    :param df_person_kaplan: pandas df,
        DataFrame gathering the demographic data about the patients of interest.
        Must have the same structure as the initial `df_person` table (must contain especially `person_id`,
        potential `death_datetime`, `birth_datetime` and `gender_source_value`).
    :param list_case: list of tuples,
        List of studied case for the survival analysis.
        List of tuple (df_visit-pandas df-, df_med-pandas df-, name-str-) having :
            - df_visit : hospitalization DataFrame, with information on entry/exit dates
            - df_med : drug administration DataFrame, must contain ONLY the drugs of interest (i.e epidemic)
            - name : name of the studied case (for visualization purposes)
    :param t_end_of_study: datetime.date,
        Date of the end of the study, i.e after which no information can be trusted (for censoring purposes).
    :param drug_name: str,
        Name of the drug on which to perform the stratified analysis.
        Must be in ['drugA', 'drugB']

    Returns
    -------
    :return: None
        Plots the survival curves built by the Kaplan-Meier estimates and stratified by age and gender.
    """
    # controls
    if drug_name not in ["drugA", "drugB"]:
        raise AttributeError(
            f"drug_name: {drug_name} is not among available drug names."
        )

    fig, axs = plt.subplots(4, 2)
    fig.set_size_inches(10.5, 18.5)

    for i, age_range in enumerate([(5, 18), (18, 25), (25, 65), (65, 100)]):
        i_loc = 0
        for df_visit_kaplan, df_med_kaplan, name in list_case:
            dfm = get_df_kaplan(
                df_person_kaplan,
                df_visit_kaplan,
                df_med_kaplan,
                t_end_of_study,
                age_range,
                "m",
            )
            dff = get_df_kaplan(
                df_person_kaplan,
                df_visit_kaplan,
                df_med_kaplan,
                t_end_of_study,
                age_range,
                "f",
            )
            dfmc, dfmA = dfm.query('group=="control"'), dfm.query(
                f'group=="{drug_name}"'
            )
            dffc, dffA = dff.query('group=="control"'), dff.query(
                f'group=="{drug_name}"'
            )
            if i_loc == 0:
                kmf.fit(dffc["T"], dffc["E"], label="control")
                kmf.plot_survival_function(ax=axs[i, 0])
                kmf.fit(dfmc["T"], dfmc["E"], label="control")
                kmf.plot_survival_function(ax=axs[i, 1])
            kmf.fit(dffA["T"], dffA["E"], label=f"{drug_name} - {name}")
            kmf.plot_survival_function(ax=axs[i, 0])
            kmf.fit(dfmA["T"], dfmA["E"], label=f"{drug_name} - {name}")
            kmf.plot_survival_function(ax=axs[i, 1])
            i_loc += 1

        axs[i, 0].set_title(f"{drug_name} - women - age range {age_range}")
        axs[i, 1].set_title(f"{drug_name} - men - age range {age_range}")
        # resultsA = logrank_test(
        #     dffA["T"], dffc["T"], event_observed_A=dffA["E"], event_observed_B=dffc["E"]
        # )
        # resultsB = logrank_test(
        #     dfmA["T"], dfmc["T"], event_observed_A=dfmA["E"], event_observed_B=dfmc["E"]
        # )
        # axs[i, 0].set_title(
        #     f"{drug_name} - women - age range {age_range}\nlog-rank test p_value: {round(resultsA.p_value, 3)}"
        # )
        # axs[i, 1].set_title(
        #     f"{drug_name} - men - age range {age_range}\nlog-rank test p_value: {round(resultsB.p_value, 3)}"
        # )
        axs[i, 0].set_ylim([0, 1.05])
        axs[i, 1].set_ylim([0, 1.05])
        axs[i, 0].xaxis.set_major_locator(MaxNLocator(integer=True))
        axs[i, 1].xaxis.set_major_locator(MaxNLocator(integer=True))

    for ax in axs.flat:
        ax.set(xlabel="days after admission", ylabel="probability of survival")

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    plt.tight_layout()
    plt.show()


def plot_primary_multicase_logranktest(
    df_person_kaplan,
    list_case,
    t_end_of_study,
):
    """
    Displays log-rank test p-values for all cases in list_case for the overall population.

    :param df_person_kaplan: pandas df,
        minimal "person" table (same schema than raw data df)
    :param df_cond_kaplan: pandas df,
        minimal "condition_occurrence" table (same schema than raw data df)
    :param list_case: list of tuples,
        list of (df_visit-pandas df-, df_med-pandas df-, name-str-) to display
    :param t_end_of_study: datetime.date,
        date at which starting to censor data (date after which no information can be trusted).

    :return: None
    """
    dict_pvalues = {"case": [], "pvalue": [], "title": []}
    i_plot = 0
    for df_visit_kaplan, df_med_kaplan, name in list_case:
        df_kaplan = get_df_kaplan(
            df_person_kaplan,
            df_visit_kaplan,
            df_med_kaplan,
            t_end_of_study=t_end_of_study,
        )
        dfA = df_kaplan.query('group=="drugA"')
        dfB = df_kaplan.query('group=="drugB"')
        dfc = df_kaplan.query('group=="control"')
        resultsA = logrank_test(
            dfA["T"],
            dfc["T"],
            event_observed_A=dfA["E"],
            event_observed_B=dfc["E"],
        )
        resultsB = logrank_test(
            dfB["T"],
            dfc["T"],
            event_observed_A=dfB["E"],
            event_observed_B=dfc["E"],
        )
        dict_pvalues["case"].append(name)
        dict_pvalues["pvalue"].append(resultsA.p_value)
        dict_pvalues["title"].append(f"{i_plot}) drugA - all population")
        dict_pvalues["case"].append(name)
        dict_pvalues["pvalue"].append(resultsB.p_value)
        dict_pvalues["title"].append(f"{i_plot + 1}) drugB - all population")

    points = (
        alt.Chart(
            pd.DataFrame(dict_pvalues).rename(
                columns={"title": "log rank test p-values"}
            )
        )
        .mark_point(filled=True, color="black")
        .encode(
            x=alt.X("pvalue:Q", scale=alt.Scale(type="log")),
            y=alt.Y("case:N"),
        )
        .properties(width=180, height=180)
        .facet(facet="log rank test p-values:N", columns=2)
        .resolve_scale(
            x="independent",
            y="independent",
        )
    )
    points.display()


def plot_secondary_multicase_logranktest(
    df_person_kaplan,
    list_case,
    t_end_of_study,
    drug_name="drugA"
):
    """
    Displays log-rank test p-values for all cases in list_case for specific populations (specific age and gender).

    :param df_person_kaplan: pandas df,
        minimal "person" table (same schema than raw data df)
    :param df_cond_kaplan: pandas df,
        minimal "condition_occurrence" table (same schema than raw data df)
    :param list_case: list of tuples,
        list of (df_visit-pandas df-, df_med-pandas df-, name-str-) to display
    :param t_end_of_study,
        date at which starting to censor data (date after which no information can be trusted).
    :param drug_name: str,
        drug on which filter data
    :return: None
    """
    dict_pvalues = {"case": [], "pvalue": [], "title": []}
    i_plot = 0
    for i, age_range in enumerate([(5, 17), (18, 24), (25, 64), (65, 100)]):
        for df_visit_kaplan, df_med_kaplan, name in list_case:
            dfm = get_df_kaplan(
                df_person_kaplan,
                df_visit_kaplan,
                df_med_kaplan,
                t_end_of_study,
                age_range,
                "m",
            )
            dff = get_df_kaplan(
                df_person_kaplan,
                df_visit_kaplan,
                df_med_kaplan,
                t_end_of_study,
                age_range,
                "f",
            )
            dfmc, dfmA = dfm.query('group=="control"'), dfm.query(
                f'group=="{drug_name}"'
            )
            dffc, dffA = dff.query('group=="control"'), dff.query(
                f'group=="{drug_name}"'
            )
            resultsM = logrank_test(
                dffA["T"],
                dffc["T"],
                event_observed_A=dffA["E"],
                event_observed_B=dffc["E"],
            )
            resultsF = logrank_test(
                dfmA["T"],
                dfmc["T"],
                event_observed_A=dfmA["E"],
                event_observed_B=dfmc["E"],
            )
            dict_pvalues["case"].append(f"F {age_range} | {name}")
            dict_pvalues["pvalue"].append(resultsF.p_value)
            dict_pvalues["title"].append(
                f"{i_plot}) {drug_name} - women - age range {age_range}"
            )
            dict_pvalues["case"].append(f"M {age_range} | {name}")
            dict_pvalues["pvalue"].append(resultsM.p_value)
            dict_pvalues["title"].append(
                f"{i_plot + 1}) {drug_name} - men - age range {age_range}"
            )
        i_plot += 2

    points = (
        alt.Chart(
            pd.DataFrame(dict_pvalues).rename(
                columns={"title": "log rank test p-values"}
            )
        )
        .mark_point(filled=True, color="black")
        .encode(
            x=alt.X("pvalue:Q", scale=alt.Scale(type="log")),
            y=alt.Y("case:N"),
        )
        .properties(width=180, height=180)
        .facet(facet="log rank test p-values:N", columns=2)
        .resolve_scale(
            x="independent",
            y="independent",
        )
    )
    points.display()
