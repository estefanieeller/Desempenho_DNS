# -*- coding: utf-8 -*-
# Importa a biblioteca para trabalhar com conexões de rede (Sockets da Camada de Transporte)
import random
import socket
import statistics

# Importa a biblioteca de tempo para capturar os instantes de envio e chegada (cálculo do RTT)
import time

# Configurações gerais do programa
PORTA_DNS = 53
TIMEOUT_S = 2.0
TAMANHO_BUFFER = 1024
PACOTES_PADRAO = 5
PACOTES_DISTANCIA = 3
VELOCIDADE_FIBRA_KM_S = 200_000
DOMINIO_PADRAO = "google.com"

# Dicionário constante contendo os IPs dos principais Servidores DNS Públicos
SERVIDORES_DNS = {
    "Cloudflare": "1.1.1.1",
    "Google DNS": "8.8.8.8",
    "Quad9": "9.9.9.9",
    "OpenDNS": "208.67.222.222",
}


def montar_pacote_dns(dominio):
    """
    Função que pega um domínio em texto (ex: 'google.com') e o converte
    num pacote de bytes em formato hexadecimal, que é o padrão exigido pelo
    protocolo DNS na Camada de Aplicação.
    """
    # ID de transação aleatório para correlacionar pergunta e resposta
    transaction_id = random.randint(0, 65535).to_bytes(2, "big")

    # Cabeçalho padrão do DNS (1 requisição padrão com 1 pergunta)
    cabecalho = transaction_id + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"

    qname = b""
    for parte in dominio.split("."):
        qname += bytes([len(parte)]) + parte.encode("utf-8")
    qname += b"\x00"

    # Tipo A (0x0001) e classe IN (0x0001)
    qinfo = b"\x00\x01\x00\x01"

    return cabecalho + qname + qinfo, transaction_id


def enviar_consulta(sock, ip_servidor, pacote_dns, transaction_id):
    """
    Envia um pacote DNS e mede o RTT.
    Retorna o tempo em milissegundos ou None se a resposta for inválida.
    """
    inicio = time.time()
    sock.sendto(pacote_dns, (ip_servidor, PORTA_DNS))
    resposta, _ = sock.recvfrom(TAMANHO_BUFFER)

    # Confere se a resposta pertence à consulta enviada
    if resposta[:2] != transaction_id:
        return None

    fim = time.time()
    return (fim - inicio) * 1000


def disparar_testes(ip_servidor, dominio, num_pacotes):
    """
    Função principal de rede. Cria o Socket UDP, envia a pergunta e calcula o RTT.
    """
    rtts = []
    perdidos = 0

    # Reutiliza o mesmo socket para todos os pacotes enviados ao mesmo servidor
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_cliente:
        socket_cliente.settimeout(TIMEOUT_S)

        for _ in range(num_pacotes):
            pacote_dns, transaction_id = montar_pacote_dns(dominio)

            try:
                rtt = enviar_consulta(
                    socket_cliente,
                    ip_servidor,
                    pacote_dns,
                    transaction_id,
                )

                if rtt is None:
                    perdidos += 1
                else:
                    rtts.append(rtt)

            except socket.timeout:
                perdidos += 1

            except OSError as erro:
                print(f"  [!] Erro de rede com {ip_servidor}: {erro}")
                perdidos += 1

    return rtts, perdidos


def validar_dominio(dominio):
    """Valida formato básico de um nome de domínio."""
    if not dominio or "." not in dominio:
        return False

    partes = dominio.split(".")
    return all(parte and len(parte) <= 63 for parte in partes)


def formatar_estatisticas(rtts, perdidos, num_pacotes):
    """Monta o texto com média, min, max, jitter e perda."""
    if not rtts:
        return "  Falha: 100% de perda de pacotes (Timeout ou resposta inválida).\n"

    jitter = max(rtts) - min(rtts)
    desvio = statistics.stdev(rtts) if len(rtts) > 1 else 0.0
    perda_pct = (perdidos / num_pacotes) * 100

    return (
        f"  RTT Médio:  {statistics.mean(rtts):.2f} ms\n"
        f"  RTT Mínimo: {min(rtts):.2f} ms | Máximo: {max(rtts):.2f} ms\n"
        f"  Jitter:     {jitter:.2f} ms | Desvio: {desvio:.2f} ms\n"
        f"  Perda:      {perda_pct:.0f}%\n"
    )


def testar_todos_servidores(dominio, num_pacotes, callback):
    """Executa o teste em todos os servidores DNS cadastrados."""
    for nome, ip in SERVIDORES_DNS.items():
        rtts, perdidos = disparar_testes(ip, dominio, num_pacotes)
        callback(nome, ip, rtts, perdidos, num_pacotes)


