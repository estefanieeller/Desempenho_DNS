## Dashboard Interativo de Diagnóstico de Rede & Desempenho DNS

Este projeto consiste em uma aplicação web interativa desenvolvida em **Python** utilizando **Streamlit** e **Plotly**.
O objetivo principal é realizar diagnósticos de desempenho de rede em servidores DNS públicos utilizando sockets de baixo nível (UDP puro), permitindo analisar métricas essenciais das camadas de aplicação e transporte do modelo TCP/IP.

## Funcionalidades

O dashboard divide-se em três pilhas analíticas principais:
1. **Análise Avançada (RTT/Jitter):** Dispara múltiplos pacotes UDP puros para calcular o RTT (Round-Trip Time) mínimo, médio, máximo, a variação estatística de atraso (Jitter) e a porcentagem de perda de pacotes.
2. **Impacto do Cache DNS:** Demonstra de forma prática e visual a diferença de tempo de resposta entre uma consulta com *Cache Miss* (1ª tentativa) e *Cache Hit* (2ª tentativa).
3. **Estimativa de Distância Física:** Realiza uma aproximação geométrica da distância teórica entre a sua máquina e o servidor DNS com base no menor tempo de propagação do sinal na fibra óptica.

## Conceitos Teóricos Abordados

Este projeto implementa conceitos fundamentais da literatura de redes de computadores (baseado na abordagem *Top-Down* de Kurose & Ross):
* **Sockets UDP puros (Porta 53):** A aplicação não utiliza comandos do sistema operacional (como `nslookup` ou `ping`), mas sim estruturas da biblioteca `socket` do Python (`sendto` e `recvfrom`), construindo as requisições em nível de bytes.
* **Atraso de Propagação:** Utilizado na aba de estimativa de distância, aplicando a velocidade da luz na fibra óptica (~200.000 km/s) sobre o menor RTT registrado.
* **Mecânica de Cache DNS:** Evidencia como o armazenamento temporário de registros reduz o tráfego global na raiz da Internet e melhora drasticamente o tempo de navegação do usuário.

## Pré-requisitos & Instalação (Mac/Linux)

Certifique-se de ter o Python 3.x instalado em sua máquina.

Passo 1 (Navegação): Abra o Terminal do seu sistema e use o comando cd para entrar na pasta exata onde guardou o arquivo app_dns.py (por exemplo, cd ~/Documents).

Passo 2 (Instalação): Instale as dependências de interface e gráficos do ecossistema Python executando o comando pip3 install streamlit plotly pandas.

Passo 3 (Inicialização): Para contornar restrições de ambiente locais das shells Zsh ou Bash, inicialize o dashboard através do comando central do interpretador: python3 -m streamlit run app_dns.py.

Passo 4 (Configuração Inicial): Caso o terminal solicite um e-mail com o aviso Email:, pressione apenas a tecla Enter para ignorar e deixar o campo em branco.

Passo 5 (Acesso Web): Aguarde a aplicação abrir de forma automática uma nova aba no seu navegador de internet padrão sob o endereço local http://localhost:8501.
