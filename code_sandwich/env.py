import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from rlcard.envs.env import Env
from .game import CodeSandwichGame
from .card import Card
# Assuming config.py exists and has DEFAULT_GAME_CONFIG
from config import DEFAULT_GAME_CONFIG


class CodeSandwichEnv(Env):
    """Ambiente RLCard para o jogo Code Sandwich."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o ambiente.

        Args:
            config: Configurações do ambiente
        """
        if config is None:
            config = DEFAULT_GAME_CONFIG.copy()

        config.setdefault("allow_step_back", False)
        config.setdefault("seed", None)

        self.num_players = config.get("num_players", 2) # Default to 2 if not provided
        self.cards_file = config.get("cards_file", "cartas.json") # Default file if not provided

        self.game = CodeSandwichGame(
            num_players=self.num_players,
            cards_file=self.cards_file
        )

        self.name = "code-sandwich"
        # state_shape and num_actions are set *after* super().__init__
        super().__init__(config)
        # We need to set these *after* super().__init__ has run and self.game exists
        self.state_shape = [[self._get_state_size()]] # rlcard expects list of lists for shape
        self.num_actions = self.game.get_num_actions()


    def _get_state_size(self) -> int:
        """
        Calcula o tamanho do vetor de estado (observação numérica).
        Needs to match the output of _extract_state['obs']
        """
        # 5 (game general) + 4 (player specific) + 6 (hand types) + 4 (result types) + (N-1) * 4 (opponents public)
        # Make sure num_players is correctly fetched
        num_players = self.num_players if hasattr(self, 'num_players') else 2 # Safe default
        return 5 + 4 + 6 + 4 + (num_players - 1) * 4

    def _extract_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai o estado numérico (obs) e ações legais (índices) do estado bruto do jogo.
        Este é o método que faltava, exigido pela rlcard.Env.

        Args:
            state (Dict): O dicionário de estado bruto retornado por game.get_state().

        Returns:
            Dict: Dicionário contendo {'obs': np.ndarray, 'legal_actions': List[int]}
        """
        if not state:
             # Return a default empty state matching the shape
             obs = np.zeros(self._get_state_size(), dtype=np.float32)
             legal_actions = []
             return {'obs': obs, 'legal_actions': legal_actions}


        player_id = state.get('player_id', 0) # Use player_id from raw state
        game_info = state.get('game_info', {}) # Use the general game info part

        # --- Construção do Vetor de Observação ('obs') ---
        obs_vector = []

        is_discard_phase = 1 if game_info.get('phase') == 'discard' else 0
        obs_vector.extend([
            game_info.get('current_player', 0),
            game_info.get('turn_count', 0),
            game_info.get('main_deck_size', 0),
            game_info.get('discard_pile_size', 0),
            is_discard_phase,
        ]) # 5 features gerais

        obs_vector.extend([
            len(state.get('hand', [])),
            len(state.get('result_area', [])),
            len(state.get('bugs', [])),
            int(state.get('recipe') is not None)
        ]) # 4 features do jogador

        # Hand types calculation (handle card dicts or strings)
        hand_types = {"Pão": 0, "Proteína": 0, "Vegetal": 0, "Condimento": 0, "Ação": 0, "Coringa": 0}
        raw_hand = state.get('hand', [])
        for card_repr in raw_hand:
             card_type = None
             if isinstance(card_repr, dict):
                 card_type = card_repr.get('tipo')
             # Add elif isinstance(card_repr, str): to parse string if needed
             if card_type in hand_types:
                 hand_types[card_type] += 1
        obs_vector.extend(list(hand_types.values())) # 6 features de tipos na mão

        # Result types calculation (handle card dicts or strings)
        result_types = {"Pão": 0, "Proteína": 0, "Vegetal": 0, "Condimento": 0}
        raw_result = state.get('result_area', [])
        for card_repr in raw_result:
             card_type = None
             if isinstance(card_repr, dict):
                 card_type = card_repr.get('tipo')
             # Add elif isinstance(card_repr, str): to parse string if needed
             if card_type in result_types:
                 result_types[card_type] += 1
        obs_vector.extend(list(result_types.values())) # 4 features de tipos na área resultado


        # Opponent info (using the public part from get_state)
        opponents_public = state.get('opponents_public', [])
        opponent_count = 0
        num_players = self.num_players if hasattr(self, 'num_players') else 2
        for opp_info in opponents_public:
             if opponent_count < (num_players - 1):
                  obs_vector.extend([
                      opp_info.get('hand_size', 0),
                      opp_info.get('result_size', 0),
                      opp_info.get('bugs_count', 0),
                      int(opp_info.get('has_recipe', False))
                  ]) # 4 features por oponente
                  opponent_count += 1
        # Pad opponent slots if fewer opponents than num_players - 1
        while opponent_count < (num_players - 1):
             obs_vector.extend([0, 0, 0, 0])
             opponent_count += 1


        # Pad vector if it's shorter than expected size
        target_size = self._get_state_size()
        while len(obs_vector) < target_size:
            obs_vector.append(0)

        obs = np.array(obs_vector[:target_size], dtype=np.float32)

        # --- Extração das Ações Legais (Índices) ---
        # A chave 'legal_actions' no estado bruto *já* contém os dicionários detalhados das ações
        raw_legal_actions_list = state.get('legal_actions', [])
        legal_action_indices = list(range(len(raw_legal_actions_list)))
        # --- CORREÇÃO: Cria o dicionário como esperado pelo DQNAgent ---
        legal_actions_dict = {action_index: None for action_index in legal_action_indices}

        return {'obs': obs, 'legal_actions': legal_actions_dict} # Retorna o dicionário

    # get_state agora DELEGA para o game e _extract_state
    def get_state(self, player_id: int) -> Dict[str, Any]:
        """
        Retorna o estado processado (obs, legal_actions) para a rlcard.
        Mantém a compatibilidade com a chamada esperada pela rlcard base class.
        """
        if not hasattr(self, 'game') or self.game is None:
             # Handle case where get_state is called before reset?
             # Return default empty state
             return self._extract_state({})

        raw_state = self.game.get_state(player_id)
        return self._extract_state(raw_state)

    def reset(self) -> Tuple[Dict[str, Any], int]: # Retorna Dict agora
        """
        Reinicia o jogo.

        Returns:
            Tupla com (estado_inicial_dict, jogador_inicial)
        """
        self.game = CodeSandwichGame(
            num_players=self.num_players,
            cards_file=self.cards_file
        )
        self.game.start_turn() # Start first turn (draws card)

        player_id = self.game.get_current_player_id()
        # Get the RAW state dict from the game for the *current* player
        raw_state = self.game.get_state(player_id)

        # Extract the standard obs and legal_actions using the new method
        extracted_state = self._extract_state(raw_state)

        # Construct the full dictionary needed by agents using use_raw=True
        state_dict_for_agent = {
            'obs': extracted_state['obs'],
            'legal_actions': extracted_state['legal_actions'],
            'raw_legal_actions': raw_state.get('legal_actions', []), # Raw actions from game state
            'player': self.game.get_current_player() # Current Player object
        }

        return state_dict_for_agent, player_id

    def step(self, action: int, use_raw: bool = False) -> Tuple[Dict[str, Any], int]: # Retorna Dict agora
        """
        Executa uma ação no jogo.
        """
        current_player_id = self.game.get_current_player_id()
        current_player = self.game.get_current_player()
        # Get raw legal actions for the current player to find the action data
        # Use get_state to ensure consistency? No, get_legal_actions is simpler here.
        raw_legal_actions = self.game.get_legal_actions(current_player)

        if action < 0 or action >= len(raw_legal_actions):
            # If action index is invalid, default to 'pass'
            print(f"Warning: Invalid action index {action} received. Max is {len(raw_legal_actions)-1}. Defaulting to pass.")
            action_data = {'type': 'pass'}
            # Find the index for the actual pass action if possible
            pass_idx = next((i for i, a in enumerate(raw_legal_actions) if a.get('type') == 'pass'), -1)
            if pass_idx != -1:
                 action = pass_idx # Correct the action index if defaulting to pass
            else:
                 # If somehow pass action isn't available, this might cause issues
                 pass
        else:
            action_data = raw_legal_actions[action]

        # Execute the step in the game logic
        self.game.step(action_data)

        # Determine the next player
        next_player_id = self.game.get_current_player_id()
        next_player_obj = self.game.get_current_player()

        # Get the RAW state dict for the next player
        next_raw_state = self.game.get_state(next_player_id)

        # Extract standard obs and legal actions for rlcard internal use
        extracted_next_state = self._extract_state(next_raw_state)

        # Construct the state dict needed by the HeuristicAgent (using use_raw=True)
        next_state_dict_for_agent = {
            'obs': extracted_next_state['obs'],
            'legal_actions': extracted_next_state['legal_actions'],
            'raw_legal_actions': next_raw_state.get('legal_actions', []),
            'player': next_player_obj
        }

        return next_state_dict_for_agent, next_player_id


    def get_legal_actions(self) -> List[int]:
        """
        Retorna os *índices* das ações legais para o jogador atual.
        Usado internamente pela rlcard, baseado no estado *atual*.
        """
        if not hasattr(self, 'game') or self.game is None:
             return []
        current_player = self.game.get_current_player()
        raw_legal_actions = self.game.get_legal_actions(current_player)
        return list(range(len(raw_legal_actions)))

    def is_over(self) -> bool:
        """
        Verifica se o jogo terminou.
        """
        if not hasattr(self, 'game') or self.game is None:
             return True # If no game, it's over?
        return self.game.is_over()

    def get_payoffs(self) -> List[float]:
        """
        Retorna as recompensas para cada jogador.
        """
        num_players = self.num_players if hasattr(self, 'num_players') else 2
        if not hasattr(self, 'game') or self.game is None or not self.is_over():
            return [0.0] * num_players

        payoffs = [-1.0] * num_players # Default loss
        winner = self.game.get_winner()

        if winner is not None:
            payoffs[winner] = 1.0
        else:
             # If game is over but no winner (e.g., turn limit draw)
             # rlcard typically uses 0 for draws
             if self.game.game_over and self.game.winner is None:
                 return [0.0] * num_players

        return payoffs

    def get_perfect_information(self) -> Dict[str, Any]:
        """
        Retorna informações completas do jogo (para debug).
        """
        if not hasattr(self, 'game') or self.game is None:
             return {}
        # Return raw state of current player seems reasonable for debug
        return self.game.get_state(self.game.get_current_player_id())

    # Properties expected by rlcard Env
    @property
    def num_actions(self) -> int:
        """Número de ações possíveis (upper bound)."""
        return self.game.get_num_actions() if hasattr(self, 'game') and self.game else 150 # Default during init
    @num_actions.setter
    def num_actions(self, value: int):
        pass # Let it be derived from the game

    @property
    def state_shape(self) -> List[List[int]]: # Needs to be List[List[int]]
        """Formato do vetor de estado."""
        return [[self._get_state_size()]] if hasattr(self, 'game') and self.game else [[1]] # Default during init
    @state_shape.setter
    def state_shape(self, value: List[List[int]]):
        pass # Let it be derived