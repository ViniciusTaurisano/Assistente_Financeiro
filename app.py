import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuração da página
st.set_page_config(page_title="Finanças do Casal v5.0", layout="wide")

# 2. Estilização personalizada
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialização de dados (Substituindo o Banco de Dados por Session State)
if 'df_gastos' not in st.session_state:
    st.session_state.df_gastos = pd.DataFrame([
        {"id": 1, "data": "2024-04-20", "projeto": "Casamento", "categoria": "Buffet", "descricao": "Entrada Buffet", "valor": 5000.00},
        {"id": 2, "data": "2024-04-21", "projeto": "Rotina Mensal", "categoria": "Aluguel", "descricao": "Parcela Abril", "valor": 2500.00}
    ])

if 'df_categorias' not in st.session_state:
    st.session_state.df_categorias = pd.DataFrame([
        {"nome": "Buffet", "tipo": "Casamento"},
        {"nome": "Decoração", "tipo": "Casamento"},
        {"nome": "Aluguel", "tipo": "Rotina Mensal"},
        {"nome": "Mercado", "tipo": "Rotina Mensal"}
    ])

# Atalhos para facilitar o uso no código
df_gastos = st.session_state.df_gastos
df_categorias = st.session_state.df_categorias

# --- SIDEBAR ---
with st.sidebar:
    st.title("💍 Gestão Premium")
    menu = st.radio("Navegação:", ["📝 Lançamentos & Edição", "📊 Dashboards"])

    st.divider()
    
    with st.expander("⚙️ Configurar Categorias"):
        st.subheader("Nova")
        n_cat = st.text_input("Nome da Categoria")
        t_cat = st.selectbox("Tipo:", ["Casamento", "Rotina Mensal"])
        
        if st.button("Adicionar Categoria"):
            if n_cat:
                nova_linha = pd.DataFrame([{"nome": n_cat, "tipo": t_cat}])
                st.session_state.df_categorias = pd.concat([st.session_state.df_categorias, nova_linha], ignore_index=True)
                st.success("Categoria adicionada localmente!")
                st.rerun()

# --- PÁGINA 1: LANÇAMENTOS & EDIÇÃO ---
if menu == "📝 Lançamentos & Edição":
    st.header("📝 Gestão de Registros")

    with st.expander("➕ Novo Lançamento", expanded=True):
        with st.form("form_novo"):
            c1, c2, c3 = st.columns(3)
            with c1:
                data_l = st.date_input("Data", date.today())
                proj_l = st.selectbox("Destino", ["Casamento", "Rotina Mensal"])
            with c2:
                cats_disponiveis = df_categorias[df_categorias['tipo'] == proj_l]['nome'].tolist()
                cat_l = st.selectbox("Categoria", cats_disponiveis if cats_disponiveis else ["Geral"])
            with c3:
                val_l = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            desc_l = st.text_input("Descrição")
            
            if st.form_submit_button("Salvar Registro"):
                novo_id = int(pd.Timestamp.now().timestamp())
                novo_gasto = pd.DataFrame([{
                    "id": novo_id, "data": data_l.isoformat(), "projeto": proj_l, 
                    "categoria": cat_l, "descricao": desc_l, "valor": val_l
                }])
                st.session_state.df_gastos = pd.concat([st.session_state.df_gastos, novo_gasto], ignore_index=True)
                st.success("Gasto salvo na memória!")
                st.rerun()

    st.divider()
    st.subheader("🛠️ Visualização dos Itens")
    st.dataframe(df_gastos, use_container_width=True)

# --- PÁGINA 2: DASHBOARDS ---
else:
    st.header("📊 Análise Financeira")
    f_destino = st.multiselect("Filtrar Destino:", ["Casamento", "Rotina Mensal"], default=["Casamento", "Rotina Mensal"])
    
    if not df_gastos.empty:
        df = df_gastos[df_gastos['projeto'].isin(f_destino)].copy()
        df['data'] = pd.to_datetime(df['data'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gasto Total", f"R$ {df['valor'].sum():,.2f}")
        m2.metric("Nº de Itens", len(df))
        m3.metric("Média", f"R$ {df['valor'].mean():,.2f}")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💰 Por Categoria")
            chart_data = df.groupby('categoria')['valor'].sum()
            st.bar_chart(chart_data)
        with c2:
            st.subheader("📈 Evolução")
            evolucao = df.groupby('data')['valor'].sum()
            st.line_chart(evolucao)
