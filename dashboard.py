import streamlit as st
import pandas as pd
from scipy.stats import norm
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# Nastavení hesla
APP_PASSWORD = "5p3n9pg"

def check_password():
    """Funkce pro ověření hesla."""
    st.sidebar.header("Přihlášení")
    password = st.sidebar.text_input("Zadejte heslo:", type="password")
    if password == APP_PASSWORD:
        return True
    elif password:
        st.sidebar.error("Nesprávné heslo.")
    return False

def calculate_95ci(series):
    """Vypočítá 95% interval spolehlivosti pro daný pandas Series."""
    n = series.count()
    mean = series.mean()
    std = series.std()
    if n > 1:
        ci = norm.ppf(0.975) * std / np.sqrt(n)
        lower_bound = mean - ci
        upper_bound = mean + ci
        return mean, lower_bound, upper_bound
    else:
        return mean, None, None

if check_password():
    data = pd.read_csv("https://drive.google.com/uc?id=1eML31iQWPXUyBehx9B25imjpbc3j3E-Y", delimiter=";")

    # Seznam rolí a zařízení
    roles = [
        "Lékař", "Sestra", "Psychosociální pracovník", "Psycholog", "Fyzioterapeut",
        "Duchovní", "Ošetřovatel", "Dobrovolník", "Manažer", "Jiné"
    ]
    role_columns = [f"1. Jakou roli v paliativním týmu zastáváte? (choice={role})" for role in roles]
    facility_column = "2. V jakém typu zařízení paliativní péče pracujete (nejvíce)?"

    # Filtrování dle výběru rolí a typu zařízení
    st.sidebar.header("Filtr")
    selected_roles = st.sidebar.multiselect("Vyberte roli v týmu", roles)
    selected_facilities = st.sidebar.multiselect("Vyberte zařízení", data[facility_column].unique())

    # Filtr dat
    filtered_data = data.copy()

    # Filtrace podle rolí
    if selected_roles:
        selected_role_columns = [
            f"1. Jakou roli v paliativním týmu zastáváte? (choice={role})" for role in selected_roles
        ]
        role_filter = filtered_data[selected_role_columns].eq("Checked").any(axis=1)
        filtered_data = filtered_data[role_filter]

    # Filtrace podle zařízení
    if selected_facilities:
        filtered_data = filtered_data[filtered_data[facility_column].isin(selected_facilities)]

    # Rozdělení na "Vybráno" a "Ostatní"
    data["Vybráno"] = data.index.isin(filtered_data.index)
    selected_data = data[data["Vybráno"]]
    other_data = data[~data["Vybráno"]]

    # Funkce pro výpočet tabulky
    def calculate_summary_table(columns, selected_data, other_data):
        """Vytvoří tabulku s průměrnými hodnotami, 95% CI a počtem případů (n)."""
        summary = pd.DataFrame({
            "Možnosti/Rizika": columns,
            "Vybráno (průměr ± 95% CI, n)": [
                f"{round(mean, 2)} ({round(lower, 2)} - {round(upper, 2)}) n = {n}"
                if lower is not None and upper is not None else f"{round(mean, 2)} (N/A - N/A) n = {n}"
                for mean, lower, upper, n in (
                    (calculate_95ci(selected_data[col]) + (selected_data[col].count(),)) for col in columns
                )
            ],
            "Ostatní (průměr ± 95% CI, n)": [
                f"{round(mean, 2)} ({round(lower, 2)} - {round(upper, 2)}) n = {n}"
                if lower is not None and upper is not None else f"{round(mean, 2)} (N/A - N/A) n = {n}"
                for mean, lower, upper, n in (
                    (calculate_95ci(other_data[col]) + (other_data[col].count(),)) for col in columns
                )
            ],
        })
        return summary

    # Definice sloupců
    option_columns = [
        "Zlepšuje sebeobsluhu pacienta", "Pomáhá snižovat pacientovu bolest", "Snižuje pacientovu dušnost",
        "Pomáhá působit preventivně proti vzniku komplikací péče (pády, kožní defekty, vznik kontraktur, etc.)",
        "Působí preventivně proti vzniku dalších komorbidit vyplývajících z onemocnění pacienta",
        "Pomáhá pacientovi s prognostickým uvědoměním", "Zlepšuje psychický stav pacienta",
        "Při přeložení pacienta do jiného zařízení pomáhá s předáním informací o stavu a potřebách pacienta",
        "Pomáhá pacientovi a rodině nastavit alternativní způsoby komunikace v případě zhoršení schopnosti mluvit",
        "Pomáhá pacientovi s relaxací, zklidněním",
        "Pomáhá pacientovi pomocí nastavených aktivit v průběhu dne s orientací v čase",
        "Pomáhá pacientovi po spirituální stránce",
        "Může edukovat ostatní členy paliativních týmů v možnostech zapojení rehabilitace do PP"
    ]
    risk_columns = [
        "Vznik falešné naděje u paliativních pacientů", "Zvýšení únavy pacienta", "Pozátěžové zhoršení stavu pacienta",
        "Nedostatečná znalost komunikace v paliativní péči", "Nízký efekt fyzioterapeutické intervence u paliativních pacientů ",
        "Vznik (zvýšení rizika)  zranění při rehabilitaci u paliativních pacientů",
        "Účast další osoby se setká s nevolí pacienta či pečujících"
    ]

    # Výpočet tabulek
    options_table = calculate_summary_table(option_columns, selected_data, other_data)
    risks_table = calculate_summary_table(risk_columns, selected_data, other_data)



    # Funkce pro vytvoření grafu
    def create_stacked_bar_chart(data, columns, title):
        # Výpočet proporcí pro jednotlivé hodnoty (1 až 10)
        proportions = {
            value: (data[columns] == value).mean() for value in range(1, 11)
        }

        # Inicializace grafu
        fig = go.Figure()


        # Funkce pro generování přechodové škály
        def interpolate_colors(color1, color2, n):
            """
            Interpoluje `n` barev mezi `color1` a `color2`.
            """
            cmap = plt.get_cmap("viridis")  # Vybereme např. viridis nebo vytvoříme vlastní
            return [
                f"rgba({int(c[0] * 255)}, {int(c[1] * 255)}, {int(c[2] * 255)}, {c[3]})"
                for c in cmap([i / (n - 1) for i in range(n)])
            ]

        # Vlastní barvy (přechod od zlaté do tmavě zelené)
        start_color = "#FFD700"  # Zlatá
        end_color = "#006400"  # Tmavě zelená

        # Generování barevné škály
        colors = interpolate_colors(start_color, end_color, 10)


        # Hodnoty 1 až 5 (nalevo)
        for value in [5, 4, 3, 2, 1]:
            fig.add_trace(go.Bar(
                x=-proportions[value] * 100,  # Na zápornou osu
                y=columns,
                orientation="h",
                marker=dict(color=colors[value - 1]),  # Barva podle indexu
                name="1 nejméně" if value == 1 else None,  # Legenda pro 1
                showlegend=value == 1,
                hovertemplate="Hodnota: %{customdata:.1f}%",
                customdata=proportions[value] * 100  # Pro tooltip
            ))

        # Hodnoty 6 až 10 (napravo)
        for value in range(6, 11):
            fig.add_trace(go.Bar(
                x=proportions[value] * 100,  # Na kladnou osu
                y=columns,
                orientation="h",
                marker=dict(color=colors[value - 1]),  # Barva podle indexu
                name="10 nejvíce" if value == 10 else None,  # Legenda pro 10,
                showlegend=value == 10,
                hovertemplate="Hodnota: %{customdata:.1f}%",
                customdata=proportions[value] * 100  # Pro tooltip
            ))

        # Aktualizace vzhledu grafu
        fig.update_layout(
            title=title,
            barmode="relative",  # Stacked kolem středu
            xaxis=dict(
                title="Podíl odpovědí (%)",
                tickformat=".0f",  # Bez desetinných míst
                range=[-50, 50]  # Rozsah osy
            ),
            yaxis=dict(title=""),
            legend=dict(
                orientation="h",  # Horizontální legenda
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            height=600,  # Výška grafu
            width=1200  # Šířka grafu
        )
        return fig

    # Možnosti a rizika
    option_columns = [
        "Zlepšuje sebeobsluhu pacienta", "Pomáhá snižovat pacientovu bolest", "Snižuje pacientovu dušnost",
        "Pomáhá působit preventivně proti vzniku komplikací péče (pády, kožní defekty, vznik kontraktur, etc.)",
        "Působí preventivně proti vzniku dalších komorbidit vyplývajících z onemocnění pacienta",
        "Pomáhá pacientovi s prognostickým uvědoměním", "Zlepšuje psychický stav pacienta",
        "Při přeložení pacienta do jiného zařízení pomáhá s předáním informací o stavu a potřebách pacienta",
        "Pomáhá pacientovi a rodině nastavit alternativní způsoby komunikace v případě zhoršení schopnosti mluvit",
        "Pomáhá pacientovi s relaxací, zklidněním",
        "Pomáhá pacientovi pomocí nastavených aktivit v průběhu dne s orientací v čase",
        "Pomáhá pacientovi po spirituální stránce",
        "Může edukovat ostatní členy paliativních týmů v možnostech zapojení rehabilitace do PP"
    ]
    risk_columns = [
        "Vznik falešné naděje u paliativních pacientů", "Zvýšení únavy pacienta", "Pozátěžové zhoršení stavu pacienta",
        "Nedostatečná znalost komunikace v paliativní péči", "Nízký efekt fyzioterapeutické intervence u paliativních pacientů ",
        "Vznik (zvýšení rizika)  zranění při rehabilitaci u paliativních pacientů",
        "Účast další osoby se setká s nevolí pacienta či pečujících"
    ]

    # Vizualizace
    st.header("Fyzioterapie v paliativní péči")

    st.subheader("Možnosti")
    st.plotly_chart(create_stacked_bar_chart(filtered_data, option_columns, "Možnosti"))

    st.subheader("Možnosti")
    st.table(options_table)

    st.subheader("Rizika")
    st.plotly_chart(create_stacked_bar_chart(filtered_data, risk_columns, "Rizika"))
    st.subheader("Rizika")
    st.table(risks_table)
