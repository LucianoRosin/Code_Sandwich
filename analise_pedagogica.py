import json
import statistics
import os
import asyncio
import random
import sys
import time
# utils agora só precisa de load_json_data e call_gemini_api
from utils import load_json_data, call_gemini_api
from config import DEFAULT_GAME_CONFIG # Importar a configuração
# --- Constantes ---
# Usar valores da configuração importada
ARQUIVO_CARTAS = DEFAULT_GAME_CONFIG.get('cards_file', 'cartas.json')
ARQUIVO_KCS = DEFAULT_GAME_CONFIG.get('kcs_file', 'kcs.json')
DIRETORIO_ANALISES = DEFAULT_GAME_CONFIG.get('analysis_directory', 'analises')
ARQUIVO_RELATORIO = os.path.join(DIRETORIO_ANALISES, DEFAULT_GAME_CONFIG.get('acp_report_file', 'RELATORIO_ACP.md'))
# NUM_CARTAS_PILAR1 = 5 # Remover constante local

# --- Pilar 1: Auditoria de Metáfora ---
async def analisar_pilar_1_dinamico(model, cartas, kcs):
    """Realiza a análise de coerência da 'Tríade' para uma amostra."""
    relatorio_p1 = "## Pilar 1: Auditoria de Coerência de Metáfora (Análise Dinâmica via IA)\n\n"
    relatorio_p1 += "Esta análise verifica a coerência da 'tríade' (Conceito, Metáfora, Mecânica) para uma amostra de cartas.\n\n"

    # Obter o número de cartas a analisar da configuração
    num_cartas_pilar1 = DEFAULT_GAME_CONFIG.get('num_cartas_pilar1', 5) # Usar 5 como fallback
    if not model:
        return relatorio_p1 + "Análise IA pulada: Modelo Gemini não configurado.\n"

    kc_lookup = {kc_id: data.get('dificuldade', '?') for kc_id, data in kcs.items()}
    cartas_dict = {c.get('id'): c for c in cartas if c.get('tipo') != 'Receita Final'}

    if not cartas_dict:
        return relatorio_p1 + "AVISO: Nenhuma carta (não-receita) encontrada para análise.\n"

    # Seleciona amostra aleatória, tentando diversificar
    tipos_presentes = {c.get('tipo') for c in cartas_dict.values() if c.get('tipo')}
    cartas_para_analisar_ids = []
    cartas_disponiveis = list(cartas_dict.keys())
    random.shuffle(cartas_disponiveis)

    # Tenta pegar uma de cada tipo
    for tipo in tipos_presentes:
        if len(cartas_para_analisar_ids) >= num_cartas_pilar1: break # Usar variável da config
        for card_id in cartas_disponiveis:
            if cartas_dict[card_id].get('tipo') == tipo and card_id not in cartas_para_analisar_ids:
                cartas_para_analisar_ids.append(card_id)
                cartas_disponiveis.remove(card_id) # Remove para não repetir
                break

    # Completa com aleatórias se necessário
    while len(cartas_para_analisar_ids) < num_cartas_pilar1 and cartas_disponiveis: # Usar variável da config
        card_id = cartas_disponiveis.pop(0)
        cartas_para_analisar_ids.append(card_id)

    if not cartas_para_analisar_ids:
         return relatorio_p1 + "AVISO: Não foi possível selecionar cartas para análise.\n"

    relatorio_p1 += f"**Amostra Selecionada (Máx {num_cartas_pilar1}):** `{', '.join(cartas_para_analisar_ids)}`\n\n" # Usar variável da config
    tasks = []

    for card_id in cartas_para_analisar_ids:
        carta = cartas_dict.get(card_id)
        if carta:
            kcs_associados = carta.get('kc_associado', [])
            kcs_str = ", ".join(kcs_associados) if kcs_associados else "Nenhum"
            difs_str = ', '.join(str(kc_lookup.get(kc, '?')) for kc in kcs_associados) if kcs_associados else "N/A"

            prompt = f"""
            **Tarefa de Análise Pedagógica (Jogo: Code Sandwich)**
            **Contexto:** Você é um especialista em design de jogos educacionais. Analise a seguinte carta do jogo 'Code Sandwich'.
            **Carta:**
            - **Nome:** {carta.get('nome', 'N/A')} ({card_id})
            - **Tipo:** {carta.get('tipo', 'N/A')}
            - **Conceito(s) Alvo (KC):** {kcs_str} (Dificuldade(s): {difs_str})
            - **Metáfora/Descrição:** "{carta.get('texto_efeito', '')}"
            - **Mecânica no Jogo:** (Inferida do tipo e descrição)
            **Sua Avaliação (em português do Brasil):**
            1.  **Coerência da Tríade:** Avalie o alinhamento entre Metáfora, Mecânica e Conceito(s) Alvo (KC). A conexão é clara, forçada ou confusa?
            2.  **Potencial Pedagógico:** A carta pode ajudar um jogador leigo a entender/reforçar o conceito de programação associado? Por quê?
            3.  **Sugestão (Opcional):** Há melhoria óbvia para fortalecer o valor educacional?
            **Formato:** Use bullet points ou parágrafos curtos. Seja crítico e construtivo.
            """
            tasks.append(call_gemini_api(model, prompt))
        else:
             # Adiciona um resultado de erro diretamente se a carta não for encontrada
             tasks.append(asyncio.sleep(0, result=f"ERRO: Carta {card_id} não encontrada."))

    resultados_ia = await asyncio.gather(*tasks)

    for i, card_id in enumerate(cartas_para_analisar_ids):
        carta = cartas_dict.get(card_id)
        relatorio_p1 += f"### {i+1}. Análise da Carta: {carta.get('nome', 'N/A') if carta else card_id} ({card_id})\n"
        if carta:
            kcs_associados = carta.get('kc_associado', [])
            kcs_str = ", ".join(kcs_associados) if kcs_associados else "Nenhum"
            difs_str = ', '.join(str(kc_lookup.get(kc, '?')) for kc in kcs_associados) if kcs_associados else "N/A"
            relatorio_p1 += f"- **Tipo:** {carta.get('tipo', 'N/A')}\n"
            relatorio_p1 += f"- **Conceito(s) (KC):** `{kcs_str}` (Dificuldade(s): {difs_str})\n"
            relatorio_p1 += f"- **Metáfora (Texto):** \"{carta.get('texto_efeito', '')}\"\n"
            relatorio_p1 += f"**Avaliação da IA:**\n{resultados_ia[i]}\n\n" # Inclui a resposta da IA ou a mensagem de erro
        else:
            relatorio_p1 += f"- ERRO: Carta {card_id} não encontrada nos dados.\n\n" # Mantém a consistência

    return relatorio_p1

