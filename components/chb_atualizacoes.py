import json
import streamlit as st
import streamlit.components.v1 as components
from services.chb_atualizacoes import CHBAtualizacoes

def render_chb_atualizacoes_tab():
  chb_atualizacoes_utils = CHBAtualizacoes()
  st.session_state.setdefault('alteracoes_chb', '')

  def salvarAlteracoes():
    novas_alteracoes = chb_atualizacoes_utils.parse_updates(atualizacoesDia)
    if not novas_alteracoes:
      return

    if st.session_state['alteracoes_chb']:
      st.session_state['alteracoes_chb'] += "\n" + novas_alteracoes
    else:
      st.session_state['alteracoes_chb'] = novas_alteracoes

  def limparAlteracoes():
    st.session_state['alteracoes_chb'] = ''

  atualizacoesDia = st.text_area(
        "Corpo do e-mail",
    "",
    placeholder="Insira o corpo do e-mail enviado pelo CHB",
    label_visibility="collapsed",
  )

  col_salvar, col_limpar, col_copiar = st.columns(3)

  with col_salvar:
    st.button("Salvar", on_click=salvarAlteracoes)
  with col_limpar:
    st.button("Limpar", on_click=limparAlteracoes)
  with col_copiar:
    copia_habilitada = len(st.session_state.alteracoes_chb) > 0
    components.html(f"""
      <button
        onclick="navigator.clipboard.writeText({json.dumps(st.session_state.alteracoes_chb)})"
        {"disabled" if not copia_habilitada else ""}
        style="width:100%; padding:0.5rem; border-radius:0.5rem; border:1px solid rgba(250,250,250,0.2); background:transparent; cursor:pointer;"
      >Copiar</button>
    """, height=45)

  st.text(st.session_state.alteracoes_chb)