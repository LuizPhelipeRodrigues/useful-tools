import pyperclip
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

  def copiarAtualizacoes():
    pyperclip.copy(st.session_state['alteracoes_chb'])
  
  atualizacoesDia = st.text_area(
        "Corpo do e-mail",
    "",
    placeholder="Insira o corpo do e-mail enviado pelo CHB",
    label_visibility="collapsed",
  )

  with st.container(border=True, vertical_alignment='center', horizontal_alignment='center'):
    copia_habilitada = len(st.session_state.alteracoes_chb) > 0
    _, button_columns_left, button_columns_mid, button_columns_right, _ = st.columns(
      [3, 1, 1, 1, 3], vertical_alignment='center'
    )

    with button_columns_left:
      st.button(
        "Salvar",
        width="stretch",
        on_click=salvarAlteracoes,
        )
    with button_columns_mid:
      st.button(
        "Limpar",
        width="stretch",
        on_click=limparAlteracoes,
        disabled=not copia_habilitada,
        )
    with button_columns_right:
      st.button(
        "Copiar",
        width="stretch",
        on_click=copiarAtualizacoes,
        disabled=not copia_habilitada,
      )

  st.text(st.session_state.alteracoes_chb)