# --- Pilar 2: Análise Curricular ---
async def analisar_pilar_2_com_ia(model, cartas, kcs):
    """Calcula dificuldade média das receitas e pede análise da IA."""
    relatorio_p2 = "\n## Pilar 2: Análise Curricular e Progressão de Dificuldade (com Análise IA)\n\n"
    relatorio_p2 += "Análise da 'Dificuldade Média da Receita' e avaliação da progressão curricular pela IA.\n\n"

    kc_dificuldades = {kc_id: data.get('dificuldade', 0) for kc_id, data in kcs.items()}
    receitas = [carta for carta in cartas if carta.get('tipo') == 'Receita Final']

    if not receitas:
        return relatorio_p2 + "AVISO: Nenhuma carta de Receita Final encontrada.\n"

    resultados_receitas = []
    for receita in receitas:
        kcs_associados = receita.get('kc_associado', [])
        dificuldades_kcs = [kc_dificuldades.get(kc) for kc in kcs_associados if kc_dificuldades.get(kc) is not None]
        kcs_com_dificuldade_str = ", ".join([f"{kc} (D{kc_dificuldades.get(kc, '?')})" for kc in kcs_associados])
        dificuldade_media = statistics.mean(dificuldades_kcs) if dificuldades_kcs else 0.0
        resultados_receitas.append({
            "id": receita.get('id', 'N/A'),
            "nome": receita.get('nome', 'N/A'),
            "dificuldade_media": dificuldade_media,
            "kcs_str": kcs_com_dificuldade_str if kcs_associados else "Nenhum KC associado"
        })

    resultados_receitas.sort(key=lambda x: x["dificuldade_media"])

    # Tabela Markdown
    tabela_md = "| Dificuldade Média | Receita (ID) | KCs Associados (com Dificuldade) |\n"
    tabela_md += "|:---:|:---|:---|\n"
    for r in resultados_receitas:
        tabela_md += f"| **{r['dificuldade_media']:.2f}** | {r['nome']} (`{r['id']}`) | {r['kcs_str']} |\n"
    relatorio_p2 += tabela_md + "\n"

    # Análise IA
    if model:
        resumo_dificuldades = [(r['nome'], round(r['dificuldade_media'], 2)) for r in resultados_receitas] # Arredonda para prompt mais limpo
        prompt = f"""
        **Tarefa de Análise Curricular (Jogo: Code Sandwich)**
        **Contexto:** Lista de 'Receitas Finais' ordenadas por 'Dificuldade Média' calculada dos conceitos de programação (KCs) abordados.
        **Dados (Receita, Dificuldade Média):**
        {json.dumps(resumo_dificuldades, ensure_ascii=False, indent=2)}
        **Sua Avaliação (em português do Brasil):**
        1.  **Progressão:** A ordem sugere progressão de aprendizado suave e lógica para iniciantes? Há saltos grandes de dificuldade?
        2.  **Cobertura:** A variedade de dificuldades é adequada? Cobre do básico ao avançado?
        3.  **Insights:** O que a ordenação revela sobre o design curricular? Pontos fortes/fracos?
        **Formato:** Análise concisa em 1-2 parágrafos.
        """
        interpretacao_ia = await call_gemini_api(model, prompt)
        relatorio_p2 += f"**Análise da IA sobre a Progressão Curricular:**\n{interpretacao_ia}\n"
    else:
        relatorio_p2 += "**Análise da IA sobre a Progressão Curricular:** Pulada (Modelo não configurado).\n"

    return relatorio_p2

