import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date

# Configuração e Design
st.set_page_config(page_title="Gestão Premium", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Ajustado para os nomes exatos dos seus prints: 'gastos' e 'categoria'
    gastos = conn.read(worksheet="gastos", ttl="0")
    categorias = conn.read(worksheet="categoria", ttl="0")
    return gastos.dropna(how="all"), categorias.dropna(how="all")

df_gastos, df_categorias = get_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("💍 Gestão Premium")
    menu = st.radio("Navegação:", ["📝 Lançamentos & Edição", "📊 Dashboards"])

    st.divider()
    
    with st.expander("⚙️ Configurar Categorias"):
        st.subheader("Nova")
        n_cat = st.text_input("Nome da Categoria")
        t_cat = st.selectbox("Vincular a:", ["Casamento", "Rotina Mensal"])
        
        if st.button("Adicionar Categoria"):
            if n_cat:
                if n_cat not in df_categorias['nome'].values:
                    nova_linha = pd.DataFrame([{"nome": n_cat, "tipo": t_cat}])
                    df_cat_updated = pd.concat([df_categorias, nova_linha], ignore_index=True)
                    conn.update(worksheet="categoria", data=df_cat_updated)
                    st.success("Categoria adicionada!")
                    st.rerun()
                else:
                    st.error("Esta categoria já existe!")

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
                # Filtragem inteligente de categorias
                if not df_categorias.empty:
                    cats_filtradas = df_categorias[df_categorias['tipo'] == proj_l]['nome'].tolist()
                    cat_l = st.selectbox("Categoria", cats_filtradas if cats_filtradas else ["Cadastre uma categoria"])
                else:
                    cat_l = st.selectbox("Categoria", ["Nenhuma categoria encontrada"])
            with c3:
                val_l = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            desc_l = st.text_input("Descrição")
            
            if st.form_submit_button("Salvar Registro"):
                # Usei 'descricao' sem o 'til' para bater com seu print da planilha
                novo_id = int(pd.Timestamp.now().timestamp())
                novo_gasto = pd.DataFrame([{
                    "id": novo_id, "data": data_l.isoformat(), "projeto": proj_l, 
                    "categoria": cat_l, "descricao": desc_l, "valor": val_l
                }])
                df_gastos_updated = pd.concat([df_gastos, novo_gasto], ignore_index=True)
                conn.update(worksheet="gastos", data=df_gastos_updated)
                st.success("Salvo com sucesso!")
                st.rerun()

    # --- EDIÇÃO / EXCLUSÃO ---
    st.divider()
    st.subheader("🛠️ Editar ou Remover Itens")
    if not df_gastos.empty:
        df_display = df_gastos.sort_values('data', ascending=False)
        escolha_id = st.selectbox(
            "Selecione o lançamento:",
            df_display['id'].tolist(),
            format_func=lambda x: f"ID {x} | {df_display[df_display.id==x]['data'].values[0]} | R$ {df_display[df_display.id==x]['valor'].values[0]}"
        )
        
        item = df_gastos[df_gastos.id == escolha_id].iloc[0]
        
        with st.container(border=True):
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                n_data = st.date_input("Data", pd.to_datetime(item['data']))
                n_proj = st.selectbox("Destino ", ["Casamento", "Rotina Mensal"], index=0 if item['projeto']=="Casamento" else 1)
            with col_e2:
                n_cats = df_categorias[df_categorias['tipo'] == n_proj]['nome'].tolist()
                n_cat = st.selectbox("Categoria ", n_cats, index=n_cats.index(item['categoria']) if item['categoria'] in n_cats else 0)
            with col_e3:
                n_val = st.number_input("Valor ", value=float(item['valor']), format="%.2f")
            
            n_desc = st.text_input("Descrição ", value=item['descricao'])
            
            b1, b2, _ = st.columns([1,1,2])
            if b1.button("💾 Atualizar"):
                df_gastos.loc[df_gastos.id == escolha_id, ['data', 'projeto', 'categoria', 'descricao', 'valor']] = [n_data.isoformat(), n_proj, n_cat, n_desc, n_val]
                conn.update(worksheet="gastos", data=df_gastos)
                st.success("Atualizado!")
                st.rerun()
            
            if b2.button("🗑️ Excluir"):
                df_gastos_updated = df_gastos[df_gastos.id != escolha_id]
                conn.update(worksheet="gastos", data=df_gastos_updated)
                st.warning("Excluído!")
                st.rerun()

# --- PÁGINA 2: DASHBOARDS ---
else:
    st.header("📊 Dashboards")
    if not df_gastos.empty:
        df = df_gastos.copy()
        df['data'] = pd.to_datetime(df['data'])
        
        m1, m2 = st.columns(2)
        m1.metric("Gasto Total", f"R$ {df['valor'].sum():,.2f}")
        m2.metric("Lançamentos", len(df))
        
        st.bar_chart(df.groupby('categoria')['valor'].sum())
    else:
        st.info("Nenhum dado para exibir no Dashboard.")
