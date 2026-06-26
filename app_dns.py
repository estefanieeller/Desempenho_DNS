import random
import socket
import statistics
import time
import plotly.express as px
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURAÇÕES DE REDE (Mantidas do teu código)
# ==========================================
PORTA_DNS = 53
TIMEOUT_S = 2.0
TAMANHO_BUFFER = 1024
VELOCIDADE_FIBRA_KM_S = 200_000

SERVIDORES_DNS = {
    "Cloudflare": "1.1.1.1",
    "Google DNS": "8.8.8.8",
    "Quad9": "9.9.9.9",
    "OpenDNS": "208.67.222.222",
}


# ==========================================
# FUNÇÕES LÓGICAS DE REDE
# ==========================================
def montar_pacote_dns(dominio):
    transaction_id = random.randint(0, 65535).to_bytes(2, "big")
    cabecalho = transaction_id + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    qname = b""
    for parte in dominio.split("."):
        qname += bytes([len(parte)]) + parte.encode("utf-8")
    qname += b"\x00"
    qinfo = b"\x00\x01\x00\x01"
    return cabecalho + qname + qinfo, transaction_id


def enviar_consulta(sock, ip_servidor, pacote_dns, transaction_id):
    inicio = time.time()
    sock.sendto(pacote_dns, (ip_servidor, PORTA_DNS))
    resposta, _ = sock.recvfrom(TAMANHO_BUFFER)
    if resposta[:2] != transaction_id:
        return None
    fim = time.time()
    return (fim - inicio) * 1000


def disparar_testes(ip_servidor, dominio, num_pacotes):
    rtts = []
    perdidos = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_cliente:
        socket_cliente.settimeout(TIMEOUT_S)
        for _ in range(num_pacotes):
            pacote_dns, transaction_id = montar_pacote_dns(dominio)
            try:
                rtt = enviar_consulta(
                    socket_cliente, ip_servidor, pacote_dns, transaction_id
                )
                if rtt is None:
                    perdidos += 1
                else:
                    rtts.append(rtt)
            except socket.timeout:
                perdidos += 1
            except OSError:
                perdidos += 1
    return rtts, perdidos


# ==========================================
# INTERFACE GRÁFICA (STREAMLIT)
# ==========================================
st.set_page_config(
    page_title="Dashboard de Desempenho DNS", page_icon="🌐", layout="wide"
)

st.title("🌐 Dashboard de Diagnóstico de Rede & DNS")
st.markdown(
    "Converta a sua ferramenta de terminal numa aplicação visual para analisar a Camada de Aplicação e Transporte."
)

# Barra Lateral para Parâmetros
st.sidebar.header("⚙️ Configurações do Teste")
dominio_alvo = st.sidebar.text_input("Domínio para consulta", "google.com")
num_pacotes = st.sidebar.slider(
    "Número de pacotes por servidor", min_value=1, max_value=20, value=5
)

# Criação de abas para replicar as opções do menu original
aba1, aba2, aba3 = st.tabs(
    [
        "📊 Análise Avançada (RTT/Jitter)",
        "⚡ Cache DNS",
        "🗺️ Estimativa de Distância",
    ]
)

