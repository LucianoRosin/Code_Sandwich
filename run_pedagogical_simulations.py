"""
Script para rodar simulações com agentes pedagógicos e gerar logs enriquecidos
para treinamento do modelo de Knowledge Tracing.
"""

import csv
import os
import argparse
from tqdm import tqdm
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_sandwich.env import CodeSandwichEnv
from code_sandwich.pedagogical_agents import PedagogicalAgent
from config import DEFAULT_GAME_CONFIG


def run_pedagogical_simulation(deck_file, log_file, num_games, num_players, personas):
    """
    Roda simulações com agentes pedagógicos e salva logs enriquecidos.
    
    Args:
        deck_file: Arquivo de cartas
        log_file: Arquivo para salvar logs
        num_games: Número de jogos a simular
        num_players: Número de jogadores
        personas: Lista de personas para os agentes
    """
    print(f"\n{'='*60}")
    print(f"SIMULAÇÃO PEDAGÓGICA - Code Sandwich")
    print(f"{'='*60}")
    print(f"Jogos: {num_games}")
    print(f"Jogadores: {num_players}")
    print(f"Personas: {personas}")
    print(f"Baralho: {deck_file}")
    print(f"Log: {log_file}")
    print(f"{'='*60}\n")
    
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Cabeçalho do CSV enriquecido
    header = [
        'game_id',
        'player_id',
        'persona',
        'turn',
        'action_type',
        'card_id',
        'card_name',
        'kcs_involved',
        'recipe_id',
        'recipe_progress',
        'has_bugs',
        'hand_size',
        'optimal_action',
        'thinking_strategy',
        'success',
        'game_winner',
        'game_turns'
    ]
    
    try:
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            for game_id in tqdm(range(num_games), desc="Simulando Jogos"):
                # Configura ambiente
                env_config = {
                    'cards_file': deck_file,
                    'num_players': num_players,
                    'max_turns': DEFAULT_GAME_CONFIG.get('max_turns', 200)
                }
                env = CodeSandwichEnv(env_config)
                
                # Cria agentes pedagógicos
                agents = []
                for i in range(num_players):
                    persona = personas[i % len(personas)]
                    agent = PedagogicalAgent(
                        num_actions=env.num_actions,
                        persona=persona,
                        kcs_file=DEFAULT_GAME_CONFIG.get('kcs_file', 'kcs.json')
                    )
                    agents.append(agent)
                
                env.set_agents(agents)
                
                # Roda o jogo
                trajectories, payoffs = env.run(is_training=False)
                
                # Coleta dados do jogo
                winner_id = env.game.get_winner()
                game_turns = env.game.turn_count
                
                # Processa histórico de ações de cada agente
                for player_id, agent in enumerate(agents):
                    player = env.game.players[player_id]
                    
                    for turn_idx, action_info in enumerate(agent.action_history):
                        # Extrai informações da ação
                        # Salva KCs como string de lista Python para facilitar o eval() posterior
                        kcs_str = str(action_info['kcs_involved']) if action_info['kcs_involved'] else '[]'
                        
                        # Calcula progresso da receita
                        recipe_progress = 0.0
                        recipe_id = ''
                        if player.recipe_card:
                            recipe_id = player.recipe_card.nome
                            total_ingredients = len(player.recipe_card.ingredientes)
                            if total_ingredients > 0:
                                completed = len([c for c in player.result_area if c.nome in player.recipe_card.ingredientes])
                                recipe_progress = completed / total_ingredients
                        
                        # Determina tipo de ação
                        action_type = 'unknown'
                        card_id = ''
                        card_name = ''
                        
                        # Aqui seria ideal ter mais informações do histórico
                        # Por simplicidade, usamos os dados disponíveis
                        
                        row = [
                            game_id,
                            player_id,
                            agent.persona,
                            turn_idx,
                            action_type,
                            card_id,
                            card_name,
                            kcs_str,
                            recipe_id,
                            f"{recipe_progress:.2f}",
                            int(len(player.bugs) > 0),
                            len(player.hand),
                            int(action_info['is_optimal']),
                            action_info['thinking_strategy'],
                            int(action_info['is_optimal']),  # success = is_optimal
                            winner_id if winner_id is not None else -1,
                            game_turns
                        ]
                        
                        writer.writerow(row)
        
        print(f"\n{'='*60}")
        print(f"Simulação concluída!")
        print(f"Logs salvos em: {log_file}")
        print(f"{'='*60}\n")
        
        # Gera resumo
        generate_simulation_summary(log_file, agents)
        
    except Exception as e:
        print(f"\nERRO durante a simulação: {e}")
        import traceback
        traceback.print_exc()


def generate_simulation_summary(log_file, agents):
    """Gera resumo da simulação."""
    print("\n" + "="*60)
    print("RESUMO DA SIMULAÇÃO")
    print("="*60)
    
    for i, agent in enumerate(agents):
        summary = agent.get_knowledge_summary()
        print(f"\nAgente {i} ({summary['persona']}):")
        print(f"  Total de ações: {summary['total_actions']}")
        print(f"  Ações ótimas: {summary['optimal_actions']}")
        if summary['total_actions'] > 0:
            accuracy = (summary['optimal_actions'] / summary['total_actions']) * 100
            print(f"  Taxa de acerto: {accuracy:.2f}%")
        print(f"  Maestria média: {summary['average_mastery']:.3f}")
        print(f"  Estado de conhecimento:")
        for kc, mastery in sorted(summary['knowledge_state'].items()):
            print(f"    {kc}: {mastery:.3f}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Roda simulações pedagógicas do Code Sandwich"
    )
    
    parser.add_argument('--deck_file', type=str,
                       default=DEFAULT_GAME_CONFIG.get('cards_file', 'cartas.json'),
                       help='Caminho para o arquivo JSON do baralho')
    
    parser.add_argument('--num_players', type=int,
                       default=DEFAULT_GAME_CONFIG.get('num_players', 2),
                       help='Número de jogadores (2-4)')
    
    parser.add_argument('--log_file', type=str,
                       default='logs/pedagogical_simulation_logs.csv',
                       help='Caminho para salvar o CSV de logs')
    
    parser.add_argument('--num_games', type=int,
                       default=100,
                       help='Número de jogos a simular')
    
    parser.add_argument('--personas', type=str,
                       default='Novice,Intermediate,Expert',
                       help='Personas separadas por vírgula (Novice, Intermediate, Expert)')
    
    args = parser.parse_args()
    
    # Processa personas
    personas = [p.strip() for p in args.personas.split(',')]
    valid_personas = ['Novice', 'Intermediate', 'Expert']
    personas = [p for p in personas if p in valid_personas]
    
    if not personas:
        print("ERRO: Nenhuma persona válida fornecida")
        print(f"Personas válidas: {', '.join(valid_personas)}")
        sys.exit(1)
    
    # Valida num_players
    if not 2 <= args.num_players <= 4:
        print(f"ERRO: Número de jogadores inválido ({args.num_players}). Deve ser entre 2 e 4.")
        sys.exit(1)
    
    # Roda simulação
    run_pedagogical_simulation(
        deck_file=args.deck_file,
        log_file=args.log_file,
        num_games=args.num_games,
        num_players=args.num_players,
        personas=personas
    )
