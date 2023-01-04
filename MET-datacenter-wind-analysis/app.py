import shutil

import numpy as np
import openpyxl
import pandas as pd
import streamlit as st
from PIL import Image

import utils


@st.experimental_memo
def read_data(WEATHER_DATA):
    # Read data from the excel file
    df = pd.read_excel(WEATHER_DATA, skiprows=10, header=0)
    # rename columns
    df.columns = ["date", "air_temp", "wet_temp", "rel_hum", "wind_speed", "wind_dir"]
    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])
    # drop rows with NaN values on wind_dir
    df = df.dropna(subset=["wind_dir"])
    return df


def calc_wind_dir_bin(df, wind_dir_step_deg=30):
    # normalize wind directions to 8
    wind_dirs = np.arange(0, 361, wind_dir_step_deg)
    df["norm_dir"] = df["wind_dir"].apply(lambda row: take_closest(wind_dirs, row))
    # replace 360 with 0
    df["norm_dir"] = df["norm_dir"].apply(lambda row: 0 if row == 360 else row)
    # df.head()
    return df


def calc_by_filtering_wind(df, WIND_QUANTILE):

    wind_sel_percentile = df.groupby("norm_dir").quantile(WIND_QUANTILE).wind_speed
    air_temp_1h_percentile = {}

    # for each wind direction
    for dir in sorted(df["norm_dir"].unique()):

        # filter data by direction
        seldf = df[df["norm_dir"] == dir]

        # filter data by wind speed
        sel_wind = seldf[seldf["wind_speed"] > wind_sel_percentile[dir]]
        sel_wind = sel_wind.sort_values("air_temp", ascending=False)

        # take the highest 20th value (1h occurrance in 20yeas)
        air_temp_likelihood = sel_wind.reset_index().take([19]).air_temp.values[0]

        # add to the dictionary
        air_temp_1h_percentile[dir] = air_temp_likelihood

    # Create a dataframe with wind_sel_percentile and air_temp_1h_percentile
    df_wind = pd.DataFrame.from_dict(air_temp_1h_percentile, orient="index", columns=["air_temp_1h_occurrence"])
    df_wind[f"wind_speed_{(WIND_QUANTILE * 100)}percentile"] = wind_sel_percentile
    # reverse column order
    df_wind = df_wind.iloc[:, ::-1]
    return df_wind


def calc_by_filtering_temp(df, TEMP_QUANTILE):
    temp_sel_quantile = df.groupby("norm_dir").quantile(TEMP_QUANTILE).air_temp.round(1)
    wind_speed_likelihood_dic = {}

    # for each wind direction
    for dir in sorted(df["norm_dir"].unique()):

        # filter data by direction
        seldf = df[df["norm_dir"] == dir]

        # filter data by temperature
        temp_quantile = seldf[seldf["air_temp"] > temp_sel_quantile[dir]]
        temp_quantile = temp_quantile.sort_values("wind_speed", ascending=False)

        # take the highest 20th value (1h occurrance in 20years)
        wind_speed_likelihood = temp_quantile.reset_index().take([19]).wind_speed.values[0]

        # add to the dictionary
        wind_speed_likelihood_dic[dir] = wind_speed_likelihood

        # Create a dataframe with wind_sel_percentile and air_temp_1h_percentile
    df_temp = pd.DataFrame.from_dict(wind_speed_likelihood_dic, orient="index", columns=["wind_speed_1h_occurrence"])
    df_temp[f"air_temp_{(TEMP_QUANTILE * 100)}_percentile"] = temp_sel_quantile
    return df_temp


@st.experimental_memo
def df2csv(df):
    return df.to_csv(index=True).encode("utf-8")


st.set_page_config(
    layout="wide",  # "centered", "wide"
    initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
    page_title="HL | MET Office Post-processing",
    page_icon="https://i.imgur.com/BKCC4TZ.png",
)

# apply custom css
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# session state
ss = st.session_state

# SIDEBAR

