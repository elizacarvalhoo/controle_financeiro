import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import shutil

# ================= BACKUP =================
def fazer_backup():
    data = datetime.now().strftime("%Y-%m-%d_%H-%M")

    if os.path.exists("dados.csv"):
        shutil.copy("dados.csv", f"backup_dados_{data}.csv")

    if os.path.exists("cartoes.csv"):
        shutil.copy("cartoes.csv", f"backup_cartoes_{data}.csv")

    if os.path.exists("metas.csv"):
        shutil.copy("metas.csv", f"backup_metas_{data}.csv")

st.set_page_config(page_title="Controle Financeiro PRO", layout="wide")

# BACKUP AUTOMÁTICO
fazer_backup()

# ================= LOGIN =================
USUARIO = "admin"
SENHA = "1234"

def login():
    st.title("🔐 Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == USUARIO and senha == SENHA:
            st.session_state["logado"] = True
        else:
            st.error("Usuário ou senha incorretos")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login()
    st.stop()

# ================= ARQUIVOS =================
ARQUIVO = "dados.csv"
ARQ_CARTOES = "cartoes.csv"
ARQ_METAS = "metas.csv"

def carregar_dados():
    try:
        return pd.read_csv(ARQUIVO)
    except:
        return pd.DataFrame(columns=["data","tipo","descricao","categoria","valor","cartao","parcela","total_parcelas"])

def carregar_cartoes():
    try:
        return pd.read_csv(ARQ_CARTOES)
    except:
        return pd.DataFrame(columns=["nome","limite","limite_alerta"])

def salvar_cartoes(df):
    df.to_csv(ARQ_CARTOES, index=False)

def carregar_metas():
    try:
        return pd.read_csv(ARQ_METAS)
    except:
        return pd.DataFrame(columns=["categoria","limite"])

def salvar_metas(df):
    df.to_csv(ARQ_METAS, index=False)

def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

df = carregar_dados()
cartoes = carregar_cartoes()
metas_df = carregar_metas()

if not df.empty:
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["mes"] = df["data"].dt.to_period("M")

st.title("💳 Controle Financeiro PRO")

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard","Adicionar","Cartões","Fatura","Previsão","Histórico","Metas"]
)

# BOTÃO BACKUP
st.sidebar.subheader("💾 Backup")

if st.sidebar.button("Salvar backup agora"):
    fazer_backup()
    st.sidebar.success("Backup salvo com sucesso!")

# ================= DASHBOARD =================
if menu == "Dashboard":

    total = df["valor"].sum()
    gastos = df[df["valor"] < 0]

    col1, col2 = st.columns(2)
    col1.metric("Saldo", f"R$ {total:.2f}")
    col2.metric("Gastos", f"R$ {abs(gastos['valor'].sum()):.2f}")

    for _, m in metas_df.iterrows():
        categoria = m["categoria"]
        limite = m["limite"]

        gasto = abs(gastos[gastos["categoria"] == categoria]["valor"].sum())

        if gasto > limite:
            st.error(f"🚨 {categoria}: estourou meta!")
        elif gasto > limite * 0.8:
            st.warning(f"⚠️ {categoria}: perto da meta")

# ================= ADICIONAR =================
elif menu == "Adicionar":

    st.header("➕ Nova Transação")

    data = st.date_input("Data")
    tipo = st.selectbox("Tipo", ["entrada","saida"])
    descricao = st.text_input("Descrição")

    categorias = ["alimentacao","combustivel","lazer","carro","transporte","outros"]
    categoria = st.selectbox("Categoria", categorias)

    valor = st.number_input("Valor", format="%.2f")
    cartao = st.text_input("Cartão")
    parcelas = st.number_input("Parcelas", min_value=1)

    if st.button("Salvar"):
        linhas = []

        for i in range(parcelas):
            valor_parcela = valor / parcelas
            if tipo == "saida":
                valor_parcela = -abs(valor_parcela)

            linhas.append({
                "data": data + relativedelta(months=i),
                "tipo": tipo,
                "descricao": descricao,
                "categoria": categoria,
                "valor": valor_parcela,
                "cartao": cartao,
                "parcela": i+1,
                "total_parcelas": parcelas
            })

        df = pd.concat([df, pd.DataFrame(linhas)], ignore_index=True)
        salvar_dados(df)

        st.success("Salvo!")
        st.rerun()

