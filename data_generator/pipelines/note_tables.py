from .med_tables import gen_med_table
import pandas as pd
import numpy as np
from .utils import *


def gen_nlp_extracted_table(
    df_visit,
    df_person,
    drug_source_value,
    id_generator,
    transco=None,
    deployment_date_per_hospital=None,
    timeliness_date_per_hospital=None,
    proportion=1.0,
):
    """
    Make 'note_nlp' table (based on 'drug_exposure' table but with a renamed schema).

    :param df_visit:
    :param df_person:
    :param drug_source_value: str,
        drug name.
    :param transco: str,
        type of transcoding.
    :param deployment_date_per_hospital: dict,
        date at which data if fully available (5% of missing data compare to 90% before)
    :param timeliness_date_per_hospital: dict,
        date until which data if not made available.
    :param proportion: float,
        ratio of nan "drug_source_value" (between 0 and 1)

    :return:
    df_nlp: pandas.df,
        "note_nlp" table
    df_transco_visit_hard: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med.
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id''])
    df_transco_visit_proba: pandas.df,
        links between "old" and "new" visit_occurrence_id in df_med. 'Prob' is the probability of good linkage.
        (the probability at which the linked visit_occurrence_id is one resulting to death).
        (schema: ['EHR1_visit_id', 'EHRmed_visit_id', 'prob'])
        None if transco=="hard".
    """
    df_nlp, df_nlp_tranco_hard, df_nlp_tranco_proba = gen_med_table(
        df_visit,
        df_person,
        drug_source_value,
        id_generator,
        transco=transco,
        deployment_date_per_hospital=deployment_date_per_hospital,
        timeliness_date_per_hospital=timeliness_date_per_hospital,
        proportion=proportion,
    )
    df_nlp = df_nlp.rename(
        columns={
            "drug_exposure_start_date": "note_datetime",
            "drug_exposure_id": "note_id",
            "drug_source_value": "extracted_concept_source_value",
            "EHRmed_visit_id": "EHRnote_visit_id",
        }
    ).replace({"EHR med": "EHR note"})
    if df_nlp_tranco_hard is not None:
        df_nlp_tranco_hard = df_nlp_tranco_hard.rename(
            columns={"EHRmed_visit_id": "EHRnote_visit_id"}
        )
    if df_nlp_tranco_proba is not None:
        df_nlp_tranco_proba = df_nlp_tranco_proba.rename(
            columns={"EHRmed_visit_id": "EHRnote_visit_id"}
        )

    return df_nlp, df_nlp_tranco_hard, df_nlp_tranco_proba


contextual_sentences = [
    "Le patient est arrivé ce matin.",
    "Le patient est venu accompagné.",
    "Le patient est arrivé via les urgences.",
    "Le patient est connu des services de soins de l'hopital.",
    "Le patient mentionne des douleurs dans le bas du ventre.",
    "Le patient semble etre désorienté.",
    "Vit : seul - avec son conjoint - chez un membre de la famille - entouré par sa famille - en famille d'accueil",
    "Le patient est admis le 29 août pour des difficultés respiratoires.",
    "Le père est asthmatique, sans traitement particulier.",
    "Le patient dit avoir de la toux depuis trois jours. Elle a empiré jusqu'à nécessiter un passage aux urgences.",
    "Le patient a été hospitalisé l'année dernière dans le service de gastro-entérologie.",
    "Le patient a recu un diagnostic de cancer de la tête du pancréas localemetn avancée en Novembre 2020.",
    "Le patient est contient, orienté.",
    "Il ne mentionne pas de douleur thoracique.",
    "Le patient a des nausées et de vomissement depuis avant hier.",
    "Le patient est arrivé au urgence pour diarrhées depuis ce matin.",
    "Le patient est suivi par le docuteur Dupont depuis 2 ans."
    "On note une glycémie à jeun lors de l'admission.",
    "Pas de douleurs abdominales.",
    "Bilan hépatique normal",
    "Pas de nausée ni de vomissement",
]


def note_contextual_bis():
    """
    Make a note with contextual sentences.

    Returns
    -------
    file_content: str
    """
    return np.random.choice(contextual_sentences, 1)[0]


def note_contextual():
    """
    Make a note content full of 'lorem ipsum'.

    Returns
    -------
    file_content: str
    """
    return " ".join(["lorem ipsum\n"] * np.random.randint(1, 20))