with st.sidebar as sidebar:

    image = Image.open("assets/1200px-Hoare_Lea_logo.svg_dark.png")

    st.image(
        image,
        use_column_width=False,
        width=200,
    )

    st.title("Parameters")

    # create a form with the parameters
    with st.form("parametres"):
        WIND_DIR_STEP_DEG = st.number_input(
            "Wind Direction Step (deg)", min_value=0, max_value=360, value=30, step=1, key="sel_wind_dir_step"
        )

        WIND_SPEED_PERCENTILE = st.number_input(
            "Wind Speed Percentile",
            min_value=0.0,
            max_value=100.0,
            value=90.0,
            step=0.1,
            key="wind_speed_percentile",
        )
        TEMPERATURE_PERCENTILE = st.number_input(
            "Temperature Percentile",
            min_value=0.0,
            max_value=100.0,
            value=99.6,
            step=0.1,
            key="temp_percentile",
        )

        submit_button = st.form_submit_button(
            label="Submit",
        )

        if submit_button:
            st.experimental_rerun()

body_container = st.container()

with body_container:
    # create an upload button in streamlit

    st.title("Wind Frequency Analysis")

    title_html = (
        '<p style="font-family:Roboto Slab; color:Black; font-size: 15px; text-align: left;">Pablo Arango | 2023</p>'
    )
    st.markdown(title_html, unsafe_allow_html=True)
    st.write("---")

    bodycol1, bodycol2 = st.columns(2)

    with bodycol1:
        st.write(
            """
            **This app process the RAW year hourly date from the MET office into an analysis of percentiles based on Wind Speed and Outdoor Temperature.**
            
            This assumes a file with 20 years of hourly data. The 1h occurrence is calculated taking the 20th highest value for each wind direction.
            
            Upload a weather data file in the excel format provided by the MET office. A sample file can be downloaded below.
            """
        )

        st.write("")

        # Extra - Download sample file
        with open("data/20-Year-Data-Northolt.xlsx", "rb") as my_file:
            st.download_button(
                label="Download Sample RAW Wind Data",
                data=my_file,
                file_name="example-RAW-MET-office-data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with bodycol2:
        WEATHER_DATA = st.file_uploader("Upload Annual Weather File", type=["xlsx"], key="weather_data")
        TEMPLATE_FILE = "data/Template_WFA.xlsx"

        if ss["weather_data"] is None:
            st.warning("Please upload a file")
        else:
            st.success("File uploaded successfully")

        st.write("After uploading the file, click on the Process Data button to create the output file")

        run = st.button("Process Data")

st.write("---")


# @st.experimental_memo
def process_data(WEATHER_DATA):
    df = read_data(WEATHER_DATA)

    # ----------------- CALCULATE WIND DIR BIN -----------------
    wind_dirs = np.arange(0, 361, int(ss["sel_wind_dir_step"]))
    df["norm_dir"] = df["wind_dir"].apply(lambda row: utils.take_closest(wind_dirs, row))
    # replace 360 with 0
    df["norm_dir"] = df["norm_dir"].apply(lambda row: 0 if row == 360 else row)

    # st.dataframe(df)

    df_wind = calc_by_filtering_wind(df, ss["wind_speed_percentile"] / 100)
    df_temp = calc_by_filtering_temp(df, ss["temp_percentile"] / 100)

    return df, df_wind, df_temp


calc_done = False

if (run == True) and (WEATHER_DATA is not None):
    # ----------------- PROCESS DATA -----------------
    df, df_wind, df_temp = process_data(WEATHER_DATA)
    calc_done = True


if calc_done:
    # create 2 columns with the wind speed and temperature percentiles
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### Filtered by Wind Speed")
        st.dataframe(df_wind.style.format("{:.1f}"), use_container_width=True, height=450)
        st.download_button(
            "Download",
            df2csv(df_wind),
            "percentiles_filter_by_windspeed.csv",
            "text/csv",
        )

    with col2:
        st.write("#### Filtered by Temperature")
        st.dataframe(df_temp.style.format("{:.1f}"), use_container_width=True, height=450)
        st.download_button(
            "Download",
            df2csv(df_temp),
            "percentiles_filter_by_temperature.csv",
            "text/csv",
        )


utils.hide_streamlit_logo()
