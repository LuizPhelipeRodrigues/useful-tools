import streamlit as st
import pandas as pd
from typing import Final
from components.trello import render_trello_tab
from components.chb_atualizacoes import render_chb_atualizacoes_tab

tabs: Final[list[dict]] = [
    {"tab": "Atualizações do CHB", "render": render_chb_atualizacoes_tab},
    {"tab": "Relatório do Trello", "render": render_trello_tab},
]

with open('assets/style.css') as f:
    css = f.read()

st.set_page_config(
    page_title="Ferramentas Úteis",
    layout="wide",
)

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-header">
    <div class="hero-title">Ferramentas <span>Úteis</span></div>
    <p class="hero-sub">
        Ferramentas de uso para Sistemas
    </p>
</div>
""", unsafe_allow_html=True)

st_tabs = st.tabs([t["tab"] for t in tabs])

for st_tab, tab in zip(st_tabs, tabs):
    with st_tab:
        tab["render"]()