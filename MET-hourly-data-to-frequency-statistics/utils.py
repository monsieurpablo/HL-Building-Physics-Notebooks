import base64

import pandas as pd
import streamlit as st


def hide_streamlit_logo():
    hide_streamlit_logo = """
            <style>
            MainMenu {visibility: visible;}
            footer {visibility: hidden;}
            </style>
            """
    return st.markdown(hide_streamlit_logo, unsafe_allow_html=True)


def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)
