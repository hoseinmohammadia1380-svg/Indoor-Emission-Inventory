
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    return pd.read_csv('Emission_Factors.csv')

df = load_data()

tabs = st.tabs(["Emission Calculator", "Mass Balance Model", "EF Database", "About"])

# --- Tab 1: Emission Calculator ---
with tabs[0]:
    st.header('Indoor Emission Calculator (E = Activity x EF)')

    activities = df['Activity'].unique()
    act = st.selectbox('Select Activity Type:', activities)
    pols = df[df['Activity'] == act]['Pollutant'].unique()
    pol = st.selectbox('Select Pollutant:', pols)

    ef_row = df[(df['Activity'] == act) & (df['Pollutant'] == pol)].iloc[0]
    ef = ef_row['EF']
    unit = ef_row['Unit']
    src = ef_row['Source']

    st.write(f"Emission Factor (EF): {ef} {unit}")

    val = st.number_input('Enter Activity Amount (kg, h, MJ, or J):', min_value=0.0, step=0.1)

    if st.button('Calculate Emission'):
        E_g = None
        u = unit.strip().lower()
        if 'g/kg' in u:
            # amount in kg
            E_g = val * ef
        elif 'ug/j' in u or 'µg/j' in u:
            # amount in J (or MJ), user enters J by default; if MJ, advise conversion
            E_g = val * ef / 1e6  # microgram to gram
        elif 'mg/h' in u:
            # amount is hours
            E_g = val * ef / 1000.0
        elif 'mg/kg' in u:
            # amount in kg
            E_g = val * ef / 1000.0
        else:
            st.warning('Unsupported unit type. Please adjust Activity Amount units to match EF.')

        if E_g is not None:
            st.success(f'Total Emission: {E_g:.6f} g')
            st.caption(f'Source: {src}')

# --- Tab 2: Mass Balance Model ---
with tabs[1]:
    st.header('Mass Balance Model: dC/dt = E/V - (ACH + k)*C')
    V = st.number_input('Room volume (m3):', min_value=0.0, value=50.0)
    ACH = st.number_input('Air changes per hour (ACH):', min_value=0.0, value=1.0)
    k = st.number_input('Deposition/Reaction constant (k, h-1):', min_value=0.0, value=0.0)
    E_in = st.number_input('Emission rate (g/h):', min_value=0.0, value=0.1)
    C0 = st.number_input('Initial concentration (ug/m3):', min_value=0.0, value=0.0)

    if st.button('Simulate Concentration Change'):
        t = np.linspace(0, 8, 200)  # hours
        # convert C0 to g/m3
        C0_g = C0 / 1e6
        lam = ACH + k
        # solution for constant emission E_in: C(t) = (E/V)/lam * (1 - exp(-lam t)) + C0 * exp(-lam t)
        C_g = (E_in / V) / lam * (1 - np.exp(-lam * t)) + C0_g * np.exp(-lam * t) if lam > 0 else C0_g + (E_in/V) * t
        C_ug = C_g * 1e6
        st.line_chart(pd.DataFrame({'Time_h': t, 'Concentration_ug_per_m3': C_ug}))
        st.caption('Assumes well-mixed room, constant emission during simulation period.')

# --- Tab 3: EF Database ---
with tabs[2]:
    st.header('EF Reference Database (searchable)')
    q = st.text_input('Search by activity or pollutant:')
    if q:
        mask = df.apply(lambda r: q.lower() in (str(r['Activity']).lower()+str(r['Pollutant']).lower()+str(r['Source']).lower()), axis=1)
        st.dataframe(df[mask])
    else:
        st.dataframe(df)

# --- Tab 4: About ---
with tabs[3]:
    st.header('About the Indoor Emission Tool')
    st.markdown('This online calculator estimates indoor pollutant emissions using the standard E = Activity x EF model. Data sources: ESSD (2023), Atmosphere (2019), Tehran (2021), Tobacco (2010), PAH (2008).')
