import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="CRM Gas Stations", 
    layout="wide",
    page_icon="⛽"
)
st.title("⛽ CRM – Gas Stations")

# -----------------------------
# BANCO DE DADOS
# -----------------------------
def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                status TEXT DEFAULT 'Lead',
                stage TEXT DEFAULT 'Pre-sale',
                monthly_fee REAL DEFAULT 0.0,
                next_payment TEXT,
                payment_status TEXT DEFAULT 'Pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trigger para atualizar updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_client_timestamp 
            AFTER UPDATE ON clients
            BEGIN
                UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar banco de dados: {e}")
        return False

init_db()

# -----------------------------
# FUNÇÕES PARA MANIPULAR CLIENTES
# -----------------------------
def load_clients():
    """Carrega todos os clientes do banco de dados"""
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        df = pd.read_sql("SELECT * FROM clients ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")
        return pd.DataFrame()

def add_client(name, contact, status, stage, monthly_fee, next_payment, payment_status, notes):
    """Adiciona um novo cliente ao banco de dados"""
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clients (name, contact, status, stage, monthly_fee, next_payment, payment_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name.strip(), contact, status, stage, monthly_fee, str(next_payment), payment_status, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar cliente: {e}")
        return False

def update_client(client_id, status, stage, next_payment, payment_status):
    """Atualiza os dados de um cliente existente"""
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE clients
            SET status=?, stage=?, next_payment=?, payment_status=?
            WHERE id=?
        ''', (status, stage, str(next_payment), payment_status, client_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar cliente: {e}")
        return False

def delete_client(client_id):
    """Remove um cliente do banco de dados"""
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id=?', (client_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar cliente: {e}")
        return False

# -----------------------------
# SIDEBAR - FILTROS E ESTATÍSTICAS
# -----------------------------
with st.sidebar:
    st.header("📊 Dashboard")
    
    df = load_clients()
    
    if not df.empty:
        # Estatísticas rápidas
        total_clients = len(df)
        active_clients = len(df[df['status'] == 'Client'])
        total_revenue = df['monthly_fee'].sum()
        
        st.metric("Total de Clientes", total_clients)
        st.metric("Clientes Ativos", active_clients)
        st.metric("Receita Mensal Total", f"R$ {total_revenue:,.2f}")
        
        # Filtros
        st.subheader("🔍 Filtros")
        filter_status = st.selectbox("Status", ["Todos"] + df['status'].unique().tolist())
        filter_stage = st.selectbox("Estágio", ["Todos"] + df['stage'].unique().tolist())
        
        # Aplicar filtros
        if filter_status != "Todos":
            df = df[df['status'] == filter_status]
        if filter_stage != "Todos":
            df = df[df['stage'] == filter_stage]

# -----------------------------
# FORMULÁRIO PARA ADICIONAR CLIENTE
# -----------------------------
with st.expander("➕ Adicionar Novo Cliente", expanded=False):
    with st.form("add_client_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome do Cliente *", placeholder="Nome completo ou razão social")
            contact = st.text_input("Contato *", placeholder="Email ou telefone")
            status = st.selectbox("Status *", ["Lead", "Client"])
            stage = st.selectbox("Estágio *", ["Pre-sale", "Implementation", "Post-sale"])
            
        with col2:
            monthly_fee = st.number_input("Taxa Mensal (R$) *", min_value=0.0, step=100.0, value=0.0)
            next_payment = st.date_input("Próximo Pagamento *", value=datetime.today())
            payment_status = st.selectbox("Status do Pagamento *", ["Pending", "Paid", "Overdue"])
            notes = st.text_area("Observações", placeholder="Notas adicionais...")
        
        submitted = st.form_submit_button("✅ Adicionar Cliente")
        
        if submitted:
            if name.strip() and contact.strip():
                success = add_client(name, contact, status, stage, monthly_fee, next_payment, payment_status, notes)
                if success:
                    st.success(f"Cliente {name} adicionado com sucesso!")
                    st.rerun()
            else:
                st.error("Por favor, preencha pelo menos o nome e contato do cliente.")

# -----------------------------
# EXIBIR CLIENTES
# -----------------------------
st.subheader("📋 Lista de Clientes")

if not df.empty:
    # Formatar a exibição dos dados
    display_df = df.copy()
    display_df['monthly_fee'] = display_df['monthly_fee'].apply(lambda x: f"R$ {x:,.2f}")
    
    # Selecionar colunas para exibir
    columns_to_display = ['id', 'name', 'contact', 'status', 'stage', 'monthly_fee', 'next_payment', 'payment_status']
    
    st.dataframe(
        display_df[columns_to_display],
        use_container_width=True,
        hide_index=True
    )
    
    # -----------------------------
    # ATUALIZAR CLIENTE
    # -----------------------------
    with st.expander("✏️ Editar Cliente", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            client_ids = df['id'].tolist()
            selected_id = st.selectbox("Selecionar Cliente por ID", client_ids)
        
        if selected_id:
            with col2:
                row = df[df['id'] == selected_id].iloc[0]
                
                # Botão de deletar
                if st.button("🗑️ Deletar Cliente", type="secondary"):
                    if delete_client(selected_id):
                        st.success("Cliente deletado com sucesso!")
                        st.rerun()
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                new_status = st.selectbox(
                    "Status", 
                    ["Lead", "Client"], 
                    index=0 if row['status'] == "Lead" else 1,
                    key="status_edit"
                )
                
            with col4:
                new_stage = st.selectbox(
                    "Estágio", 
                    ["Pre-sale", "Implementation", "Post-sale"], 
                    index=["Pre-sale", "Implementation", "Post-sale"].index(row['stage']),
                    key="stage_edit"
                )
                
            with col5:
                # Tratamento seguro da data
                try:
                    current_date = datetime.strptime(row['next_payment'], '%Y-%m-%d').date()
                except:
                    current_date = datetime.today().date()
                    
                new_next = st.date_input("Próximo Pagamento", value=current_date, key="date_edit")
                new_payment_status = st.selectbox(
                    "Status do Pagamento", 
                    ["Pending", "Paid", "Overdue"], 
                    index=["Pending", "Paid", "Overdue"].index(row['payment_status']),
                    key="payment_edit"
                )
            
            if st.button("💾 Atualizar Cliente", type="primary"):
                success = update_client(selected_id, new_status, new_stage, new_next, new_payment_status)
                if success:
                    st.success("Cliente atualizado com sucesso!")
                    st.rerun()
else:
    st.info("📝 Nenhum cliente encontrado. Adicione seu primeiro cliente acima.")

# -----------------------------
# FUNIL VISUAL E MÉTRICAS
# -----------------------------
st.subheader("📊 Analytics")

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["Funil de Vendas", "Métricas Financeiras", "Status de Pagamento"])
    
    with tab1:
        # Funil de estágios
        stage_counts = df['stage'].value_counts().reindex(["Pre-sale", "Implementation", "Post-sale"], fill_value=0)
        
        fig_funnel = px.bar(
            x=stage_counts.index,
            y=stage_counts.values,
            text=stage_counts.values,
            labels={'x': 'Estágio', 'y': 'Número de Clientes'},
            color=stage_counts.index,
            color_discrete_map={
                "Pre-sale": "#FF6B6B",
                "Implementation": "#4ECDC4", 
                "Post-sale": "#45B7D1"
            },
            title="Distribuição de Clientes por Estágio"
        )
        fig_funnel.update_traces(textposition='outside')
        fig_funnel.update_layout(showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True)
    
    with tab2:
        # Métricas financeiras por estágio
        revenue_by_stage = df.groupby('stage')['monthly_fee'].sum().reindex(
            ["Pre-sale", "Implementation", "Post-sale"], fill_value=0
        )
        
        fig_revenue = px.pie(
            values=revenue_by_stage.values,
            names=revenue_by_stage.index,
            title="Receita Mensal por Estágio",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with tab3:
        # Status de pagamento
        payment_counts = df['payment_status'].value_counts()
        
        fig_payment = px.bar(
            x=payment_counts.index,
            y=payment_counts.values,
            text=payment_counts.values,
            color=payment_counts.index,
            color_discrete_map={
                "Paid": "#2ecc71",
                "Pending": "#f39c12",
                "Overdue": "#e74c3c"
            },
            title="Status de Pagamento dos Clientes"
        )
        fig_payment.update_traces(textposition='outside')
        fig_payment.update_layout(showlegend=False)
        st.plotly_chart(fig_payment, use_container_width=True)

else:
    st.info("Adicione clientes para visualizar as métricas e gráficos.")

# -----------------------------
# RODAPÉ
# -----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "CRM Gas Stations ⛽ | Desenvolvido com Streamlit"
    "</div>",
    unsafe_allow_html=True
)
