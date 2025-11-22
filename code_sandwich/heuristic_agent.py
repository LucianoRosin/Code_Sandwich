"""
Implementação do Agente Heurístico para o jogo Code Sandwich.
"""

import random
from typing import List, Dict, Any, Optional, Tuple

from .card import Card
from .player import Player

class HeuristicAgent:
    """
    Agente que joga com base em um conjunto de regras pré-definidas (heurísticas).
    """

    def __init__(self, num_actions: int):
        """
        Inicializa o agente.

        Args:
            num_actions: Número de ações possíveis no ambiente.
        """
        self.num_actions = num_actions
        # Informa à 'rlcard' que este agente precisa do dicionário 'state' completo
        self.use_raw = True
    def step(self, state: Dict[str, Any]) -> int:
        """
        Escolhe uma ação com base no estado atual e nas heurísticas.

        Args:
            state: Dicionário com as informações do estado do jogo.

        Returns:
            O índice da ação escolhida.
        """
        legal_actions = state['legal_actions']
        
        if not legal_actions:
            return 0

        action_map = {i: data for i, data in enumerate(state['raw_legal_actions'])}

        player: Player = state['player']
        if player.recipe_card and player.recipe_card.ingredientes:
            recipe_reqs = player.recipe_card.ingredientes
            current_progress = [card.nome for card in player.result_area]
            
            if len(current_progress) < len(recipe_reqs):
                next_ingredient_needed = recipe_reqs[len(current_progress)]
                
                for idx, action_data in action_map.items():
                    if action_data['type'] == 'play_ingredient' and action_data['card'].nome == next_ingredient_needed:
                        return idx

        if player.bugs:
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_action' and action_data['card'].categoria_acao == 'Debug':
                    return idx

        if len(player.hand) <= 2:
            card_drawing_actions = ["Ordem Perfeita", "Loop da Sorte", "Fundamento Sólido", "Sub-rotina de Preparo"]
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_action' and action_data['card'].nome in card_drawing_actions:
                    return idx

        if player.recipe_card and player.recipe_card.ingredientes:
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_ingredient':
                    if action_data['card'].nome in player.recipe_card.ingredientes:
                        return idx
        
        action_cards = [idx for idx, data in action_map.items() if data['type'] == 'play_action']
        if action_cards:
            return random.choice(action_cards)

        ingredient_actions = [idx for idx, data in action_map.items() if data['type'] == 'play_ingredient']
        if ingredient_actions:
            return random.choice(ingredient_actions)
            
        pass_action = [idx for idx, data in action_map.items() if data['type'] == 'pass']
        if pass_action:
            return pass_action[0]
        
        # Garante que sempre retorne uma ação legal válida se o mapa não estiver vazio
        if action_map:
            return random.choice(list(action_map.keys()))
        
        # Fallback de segurança (deve ser a ação de 'passar', que geralmente é 0)
        return 0

    def eval_step(self, state: Dict[str, Any]) -> Tuple[int, Dict]:
        """
        Para avaliação, o agente heurístico se comporta da mesma maneira,
        mas retorna uma tupla (action, info_dict) conforme a API da rlcard.
        """
        action = self.step(state)
        return action, {}