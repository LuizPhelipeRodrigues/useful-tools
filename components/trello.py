import json
import streamlit as st
import pandas as pd
from services.trello import Trello

def render_trello_tab():
    trello_utils = Trello()
    
    st.markdown("**Arquivo(s) JSON do Trello**")
    json_files = st.file_uploader(
        "Selecione o arquivo JSON:",
        accept_multiple_files=True,
        type="json",
        label_visibility="collapsed",
    )

    if not json_files:
        st.stop()
    
    filter_container = st.container(border=True)
    filter_container.markdown('<div><div class="filter-title">🗓 Filtrar por período</div>', unsafe_allow_html=True)
    dates_range = filter_container.date_input(
        "Período",
        value=(),
        format="DD/MM/YYYY",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not dates_range or len(dates_range) != 2:
        filter_container.markdown("""
        <div class="info-box">
            ← Selecione a <strong>data inicial</strong> e a <strong>data final</strong> para filtrar as atividades.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    initial_date, final_date = dates_range

    all_activities: list[dict] = []

    with st.spinner("Processando arquivos…"):
        for json_file in json_files:
            try:
                data = json.load(json_file)
                activities = trello_utils.process_trello_json(data, initial_date, final_date)
                all_activities.extend(activities)
            except Exception as e:
                st.error(f"Erro ao processar **{json_file.name}**: {e}")

    if not all_activities:
        st.warning("Nenhuma atividade encontrada no período selecionado.")
        st.stop()

    df = pd.DataFrame(all_activities)

    total = len(df)
    done = (df["Status"] == "CONCLUÍDO").sum()
    pending = (df["Status"] == "PENDENTE").sum()
    sectors = df["Setor"].nunique()

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card total">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total de atividades</div>
        </div>
        <div class="metric-card done">
            <div class="metric-value">{done}</div>
            <div class="metric-label">Concluídas</div>
        </div>
        <div class="metric-card pending">
            <div class="metric-value">{pending}</div>
            <div class="metric-label">Pendentes</div>
        </div>
        <div class="metric-card sectors">
            <div class="metric-value">{sectors}</div>
            <div class="metric-label">Setores</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2 = st.columns([1, 1])

    with col_f1:
        sector_options = ["Todos"] + sorted (df["Setor"].unique().tolist())
        selected_sector = st.selectbox("Filtrar por setor", sector_options)

    with col_f2:
        status_options = ["Todos"] + sorted(df["Status"].unique().tolist())
        selected_status = st.selectbox("Filtrar por status", status_options)

    df_filtered = df.copy()
    if selected_sector != "Todos":
        df_filtered = df_filtered[df_filtered["Setor"] == selected_sector]
    if selected_status != "Todos":
        df_filtered = df_filtered[df_filtered["Status"] == selected_status]

    st.markdown(f"""
    <div style="font-size:0.8rem; color:#6b7280; margin:0.5rem 0 1rem;">
        Exibindo <strong style="color:#a5b4fc">{len(df_filtered)}</strong> de {total} atividades
    </div>
    """, unsafe_allow_html=True)

    tab_table, tab_cards = st.tabs(["📊 Tabela", "🃏 Cartões"])

    with tab_table:
        st.dataframe(
            df_filtered,
            width='stretch',
            hide_index=True,
            column_config={
                "Data": st.column_config.TextColumn("📅 Data", width="small"),
                "Atividade Realizada": st.column_config.TextColumn("📌 Atividade", width="large"),
                # "Descrição da Atividade": st.column_config.TextColumn("📝 Descrição", width="large"),
                "Setor": st.column_config.TextColumn("🏢 Setor", width="small"),
                "Status": st.column_config.TextColumn("🔖 Status", width="small"),
                "Observação": st.column_config.TextColumn("💬 Observação", width="medium"),
            },
            height=480,
        )

    with tab_cards:
        for _, row in df_filtered.iterrows():
            badge = trello_utils.status_badge(row["Status"])
            with st.expander(f"{row['Atividade Realizada']} - {row['Setor']}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**📅 Data**  \n{row['Data'] or '—'}")
                    st.markdown(f"**🏢 Setor**  \n{row['Setor']}")
                    st.markdown(f"**🔖 Status**")
                    st.markdown(badge, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**📝 Descrição**")
                    # st.markdown(row["Descrição da Atividade"] or "*Sem descrição*")
                    st.markdown(f"**💬 Observação**  \n{row['Observação']}")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    col_d1, col_d2, _ = st.columns(3)

    with col_d1:
        excel_data = trello_utils.to_excel(df_filtered)
        period_str = f"{initial_date.strftime('%d%m%Y')}_a_{final_date.strftime('%d%m%Y')}"
        st.download_button(
            label="⬇️ Baixar Excel",
            data=excel_data,
            file_name=f"trello_atividades_{period_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col_d2:
        csv_data = df_filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Baixar CSV",
            data=csv_data,
            file_name=f"trello_atividades_{period_str}.csv",
            mime="text/csv",
        )