# ================= CARTÕES =================
elif menu == "Cartões":

    st.header("💳 Cartões")

    st.subheader("➕ Adicionar cartão")
    nome = st.text_input("Nome do cartão")
    limite = st.number_input("Limite total", format="%.2f")
    alerta = st.number_input("Seu limite pessoal", format="%.2f")

    if st.button("Salvar Cartão"):
        novo = pd.DataFrame([{
            "nome": nome,
            "limite": limite,
            "limite_alerta": alerta
        }])

        cartoes = pd.concat([cartoes, novo], ignore_index=True)
        salvar_cartoes(cartoes)

        st.success("Cartão salvo!")
        st.rerun()

    for _, c in cartoes.iterrows():
        nome = c["nome"]
        limite = c["limite"]
        alerta = c["limite_alerta"]

        gastos = abs(df[df["cartao"] == nome]["valor"].sum())

        st.subheader(nome)
        st.write(f"Gasto: R$ {gastos:.2f}")

        futuros = df[(df["cartao"] == nome) & (df["data"] > datetime.today())]
        previsao = gastos + abs(futuros["valor"].sum())

        st.write(f"Previsão: R$ {previsao:.2f}")

        if previsao > limite:
            st.error("🚨 Vai estourar o limite!")
        elif previsao > alerta:
            st.warning("⚠️ Vai passar do seu limite definido!")

# ================= FATURA =================
elif menu == "Fatura":

    hoje = datetime.today()

    mes = st.number_input("Mês", 1, 12, value=hoje.month)
    ano = st.number_input("Ano", min_value=2025, value=hoje.year)

    filtro = df[(df["data"].dt.month == mes) & (df["data"].dt.year == ano)]

    st.dataframe(filtro)
    st.subheader(f"Total: R$ {abs(filtro['valor'].sum()):.2f}")

# ================= PREVISÃO =================
elif menu == "Previsão":

    futuros = df[df["data"] > datetime.today()]

    st.dataframe(futuros)
    st.subheader(f"Total futuro: R$ {abs(futuros['valor'].sum()):.2f}")

# ================= HISTÓRICO =================
elif menu == "Histórico":

    st.header("📅 Histórico (Editar / Excluir)")

    if not df.empty:

        meses = df["mes"].astype(str).unique()
        mes = st.selectbox("Mês", meses)

        filtro = df[df["mes"].astype(str) == mes].copy()

        # CRIA COLUNA DE EXCLUSÃO
        filtro["❌ Excluir"] = False

        st.write("✏️ Edite os dados ou marque para excluir:")

        df_editado = st.data_editor(
            filtro,
            use_container_width=True,
            num_rows="dynamic"
        )

        col1, col2 = st.columns(2)

        # SALVAR ALTERAÇÕES
        if col1.button("💾 Salvar alterações"):
            df.update(df_editado.drop(columns=["❌ Excluir"]))
            salvar_dados(df)
            st.success("Alterações salvas com sucesso!")
            st.rerun()

        # EXCLUIR SELECIONADOS
        if col2.button("❌ Excluir selecionados"):
            excluir = df_editado[df_editado["❌ Excluir"] == True]

            if not excluir.empty:
                df = df.drop(excluir.index)
                df = df.reset_index(drop=True)
                salvar_dados(df)

                st.success("Lançamentos excluídos!")
                st.rerun()
            else:
                st.warning("Selecione pelo menos um lançamento")

        st.subheader(f"Total do mês: R$ {df_editado['valor'].sum():.2f}")

    else:
        st.info("Sem dados ainda")

# ================= METAS =================
elif menu == "Metas":

    st.header("💰 Metas por categoria")

    categorias = ["alimentacao","combustivel","lazer","carro","transporte","outros"]

    nova_cat = st.selectbox("Categoria", categorias)
    limite = st.number_input("Limite", format="%.2f")

    if st.button("Salvar Meta"):
        nova = pd.DataFrame([{
            "categoria": nova_cat,
            "limite": limite
        }])

        metas_df = pd.concat([metas_df, nova], ignore_index=True)
        salvar_metas(metas_df)

        st.success("Meta salva!")
        st.rerun()