# --- Pilar 3: Simulação de Raciocínio ---
async def analisar_pilar_3_dinamico(model, cartas, kcs):
    """Seleciona cenário e pede à IA para simular raciocínio do aluno."""
    relatorio_p3 = "\n## Pilar 3: Simulação Dinâmica de Raciocínio (Análise Qualitativa via IA)\n\n"
    relatorio_p3 += "Seleção de um cenário (Receita + Carta) e simulação do raciocínio do aluno pela IA.\n\n"

    if not model:
        return relatorio_p3 + "Análise IA pulada: Modelo Gemini não configurado.\n"

    cartas_dict = {c.get('id'): c for c in cartas}
    receitas = [c for c in cartas if c.get('tipo') == 'Receita Final']
    ingredientes_e_acoes = [c for c in cartas if c.get('tipo') not in ['Receita Final', 'Coringa']]

    if not receitas or not ingredientes_e_acoes:
        return relatorio_p3 + "AVISO: Não há receitas ou cartas suficientes para selecionar um cenário.\n"

    # Estratégia: Receita média/alta + carta ingrediente com KC em comum.
    receitas.sort(key=lambda r: statistics.mean([kcs.get(kc, {}).get('dificuldade', 0) for kc in r.get('kc_associado', []) if kcs.get(kc)]) if r.get('kc_associado') else 0, reverse=True)

    carta_cenario = None
    receita_cenario = None
    cenario_encontrado = False

    # Tenta par com KC comum
    for r in receitas[:min(len(receitas), 10)]: # Tenta 10 mais difíceis
        kcs_receita = set(r.get('kc_associado', []))
        ingredientes_necessarios = r.get('ingredientes', [])
        random.shuffle(ingredientes_necessarios)
        for ing_nome in ingredientes_necessarios:
            carta_def = next((c for c_id, c in cartas_dict.items() if c.get('nome') == ing_nome and c.get('tipo') != 'Receita Final'), None)
            if carta_def:
                kcs_carta = set(carta_def.get('kc_associado', []))
                if kcs_receita.intersection(kcs_carta):
                    receita_cenario = r
                    carta_cenario = carta_def
                    cenario_encontrado = True
                    break
        if cenario_encontrado: break

    # Fallback: Receita difícil + ingrediente aleatório dela
    if not cenario_encontrado and receitas:
        receita_cenario = receitas[0]
        ingredientes_necessarios = receita_cenario.get('ingredientes', [])
        if ingredientes_necessarios:
            ing_nome_aleatorio = random.choice(ingredientes_necessarios)
            carta_cenario = next((c for c_id, c in cartas_dict.items() if c.get('nome') == ing_nome_aleatorio and c.get('tipo') != 'Receita Final'), None)

    if not carta_cenario or not receita_cenario:
        return relatorio_p3 + "AVISO: Falha ao selecionar dinamicamente um cenário Receita/Carta.\n"

    kc_lookup = {kc_id: data.get('dificuldade', '?') for kc_id, data in kcs.items()}
    kcs_receita_str = ", ".join([f"{kc}(D{kc_lookup.get(kc, '?')})" for kc in receita_cenario.get('kc_associado', [])])
    kcs_carta_str = ", ".join([f"{kc}(D{kc_lookup.get(kc, '?')})" for kc in carta_cenario.get('kc_associado', [])])
    kcs_comuns = set(receita_cenario.get('kc_associado', [])).intersection(set(carta_cenario.get('kc_associado', [])))
    kcs_comuns_str = ", ".join(kcs_comuns) if kcs_comuns else "Nenhum em comum"

    relatorio_p3 += f"### Cenário Selecionado: Receita '{receita_cenario.get('nome')}' e Carta '{carta_cenario.get('nome')}'\n\n"
    relatorio_p3 += f"- **Detalhes da Receita:** ID `{receita_cenario.get('id')}`, KCs: {kcs_receita_str}\n"
    relatorio_p3 += f"- **Detalhes da Carta:** ID `{carta_cenario.get('id')}`, Tipo `{carta_cenario.get('tipo')}`, KCs: {kcs_carta_str}\n"
    relatorio_p3 += f"- **KCs em Comum:** {kcs_comuns_str}\n"
    relatorio_p3 += f"- **Metáfora da Carta:** \"{carta_cenario.get('texto_efeito', '')}\"\n\n"

    prompt = f"""
    **Tarefa de Simulação de Raciocínio (Jogo: Code Sandwich)**
    **Contexto:** Simule o processo mental de um jogador iniciante.
    **Cenário:**
    O jogador está tentando completar a Receita Final '{receita_cenario.get('nome')}' (KCs: {kcs_receita_str}).
    Ele possui a Carta '{carta_cenario.get('nome')}' (Tipo: {carta_cenario.get('tipo')}, KCs: {kcs_carta_str}) na mão.
    A metáfora da carta é: "{carta_cenario.get('texto_efeito', '')}".

    **Sua Avaliação (em português do Brasil):**
    1.  **Raciocínio:** Descreva o processo de raciocínio de um jogador iniciante ao tentar relacionar a metáfora da Carta com o Conceito(s) Alvo (KC) da Receita.
    2.  **Dificuldade:** O jogador terá dificuldade em fazer essa conexão? Por quê?
    3.  **Ação Sugerida:** Qual ação o jogador provavelmente tomará (usar a carta, descartar, ignorar)?
    **Formato:** Análise concisa em 1-2 parágrafos.
    """
    interpretacao_ia = await call_gemini_api(model, prompt)
    relatorio_p3 += f"**Análise da IA sobre o Raciocínio do Jogador:**\n{interpretacao_ia}\n"

    return relatorio_p3

