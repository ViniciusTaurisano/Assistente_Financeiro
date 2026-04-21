import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Configuração e Design
st.set_page_config(page_title="Finanças do Casal v4.2", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DB SETUP ---
conn = sqlite3.connect('financeiro_casal.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS categorias (nome TEXT UNIQUE, tipo TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS gastos
             (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, projeto TEXT, categoria TEXT, descricao TEXT, valor REAL)''')
conn.commit()

# --- SIDEBAR E FILTROS ---
with st.sidebar:
    st.title("💍 Gestão Premium")
    menu = st.radio("Navegação:", ["📝 Lançamentos & Edição", "📊 Dashboards"])

    st.divider()
    if menu == "📊 Dashboards":
        st.subheader("🔍 Filtros")
        f_destino = st.multiselect("Destino:", ["Casamento", "Rotina Mensal"], default=["Casamento", "Rotina Mensal"])

        # Filtro de Categoria Contextual
        lista_filtrada = [r[0] for r in c.execute(f"SELECT nome FROM categorias WHERE tipo IN ({','.join(['?']*len(f_destino))})", f_destino).fetchall()]
        f_cat = st.multiselect("Categorias:", lista_filtrada, default=lista_filtrada)

    st.divider()
    # --- GESTÃO DE CATEGORIAS (REINCLUÍDA) ---
    with st.expander("⚙️ Configurar Categorias"):
        st.subheader("Nova")
        n_cat = st.text_input("Nome")
        t_cat = st.selectbox("Tipo:", ["Casamento", "Rotina Mensal"])
        if st.button("Adicionar Categoria"):
            if n_cat:
                try:
                    c.execute("INSERT INTO categorias (nome, tipo) VALUES (?,?)", (n_cat, t_cat))
                    conn.commit()
                    st.rerun()
                except: st.error("Erro ou Categoria já existe.")

        st.divider()
        st.subheader("Remover")
        res_del = c.execute("SELECT nome FROM categorias").fetchall()
        lista_del = [r[0] for r in res_del]
        cat_para_excluir = st.selectbox("Escolha para apagar:", lista_del)
        if st.button("Remover Permanentemente", type="secondary"):
            c.execute("DELETE FROM categorias WHERE nome = ?", (cat_para_excluir,))
            conn.commit()
            st.rerun()

# --- PÁGINA 1: LANÇAMENTOS E EDIÇÃO COMPLETA ---
if menu == "📝 Lançamentos & Edição":
    st.header("📝 Gestão de Registros")

    # 1. NOVO LANÇAMENTO
    with st.expander("➕ Novo Lançamento", expanded=True):
        with st.form("form_novo"):
            c1, c2, c3 = st.columns(3)
            with c1:
                data_l = st.date_input("Data", date.today())
                proj_l = st.selectbox("Destino", ["Casamento", "Rotina Mensal"])
            with c2:
                res_l = c.execute("SELECT nome FROM categorias WHERE tipo = ?", (proj_l,)).fetchall()
                cat_l = st.selectbox("Categoria", [r[0] for r in res_l])
            with c3:
                val_l = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            desc_l = st.text_input("Descrição")
            if st.form_submit_button("Salvar Registro"):
                c.execute("INSERT INTO gastos (data, projeto, categoria, descricao, valor) VALUES (?,?,?,?,?)",
                          (data_l.isoformat(), proj_l, cat_l, desc_l, val_l))
                conn.commit()
                st.success("Salvo com sucesso!")
                st.rerun()

    st.divider()

    # 2. EDIÇÃO E EXCLUSÃO (VISUALIZAÇÃO TOTAL)
    st.subheader("🛠️ Editar ou Remover Itens")
    df_edit = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conn)

    if not df_edit.empty:
        # Seletor com mais contexto para facilitar a busca
        escolha = st.selectbox(
            "Selecione o item para gerenciar:",
            df_edit['id'].tolist(),
            format_func=lambda x: f"ID {x} | {df_edit[df_edit.id==x]['data'].values[0]} | {df_edit[df_edit.id==x]['descricao'].values[0]} | R$ {df_edit[df_edit.id==x]['valor'].values[0]:.2f}"
        )

        # Carrega dados do item selecionado
        item = df_edit[df_edit.id == escolha].iloc[0]

        with st.container(border=True):
            st.write(f"**Editando Registro ID: {escolha}**")
            col_e1, col_e2, col_e3 = st.columns(3)

            with col_e1:
                nova_data = st.date_input("Alterar Data", pd.to_datetime(item['data']))
                novo_proj = st.selectbox("Alterar Destino", ["Casamento", "Rotina Mensal"],
                                         index=0 if item['projeto']=="Casamento" else 1)
            with col_e2:
                # Categoria dinâmica na edição também
                res_ed_cat = c.execute("SELECT nome FROM categorias WHERE tipo = ?", (novo_proj,)).fetchall()
                lista_ed_cat = [r[0] for r in res_ed_cat]
                idx_cat = lista_ed_cat.index(item['categoria']) if item['categoria'] in lista_ed_cat else 0
                nova_cat = st.selectbox("Alterar Categoria", lista_ed_cat, index=idx_cat)
            with col_e3:
                novo_valor = st.number_input("Alterar Valor", value=float(item['valor']), format="%.2f")

            nova_desc = st.text_input("Alterar Descrição", value=item['descricao'])

            ce1, ce2, _ = st.columns([1, 1, 2])
            if ce1.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                c.execute("""UPDATE gastos SET data=?, projeto=?, categoria=?, descricao=?, valor=? WHERE id=?""",
                          (nova_data.isoformat(), novo_proj, nova_cat, nova_desc, novo_valor, escolha))
                conn.commit()
                st.success("Registro atualizado!")
                st.rerun()

            if ce2.button("🗑️ Excluir Permanentemente", type="secondary", use_container_width=True):
                c.execute("DELETE FROM gastos WHERE id=?", (escolha,))
                conn.commit()
                st.warning("Registro excluído!")
                st.rerun()

# --- PÁGINA 2: DASHBOARDS (v4.2 Corrigida) ---
else:
    st.header("📊 Análise Financeira")
    if f_destino and f_cat:
        query = f"SELECT * FROM gastos WHERE projeto IN ({','.join(['?']*len(f_destino))}) AND categoria IN ({','.join(['?']*len(f_cat))})"
        df = pd.read_sql_query(query, conn, params=f_destino + f_cat)
        
        if not df.empty:
            # Tratamento essencial para o gráfico de Evolução
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data') # Ordena por data para a linha fazer sentido
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Gasto Total", f"R$ {df['valor'].sum():,.2f}")
            m2.metric("Nº de Itens", len(df))
            m3.metric("Média por Item", f"R$ {df['valor'].mean():,.2f}")
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💰 Por Categoria")
                st.bar_chart(df.groupby('categoria')['valor'].sum(), color="#d33682")
            
            with c2:
                st.subheader("📈 Evolução dos Gastos")
                # Agrupamos por data para somar gastos do mesmo dia
                evolucao = df.groupby('data')['valor'].sum().reset_index()
                # Definimos a data como índice para o gráfico de linha funcionar corretamente
                evolucao = evolucao.set_index('data')
                st.line_chart(evolucao, y="valor", color="#0077b6")
                
            st.subheader("📋 Relatório Detalhado")
            st.dataframe(df.sort_values('data', ascending=False), use_container_width=True, hide_index=True)
