# code_sandwich/pedagogical_agents.py
"""
Agentes Pedagógicos para Code Sandwich
Simulam jogadores com diferentes níveis de conhecimento (Novato, Intermediário, Especialista)
Baseado em: Hooshyar et al. (2022) - GameDKT: Deep knowledge tracing in educational games
"""

import random
from typing import Dict, Any, Tuple, List
import json
import os


class PedagogicalAgent:
    """
    Agente que simula um jogador com uma persona e estado de conhecimento específico.
    
    Personas:
    - Novice: Baixa maestria (0.1-0.4), comete muitos erros
    - Intermediate: Maestria média (0.4-0.7), comete erros ocasionais
    - Expert: Alta maestria (0.7-1.0), raramente erra
    """
    
    def __init__(self, num_actions: int, persona: str = "Novice", kcs_file: str = "kcs.json"):
        """
        Inicializa o agente pedagógico.
        
        Args:
            num_actions: Número de ações possíveis no ambiente
            persona: Nível do jogador ("Novice", "Intermediate", "Expert")
            kcs_file: Caminho para o arquivo JSON com definições dos KCs
        """
        self.num_actions = num_actions
        self.use_raw = True  # Necessário para rlcard
        self.persona = persona
        
        # Carrega informações dos KCs
        self.kcs_info = self._load_kcs(kcs_file)
        
        # Inicializa o estado de conhecimento
        self.knowledge_state = self._initialize_knowledge_state()
        
        # Parâmetros de erro baseados na persona
        self.error_params = self._get_error_params()
        
        # Histórico de jogadas (para análise)
        self.action_history = []
        
    def _load_kcs(self, kcs_file: str) -> Dict:
        """Carrega informações dos KCs do arquivo JSON."""
        if os.path.exists(kcs_file):
            with open(kcs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Fallback: KCs padrão se o arquivo não existir
            return {
                "KC1_sequencia": {"dificuldade": 1},
                "KC2_loop": {"dificuldade": 3},
                "KC3_condicional": {"dificuldade": 2},
                "KC4_debug": {"dificuldade": 2},
                "KC5_funcao": {"dificuldade": 4}
            }
    
    def _initialize_knowledge_state(self) -> Dict[str, float]:
        """
        Inicializa a maestria dos KCs com base na persona.
        Maestria é um valor entre 0 (nenhum conhecimento) e 1 (domínio completo).
        """
        knowledge = {}
        for kc_id in self.kcs_info.keys():
            if self.persona == "Novice":
                # Novatos: maestria baixa com variação
                knowledge[kc_id] = random.uniform(0.1, 0.4)
            elif self.persona == "Intermediate":
                # Intermediários: maestria média
                knowledge[kc_id] = random.uniform(0.4, 0.7)
            else:  # Expert
                # Especialistas: maestria alta
                knowledge[kc_id] = random.uniform(0.7, 1.0)
        return knowledge
    
    def _get_error_params(self) -> Dict[str, float]:
        """Define parâmetros de erro baseados na persona."""
        if self.persona == "Novice":
            return {
                'base_error_rate': 0.4,      # 40% de chance base de erro
                'strategy_adherence': 0.3,   # 30% de aderência à estratégia ótima
                'random_thinking_prob': 0.5  # 50% de chance de pensamento aleatório
            }
        elif self.persona == "Intermediate":
            return {
                'base_error_rate': 0.2,      # 20% de chance base de erro
                'strategy_adherence': 0.6,   # 60% de aderência à estratégia
                'random_thinking_prob': 0.25 # 25% de chance de pensamento aleatório
            }
        else:  # Expert
            return {
                'base_error_rate': 0.05,     # 5% de chance base de erro
                'strategy_adherence': 0.9,   # 90% de aderência à estratégia
                'random_thinking_prob': 0.05 # 5% de chance de pensamento aleatório
            }
    
    def _get_action_kcs(self, action_data: Dict[str, Any]) -> List[str]:
        """
        Extrai os KCs associados a uma ação.
        
        Args:
            action_data: Dados da ação do estado
            
        Returns:
            Lista de IDs dos KCs associados
        """
        if 'card' in action_data and action_data['card'] is not None:
            card = action_data['card']
            if hasattr(card, 'kc_associado'):
                return card.kc_associado if card.kc_associado else []
        return []
    
    def _calculate_mastery_for_action(self, action_kcs: List[str]) -> float:
        """
        Calcula a maestria média do agente para os KCs de uma ação.
        
        Args:
            action_kcs: Lista de IDs dos KCs da ação
            
        Returns:
            Maestria média (0-1)
        """
        if not action_kcs:
            return 0.5  # Maestria neutra se não há KCs
        
        masteries = [self.knowledge_state.get(kc, 0.5) for kc in action_kcs]
        return sum(masteries) / len(masteries)
    
    def _get_optimal_action(self, state: Dict[str, Any]) -> int:
        """
        Determina a ação ótima usando heurísticas (similar ao HeuristicAgent).
        
        Args:
            state: Estado atual do jogo
            
        Returns:
            Índice da ação ótima
        """
        legal_actions = state['legal_actions']
        
        if not legal_actions:
            return 0
        
        action_map = {i: data for i, data in enumerate(state['raw_legal_actions'])}
        player = state['player']
        
        # Prioridade 1: Jogar ingrediente correto da receita
        if player.recipe_card and player.recipe_card.ingredientes:
            recipe_reqs = player.recipe_card.ingredientes
            current_progress = [card.nome for card in player.result_area]
            
            if len(current_progress) < len(recipe_reqs):
                next_ingredient_needed = recipe_reqs[len(current_progress)]
                
                for idx, action_data in action_map.items():
                    if action_data['type'] == 'play_ingredient' and action_data['card'].nome == next_ingredient_needed:
                        return idx
        
        # Prioridade 2: Usar Debug se houver bugs
        if player.bugs:
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_action' and action_data['card'].categoria_acao == 'Debug':
                    return idx
        
        # Prioridade 3: Comprar cartas se a mão estiver vazia
        if len(player.hand) <= 2:
            card_drawing_actions = ["Ordem Perfeita", "Loop da Sorte", "Fundamento Sólido", "Sub-rotina de Preparo"]
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_action' and action_data['card'].nome in card_drawing_actions:
                    return idx
        
        # Prioridade 4: Jogar ingrediente da receita (mesmo que fora de ordem)
        if player.recipe_card and player.recipe_card.ingredientes:
            for idx, action_data in action_map.items():
                if action_data['type'] == 'play_ingredient':
                    if action_data['card'].nome in player.recipe_card.ingredientes:
                        return idx
        
        # Prioridade 5: Jogar carta de ação
        action_cards = [idx for idx, data in action_map.items() if data['type'] == 'play_action']
        if action_cards:
            return random.choice(action_cards)
        
        # Prioridade 6: Jogar ingrediente qualquer
        ingredient_actions = [idx for idx, data in action_map.items() if data['type'] == 'play_ingredient']
        if ingredient_actions:
            return random.choice(ingredient_actions)
        
        # Prioridade 7: Passar
        pass_action = [idx for idx, data in action_map.items() if data['type'] == 'pass']
        if pass_action:
            return pass_action[0]
        
        # Fallback
        if action_map:
            return random.choice(list(action_map.keys()))
        
        return 0
    
    def _should_make_error(self, action_kcs: List[str]) -> bool:
        """
        Decide se o agente deve cometer um erro com base na maestria e persona.
        
        Args:
            action_kcs: Lista de KCs da ação ótima
            
        Returns:
            True se deve cometer erro, False caso contrário
        """
        # Calcula maestria para a ação
        mastery = self._calculate_mastery_for_action(action_kcs)
        
        # Probabilidade de erro é inversamente proporcional à maestria
        error_prob = (1 - mastery) * self.error_params['base_error_rate']
        
        return random.random() < error_prob
    
    def _choose_thinking_strategy(self) -> str:
        """
        Escolhe a estratégia de pensamento (random vs parallel).
        
        Returns:
            "random" ou "parallel"
        """
        if random.random() < self.error_params['random_thinking_prob']:
            return "random"
        else:
            return "parallel"
    
    def _choose_erroneous_action(self, state: Dict[str, Any], optimal_action_id: int) -> int:
        """
        Seleciona uma ação errada de forma pedagogicamente relevante.
        
        Args:
            state: Estado atual do jogo
            optimal_action_id: ID da ação ótima
            
        Returns:
            Índice da ação errada escolhida
        """
        legal_actions = list(state['legal_actions'].keys())
        
        # Remove a ação ótima
        erroneous_options = [action for action in legal_actions if action != optimal_action_id]
        
        if not erroneous_options:
            return optimal_action_id
        
        # Estratégia de erro baseada na persona
        thinking_strategy = self._choose_thinking_strategy()
        
        if thinking_strategy == "random":
            # Pensamento aleatório: escolhe qualquer ação
            return random.choice(erroneous_options)
        else:
            # Pensamento paralelo: tenta uma ação que faça algum sentido
            # (ex: jogar um ingrediente, mesmo que errado)
            action_map = {i: data for i, data in enumerate(state['raw_legal_actions'])}
            
            # Prefere ações do mesmo tipo que a ótima
            optimal_type = action_map[optimal_action_id]['type']
            same_type_actions = [idx for idx in erroneous_options 
                                if action_map[idx]['type'] == optimal_type]
            
            if same_type_actions:
                return random.choice(same_type_actions)
            else:
                return random.choice(erroneous_options)
    
    def step(self, state: Dict[str, Any]) -> int:
        """
        Escolhe uma ação com base no estado e na persona do agente.
        
        Args:
            state: Estado atual do jogo
            
        Returns:
            Índice da ação escolhida
        """
        # Determina a ação ótima
        optimal_action = self._get_optimal_action(state)
        
        # Extrai KCs da ação ótima
        action_map = {i: data for i, data in enumerate(state['raw_legal_actions'])}
        optimal_action_data = action_map.get(optimal_action, {})
        action_kcs = self._get_action_kcs(optimal_action_data)
        
        # Decide se vai errar
        if self._should_make_error(action_kcs):
            chosen_action = self._choose_erroneous_action(state, optimal_action)
            is_optimal = False
        else:
            chosen_action = optimal_action
            is_optimal = True
        
        # Registra no histórico
        self.action_history.append({
            'optimal_action': optimal_action,
            'chosen_action': chosen_action,
            'is_optimal': is_optimal,
            'kcs_involved': action_kcs,
            'thinking_strategy': self._choose_thinking_strategy()
        })
        
        return chosen_action
    
    def eval_step(self, state: Dict[str, Any]) -> Tuple[int, Dict]:
        """
        Para avaliação, retorna tupla (action, info_dict) conforme API da rlcard.
        
        Args:
            state: Estado atual do jogo
            
        Returns:
            Tupla (ação escolhida, dicionário de informações)
        """
        action = self.step(state)
        return action, {}
    
    def update_knowledge(self, kc_id: str, success: bool, learning_rate: float = 0.05):
        """
        Atualiza o estado de conhecimento do agente (simula aprendizado).
        
        Args:
            kc_id: ID do KC a atualizar
            success: Se a aplicação do KC foi bem-sucedida
            learning_rate: Taxa de aprendizado (quanto aumenta/diminui a maestria)
        """
        if kc_id not in self.knowledge_state:
            return
        
        current_mastery = self.knowledge_state[kc_id]
        
        if success:
            # Aumenta maestria, mas com retornos decrescentes
            increment = learning_rate * (1 - current_mastery)
            self.knowledge_state[kc_id] = min(1.0, current_mastery + increment)
        else:
            # Diminui maestria levemente
            decrement = learning_rate * 0.5
            self.knowledge_state[kc_id] = max(0.0, current_mastery - decrement)
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo do estado de conhecimento do agente.
        
        Returns:
            Dicionário com informações sobre o conhecimento
        """
        return {
            'persona': self.persona,
            'knowledge_state': self.knowledge_state.copy(),
            'average_mastery': sum(self.knowledge_state.values()) / len(self.knowledge_state),
            'total_actions': len(self.action_history),
            'optimal_actions': sum(1 for a in self.action_history if a['is_optimal'])
        }