def opcao_1_estatisticas_avancadas():
    """
    Executa a Opção 1 do menu: Mostra a média, min, max, jitter e perdas.
    Bom para analisar a variação do Atraso de Fila (Jitter).
    """
    print("\n--- 1. Análise Avançada de Servidores ---")
    print(
        f"Enviando {PACOTES_PADRAO} pacotes para cada servidor "
        f"(Domínio padrão: {DOMINIO_PADRAO})...\n"
    )

    def exibir(nome, ip, rtts, perdidos, num_pacotes):
        print(f"[{nome} - {ip}]")
        print(formatar_estatisticas(rtts, perdidos, num_pacotes))

    testar_todos_servidores(DOMINIO_PADRAO, PACOTES_PADRAO, exibir)


def opcao_2_comparacao_sites():
    """
    Executa a Opção 2: O usuário testa a resolução de um site à escolha.
    Compara a 1ª e a 2ª consulta para observar o efeito do CACHE de DNS.
    """
    print("\n--- 2. Tempo de Resolução por Site ---")
    site = input("Digite o site que deseja testar (ex: uff.br, pudim.com.br): ").strip().lower()

    if not validar_dominio(site):
        print("Erro: informe um domínio válido (ex: uff.br).")
        return

    print(f"\nConsultando o IP de '{site}' nos servidores principais...\n")

    for nome, ip in SERVIDORES_DNS.items():
        primeira, perdidos_1 = disparar_testes(ip, site, 1)
        segunda, perdidos_2 = disparar_testes(ip, site, 1)

        if primeira:
            linha = f"[{nome}] 1ª consulta: {primeira[0]:.2f} ms"
            if segunda:
                diferenca = primeira[0] - segunda[0]
                linha += f" | 2ª consulta: {segunda[0]:.2f} ms (Δ {diferenca:+.2f} ms)"
            print(linha)
        else:
            print(f"[{nome}] não respondeu a tempo.")

        if perdidos_1 or perdidos_2:
            print(f"  Perdas: {perdidos_1 + perdidos_2} pacote(s)")

    print("\nNota: a 2ª consulta costuma ser mais rápida quando há cache no servidor ou no caminho.\n")


def opcao_3_estimativa_distancia():
    """
    Executa a Opção 3: Usa a fórmula de Atraso de Propagação
    Distância = Velocidade * Tempo
    """
    print("\n--- 3. Estimativa de Distância Física ---")
    print("Baseado no Atraso de Propagação")
    print(f"Velocidade da luz na fibra: ~{VELOCIDADE_FIBRA_KM_S:,} km/s".replace(",", "."))
    print("Atenção: servidores anycast e cache podem distorcer o resultado.\n")

    for nome, ip in SERVIDORES_DNS.items():
        rtts, _ = disparar_testes(ip, DOMINIO_PADRAO, PACOTES_DISTANCIA)

        if not rtts:
            print(f"[{nome}] sem resposta válida.\n")
            continue

        # Pega o RTT mínimo porque é o que sofreu menos atraso de fila
        rtt_min = min(rtts)

        # Divide por 2 (ida e volta) e por 1000 (ms -> s)
        tempo_ida_s = (rtt_min / 2) / 1000

        # Calcula a distância (d = s * t)
        distancia_km = tempo_ida_s * VELOCIDADE_FIBRA_KM_S

        print(f"[{nome}] RTT Mínimo: {rtt_min:.2f} ms")
        print(f"  -> Distância estimada do seu computador: ~{distancia_km:.0f} km\n")


def main():
    """
    Loop infinito do Menu Principal. Mantém o programa a correr até o utilizador pedir para sair.
    """
    opcoes = {
        "1": opcao_1_estatisticas_avancadas,
        "2": opcao_2_comparacao_sites,
        "3": opcao_3_estimativa_distancia,
    }

    while True:
        print("==================================================")
        print("    DIAGNÓSTICO DE REDE DNS E LATÊNCIA")
        print("==================================================")
        print("1 - Análise Avançada (RTT Médio, Min, Max, Jitter e Perda)")
        print("2 - Testar tempo de resposta de um Site Específico")
        print("3 - Estimar Distância Física do Servidor DNS")
        print("0 - Sair do programa")

        escolha = input("\nEscolha uma opção (0-3): ").strip()

        try:
            if escolha == "0":
                print("\nEncerrando o programa. Tenha um bom dia!\n")
                break

            funcao = opcoes.get(escolha)
            if funcao is None:
                print("\n[!] Opção inválida. Por favor, digite um número de 0 a 3.\n")
            else:
                funcao()

            input("Pressione [ENTER] para voltar ao menu principal...")
            print("\n" * 2)

        except KeyboardInterrupt:
            print("\n\n[!] Operação cancelada pelo usuário. Retornando ao menu...\n")

        except Exception as erro:
            print(f"\n[!] Ocorreu um erro inesperado de rede: {erro}")
            print("Retornando ao menu principal...\n")
            time.sleep(2)


if __name__ == "__main__":
    main()