def gen_relevant_text(word_list, sentences):
    """
    Make a note content with a sentence in sentences (filled with words in word_list if there are missing words)
    surrounded 'lorem ipsum'.

    Parameters
    ----------
    word_list: list[str],
        list of words to replace in the sentence if a word placeholder is detected.
    sentences: list[str],
        list of available sentences.

    Returns
    -------
    sentence: str
    """
    sentence = np.random.choice(sentences, 1)[0]
    if "{}" in sentence:
        sentence = sentence.format(*np.random.choice(word_list, sentence.count("{}")))
    return sentence


def gen_text(word_list, proportion, sentences):
    """
    Make a note content with a sentence in sentences (filled with words in word_list if there are missing words)
    surrounded 'lorem ipsum'.

    Parameters
    ----------
    word_list: list[str],
        list of words to replace in the sentence if a word placeholder is detected.
    proportion: float,
        ratio of nan "drug_source_value" (between 0 and 1)
    sentences: list[str],
        list of available sentences.

    Returns
    -------
    sentence: str

    """
    text = (
        note_contextual_bis()
        + "\n"
        + gen_relevant_text(word_list, sentences)
        + "\n"
        + note_contextual_bis()
    )
    if proportion == 1:
        return text
    else:
        return np.random.choice([text, np.nan], 1, p=[proportion, 1 - proportion])[0]


def duplicate_note(
    df_note,
    duplicate_note_per_visit_ratio,
    word_list,
    sentences,
    proportion,
    id_generator,
):
    """
    Generate duplicated notes for visits.

    Parameters
    ----------
    df_note
    duplicate_note_per_visit_ratio: flaot,
        ratio of visits with duplicated notes.
    word_list: list[str],
        list of words to replace in the sentence if a word placeholder is detected.
    proportion: float,
        ratio of nan "drug_source_value" (between 0 and 1)
    sentences: list[str],
        list of available sentences.

    Returns
    -------
    df_note with duplicated notes.
    """

    if duplicate_note_per_visit_ratio is not None:
        for n_dup, ratio in duplicate_note_per_visit_ratio.items():
            for _ in range(n_dup - 1):
                df_note_dup = df_note.sample(int(ratio * len(df_note)))
                df_note_dup = df_note_dup.assign(
                    note_id=lambda pp: [
                        id_generator.run("note_id") for _ in range(len(df_note_dup))
                    ]
                ).assign(
                    note_text=lambda pp: [
                        gen_text(word_list, proportion, sentences)
                        for _ in range(len(df_note_dup))
                    ]
                )
                df_note = pd.concat([df_note, df_note_dup], axis=0)
    return df_note


def note_transcoding(df_note, df_transco):
    """
    Use linkage in df_transco to transcode df_note.

    Parameters
    ----------
    df_note
    df_transco

    Returns
    -------
    df_note transcoded.
    """
    return df_note.merge(
        df_transco,
        left_on="visit_occurrence_id",
        right_on="EHR1_visit_id",
        how="inner",
    ).drop(columns=["EHR1_visit_id", "visit_occurrence_id"])


def gen_note_table(
    df_visit,
    word_list,
    sentences,
    id_generator,
    proportion=1.0,
    duplicate_note_per_visit_ratio=None,
    deployment_date_per_hospital=None,
):
    """

    :param df_visit:
    word_list: list[str],
        list of words to replace in the sentence if a word placeholder is detected.
    proportion: float,
        ratio of nan "drug_source_value" (between 0 and 1)
    sentences: list[str],
        list of available sentences.

    :return:
    df_note: pandas.df,
        "note" table
    """

    df_note = (
        df_visit.drop_duplicates()[["visit_occurrence_id", "visit_start_datetime"]]
        .rename(columns={"visit_start_datetime": "note_datetime"})
        .assign(
            note_id=lambda pp: [
                id_generator.run("note_id") for _ in range(len(df_visit))
            ],
            cdm_source=lambda pp: "EHR 1",
            note_text=lambda pp: [
                gen_text(word_list, proportion, sentences) for _ in range(len(df_visit))
            ],
        )
        .assign(note_text=lambda pp: pp["note_text"].replace({"nan": np.nan}))
    )

    if deployment_date_per_hospital:
        df_note = apply_deployment_per_hosp(
            df_note, df_visit, deployment_date_per_hospital
        )

    df_note = duplicate_note(
        df_note,
        duplicate_note_per_visit_ratio,
        word_list,
        sentences,
        proportion,
        id_generator,
    )

    df_note["note_datetime"] = pd.to_datetime(df_note["note_datetime"])

    # Shuffle dataframe to reset order
    df_note = df_note.sample(frac=1).reset_index(drop=True)

    return df_note
