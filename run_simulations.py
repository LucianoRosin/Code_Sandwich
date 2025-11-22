"""
Script para executar simulações do Code Sandwich
Suporta agentes heurísticos e pedagógicos
"""

import argparse
import os
import sys
import csv
from tqdm import tqdm

from code_sandwich.env import CodeSandwichEnv
from code_sandwich.heuristic_agent import HeuristicAgent
from config import DEFAULT_GAME_CONFIG

def run_simulations(
    num_games=1000,
    log_file='logs/simulation_logs.csv',
    agent_type='heuristic',
    personas=None,
    kcs_file='kcs.json',
    cards_file='cartas.json'
):
    """
    Executa simulações do jogo.
    
    Args:
        num_games: Número de jogos a simular
        log_file: Caminho para salvar logs
        agent_type: Tipo de agente ('heuristic' ou 'pedagogical')
        personas: Lista de personas para agentes pedagógicos (ex: ['Novice', 'Intermediate'])
        kcs_file: Arquivo de KCs
        cards_file: Arquivo de cartas
    """
    
    print(f"\n{'='*70}")
    print(f"EXECUTANDO SIMULAÇÕES - {agent_type.upper()}")
    print(f"{'='*70}")
    print(f"Número de jogos: {num_games}")
    print(f"Tipo de agente: {agent_type}")
    if agent_type == 'pedagogical' and personas:
        print(f"Personas: {', '.join(personas)}")
    print(f"Log: {log_file}")
    print(f"{'='*70}\n")
    
    # Criar diretório de logs
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configurar ambiente
    env = CodeSandwichEnv(config=DEFAULT_GAME_CONFIG)
    num_players = env.num_players
    
    # Criar agentes
    if agent_type == 'pedagogical':
        try:
            from code_sandwich.pedagogical_agents import PedagogicalAgent
            
            # Se não especificou personas, usar padrão
            if not personas:
                personas = ['Intermediate'] * num_players
            
            # Garantir que temos personas para todos os jogadores
            if len(personas) < num_players:
                personas = personas + ['Intermediate'] * (num_players - len(personas))
            
            agents = []
            for i in range(num_players):
                persona = personas[i] if i < len(personas) else 'Intermediate'
                agent = PedagogicalAgent(
                    num_actions=env.num_actions,
                    persona=persona,
                    kcs_file=kcs_file
                )
                agents.append(agent)
            
            print(f"[OK] Agentes pedagogicos criados: {[a.persona for a in agents]}")
            
        except ImportError as e:
            print(f"ERRO: Não foi possível importar PedagogicalAgent: {e}")
            print("Usando agentes heurísticos como fallback...")
            agent_type = 'heuristic'
            agents = [HeuristicAgent(num_actions=env.num_actions) for _ in range(num_players)]
    else:
        agents = [HeuristicAgent(num_actions=env.num_actions) for _ in range(num_players)]
        print(f"[OK] Agentes heuristicos criados: {num_players}")
    
    env.set_agents(agents)
    
    # Abrir arquivo de log
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Definir campos do CSV
        if agent_type == 'pedagogical':
            fieldnames = [
                'game_id', 'player_id', 'turn', 'action_type', 'card_played',
                'recipe_id', 'success', 'kcs_involved', 'optimal_action',
                'persona', 'game_turns'
            ]
        else:
            fieldnames = [
                'game_id', 'player_id', 'turn', 'action_type', 'card_played',
                'recipe_id', 'success', 'game_turns'
            ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Executar simulações
        for game_id in tqdm(range(num_games), desc="Simulando jogos"):
            try:
                state, player_id = env.reset()
                done = False
                turn = 0
                max_turns = 1000
                
                while not done and turn < max_turns:
                    # Obter ação do agente
                    agent = agents[player_id]
                    action = agent.eval_step(state)
                    
                    # Executar ação
                    next_state, player_id_next = env.step(action, raw_action=False)
                    
                    # Verificar se o jogo terminou
                    done = env.is_over()
                    
                    # Registrar log
                    log_entry = {
                        'game_id': game_id,
                        'player_id': player_id,
                        'turn': turn,
                        'action_type': 'unknown',
                        'card_played': 'unknown',
                        'recipe_id': 'unknown',
                        'success': 1 if not done else 0,
                        'game_turns': turn + 1
                    }
                    
                    # Adicionar campos específicos de agentes pedagógicos
                    if agent_type == 'pedagogical':
                        log_entry['kcs_involved'] = '[]'
                        log_entry['optimal_action'] = 0
                        log_entry['persona'] = agent.persona
                    
                    writer.writerow(log_entry)
                    
                    # Próximo turno
                    state = next_state
                    player_id = player_id_next
                    turn += 1
                
            except Exception as e:
                print(f"\nERRO no jogo {game_id}: {e}")
                continue
    
    print(f"\n[OK] Simulacoes concluidas!")
    print(f"  Log salvo em: {log_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Executar simulações do Code Sandwich')
    
    parser.add_argument('--num_games', type=int, default=1000,
                        help='Número de jogos a simular (padrão: 1000)')
    
    parser.add_argument('--log_file', type=str, default='logs/simulation_logs.csv',
                        help='Caminho para salvar logs (padrão: logs/simulation_logs.csv)')
    
    parser.add_argument('--agent_type', type=str, default='heuristic',
                        choices=['heuristic', 'pedagogical'],
                        help='Tipo de agente: heuristic ou pedagogical (padrão: heuristic)')
    
    parser.add_argument('--personas', type=str, default=None,
                        help='Personas separadas por vírgula (ex: Novice,Intermediate,Expert)')
    
    parser.add_argument('--kcs_file', type=str, default='kcs.json',
                        help='Arquivo de KCs (padrão: kcs.json)')
    
    parser.add_argument('--cards_file', type=str, default='cartas.json',
                        help='Arquivo de cartas (padrão: cartas.json)')
    
    args = parser.parse_args()
    
    # Processar personas
    personas_list = None
    if args.personas:
        personas_list = [p.strip() for p in args.personas.split(',')]
    
    # Executar simulações
    run_simulations(
        num_games=args.num_games,
        log_file=args.log_file,
        agent_type=args.agent_type,
        personas=personas_list,
        kcs_file=args.kcs_file,
        cards_file=args.cards_file
    )