# ------------------------------------------------------------
# ABA 1: ESTATÍSTICAS AVANÇADAS
# ------------------------------------------------------------
with aba1:
    st.header("Análise Avançada de Latência e Jitter")
    if st.button("🚀 Executar Diagnóstico Global", key="btn_aba1"):
        dados_dashboard = []

        with st.spinner("Disparando pacotes UDP para os servidores..."):
            for nome, ip in SERVIDORES_DNS.items():
                rtts, perdidos = disparar_testes(ip, dominio_alvo, num_pacotes)

                if rtts:
                    media = statistics.mean(rtts)
                    minimo = min(rtts)
                    maximo = max(rtts)
                    jitter = maximo - minimo
                    perda_pct = (perdidos / num_pacotes) * 100

                    dados_dashboard.append(
                        {
                            "Servidor": nome,
                            "IP": ip,
                            "RTT Médio (ms)": round(media, 2),
                            "RTT Mínimo (ms)": round(minimo, 2),
                            "RTT Máximo (ms)": round(maximo, 2),
                            "Jitter (ms)": round(jitter, 2),
                            "Perda (%)": round(perda_pct, 1),
                        }
                    )
                else:
                    dados_dashboard.append(
                        {
                            "Servidor": nome,
                            "IP": ip,
                            "RTT Médio (ms)": None,
                            "RTT Mínimo (ms)": None,
                            "RTT Máximo (ms)": None,
                            "Jitter (ms)": None,
                            "Perda (%)": 100.0,
                        }
                    )

        df = pd.DataFrame(dados_dashboard)

        # Exibição de Métricas Rápidas (Melhor Servidor)
        df_validos = df.dropna()
        if not df_validos.empty:
            melhor_srv = df_validos.loc[df_validos["RTT Médio (ms)"].idxmin()]
            st.success(
                f"🏆 **Melhor Desempenho:** {melhor_srv['Servidor']} com média de {melhor_srv['RTT Médio (ms)']} ms!"
            )

        # Tabela interativa
        st.subheader("Resultados Consolidados")
        st.dataframe(df, use_container_width=True)

        # Gráfico de Comparação
        st.subheader("Gráfico Comparativo de RTT Médio")
        fig = px.bar(
            df_validos,
            x="Servidor",
            y="RTT Médio (ms)",
            text_auto=True,
            color="Servidor",
            title=f"Latência Média por Servidor (Alvo: {dominio_alvo})",
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# ABA 2: COMPARAÇÃO DE SITES (EFEITO CACHE)
# ------------------------------------------------------------
with aba2:
    st.header("Efeito do Cache de DNS")
    st.markdown(
        "Este teste faz duas consultas consecutivas de 1 pacote. A segunda costuma ser mais rápida devido ao cache local ou do servidor."
    )

    site_especifico = st.text_input(
        "Digite o site para testar cache (ex: uff.br)", "pudim.com.br"
    )

    if st.button("⚡ Testar Tempo de Resolução", key="btn_aba2"):
        resultados_cache = []

        with st.spinner("Consultando..."):
            for nome, ip in SERVIDORES_DNS.items():
                primeira, _ = disparar_testes(ip, site_especifico, 1)
                segunda, _ = disparar_testes(ip, site_especifico, 1)

                if primeira and segunda:
                    diff = primeira[0] - segunda[0]
                    resultados_cache.append(
                        {
                            "Servidor": nome,
                            "1ª Consulta (ms)": round(primeira[0], 2),
                            "2ª Consulta (ms)": round(segunda[0], 2),
                            "Diferença (Δ ms)": round(diff, 2),
                        }
                    )

        if resultados_cache:
            df_cache = pd.DataFrame(resultados_cache)
            st.dataframe(df_cache, use_container_width=True)

            # Gráfico comparativo de barras lado a lado
            df_melted = df_cache.melt(
                id_vars=["Servidor"],
                value_vars=["1ª Consulta (ms)", "2ª Consulta (ms)"],
                var_name="Tentativa",
                value_name="Tempo (ms)",
            )
            fig_cache = px.bar(
                df_melted,
                x="Servidor",
                y="Tempo (ms)",
                color="Tentativa",
                barmode="group",
                title=f"Comparação de Impacto de Cache para {site_especifico}",
            )
            st.plotly_chart(fig_cache, use_container_width=True)
        else:
            st.error("Nenhum servidor respondeu a tempo para este domínio.")

# ------------------------------------------------------------
# ABA 3: ESTIMATIVA DE DISTÂNCIA FÍSICA
# ------------------------------------------------------------
with aba3:
    st.header("Estimativa de Distância Física")
    st.markdown(
        f"Cálculo teórico baseado no **Atraso de Propagação** utilizando a velocidade da luz na fibra: **{VELOCIDADE_FIBRA_KM_S:,} km/s**."
    )

    if st.button("🗺️ Calcular Distâncias", key="btn_aba3"):
        dados_distancia = []

        with st.spinner("Analisando tempos mínimos de propagação..."):
            for nome, ip in SERVIDORES_DNS.items():
                rtts, _ = disparar_testes(ip, dominio_alvo, 3)

                if rtts:
                    rtt_min = min(rtts)
                    tempo_ida_s = (rtt_min / 2) / 1000
                    distancia_km = tempo_ida_s * VELOCIDADE_FIBRA_KM_S

                    dados_distancia.append(
                        {
                            "Servidor": nome,
                            "RTT Mínimo (ms)": round(rtt_min, 2),
                            "Distância Estimada (km)": int(distancia_km),
                        }
                    )

        if dados_distancia:
            df_dist = pd.DataFrame(dados_distancia)

            # Mostrar em formato de "Cards" visuais do Streamlit
            cols = st.columns(len(df_dist))
            for idx, row in df_dist.iterrows():
                with cols[idx]:
                    st.metric(
                        label=f"📍 {row['Servidor']}",
                        value=f"{row['Distância Estimada (km)']} km",
                        delta=f"{row['RTT Mínimo (ms)']} ms",
                        delta_color="inverse",
                    )

            fig_dist = px.scatter(
                df_dist,
                x="Servidor",
                y="Distância Estimada (km)",
                size="Distância Estimada (km)",
                color="Servidor",
                title="Aproximação Geométrica da Distância do Roteador",
            )
            st.plotly_chart(fig_dist, use_container_width=True)