async def run_analysis(gemini_model=None, config=None): # Adicionado config como argumento opcional
    """Função principal para executar a análise pedagógica."""
    print("Iniciando Análise de Coerência Pedagógica (ACP)...")

    # Usar config passado ou DEFAULT_GAME_CONFIG se config for None
    current_config = config if config else DEFAULT_GAME_CONFIG

    # Usar caminhos e nomes de ficheiro da configuração atual
    analysis_dir = current_config.get('analysis_directory', 'analises')
    cards_file = current_config.get('cards_file', 'cartas.json')
    kcs_file = current_config.get('kcs_file', 'kcs.json')
    report_file_path = current_config.get('full_acp_report_path', os.path.join(analysis_dir, 'RELATORIO_ACP.md'))


    os.makedirs(analysis_dir, exist_ok=True)

    # 1. Carrega dados
    print(f"Lendo arquivos: {cards_file}, {kcs_file}...")
    cartas = load_json_data(cards_file)
    kcs = load_json_data(kcs_file)

    if not cartas or not kcs:
        print("ERRO: Falha ao carregar dados. Análise ACP cancelada.")
        return

    # 2. Executa Pilares (assíncrono)
    print("Executando análises com IA...")

    # Pilar 1
    print("Preparando Pilar 1: Auditoria de Metáfora (com IA)...")
    p1_task = analisar_pilar_1_dinamico(gemini_model, cartas, kcs)

    # Pilar 2
    print("Preparando Pilar 2: Análise Curricular (com IA)...")
    p2_task = analisar_pilar_2_com_ia(gemini_model, cartas, kcs)

    # Pilar 3
    print("Preparando Pilar 3: Simulação de Raciocínio (com IA)...")
    p3_task = analisar_pilar_3_dinamico(gemini_model, cartas, kcs)

    p1_relatorio, p2_relatorio, p3_relatorio = await asyncio.gather(p1_task, p2_task, p3_task)

    # 3. Monta relatório
    relatorio_final = "# Relatório de Análise de Coerência Pedagógica (ACP)\n\n"
    relatorio_final += f"**Data da Análise:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    relatorio_final += f"**Baralho Analisado:** {cards_file}\n\n" # Usar nome do ficheiro lido
    relatorio_final += "---\n\n"
    relatorio_final += p1_relatorio
    relatorio_final += "\n---\n\n"
    relatorio_final += p2_relatorio
    relatorio_final += "\n---\n\n"
    relatorio_final += p3_relatorio

    # 4. Salva relatório
    try:
        with open(report_file_path, 'w', encoding='utf-8') as f: # Usar caminho da config
            f.write(relatorio_final)
        print("ANÁLISE PEDAGÓGICA CONCLUÍDA!")
        print(f"Relatório salvo em: {report_file_path}") # Usar caminho da config
    except IOError as e:
        print(f"ERRO: Não foi possível salvar o relatório ACP: {e}")

if __name__ == "__main__":
    # Este bloco não deve ser executado diretamente se for chamado de main.py
    # Mas se for, precisa de configuração do Gemini
    from utils import configure_gemini

    gemini_model = configure_gemini()
    if gemini_model:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # Passar DEFAULT_GAME_CONFIG para run_analysis quando executado standalone
        asyncio.run(run_analysis(gemini_model, DEFAULT_GAME_CONFIG))
    else:
        print("Análise ACP não pode ser executada: API Key do Gemini não configurada.")