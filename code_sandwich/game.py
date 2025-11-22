"""
Implementação principal do jogo Code Sandwich, com suporte para 4 jogadores
e logging enriquecido para análise pedagógica detalhada.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from .card import Card, CardDeck
from .player import Player


class CodeSandwichGame:
    """Classe principal do jogo Code Sandwich."""

    def __init__(self, num_players: int = 4, cards_file: str = None):
        """
        Inicializa o jogo.

        Args:
            num_players: Número de jogadores (2-4)
            cards_file: Caminho para o arquivo JSON com as cartas
        """
        if not 2 <= num_players <= 4:
            raise ValueError("O número de jogadores deve ser entre 2 e 4")

        self.num_players = num_players
        self.players: List[Player] = [Player(i) for i in range(num_players)]
        self.current_player_id = 0
        self.turn_count = 0
        self.game_over = False
        self.winner = None

        try:
            self.card_deck = CardDeck(cards_file)
        except FileNotFoundError:
            print(f"Erro Fatal: Arquivo de cartas '{cards_file}' não encontrado.")
            raise

        self.main_deck: List[Card] = []
        self.recipe_deck: List[Card] = []
        self.discard_pile: List[Card] = []

        self.phase = "setup"
        self.action_count = 0
        self.max_actions_per_turn = 1
        self.max_hand_size = 5

        self.allow_step_back = False

        self._setup_game()

    def _setup_game(self):
        """Configura o estado inicial do jogo."""
        self.main_deck = self.card_deck.get_main_deck().copy()
        recipe_pool = self.card_deck.get_recipe_deck().copy()

        random.shuffle(self.main_deck)

        if len(recipe_pool) >= self.num_players:
            self.recipe_deck = random.sample(recipe_pool, self.num_players)
        else:
            self.recipe_deck = recipe_pool
            random.shuffle(self.recipe_deck)

        for i, player in enumerate(self.players):
            if i < len(self.recipe_deck):
                player.set_recipe_card(self.recipe_deck[i])
            # Deal initial hand
            self.draw_card(player, self.max_hand_size)


        self.phase = "playing"
        # Não chama start_turn aqui para não comprar carta extra
        # O primeiro turno será iniciado pelo ambiente


    def start_turn(self):
        """Inicia o turno de um jogador com a fase de compra obrigatória."""
        if self.is_over():
            return # Don't start turn if game already ended

        player = self.get_current_player()
        self.draw_card(player, 1)
        # Reset action count for the turn maybe? Depends on rules. Assuming 1 action only.
        self.action_count = 0
        self.phase = "playing"


    def get_current_player_id(self) -> int:
        """Retorna o ID do jogador atual."""
        return self.current_player_id

    def get_current_player(self) -> Player:
        """Retorna o jogador atual."""
        if 0 <= self.current_player_id < len(self.players):
             return self.players[self.current_player_id]
        else:
             raise IndexError(f"Invalid current_player_id: {self.current_player_id}")


    def step(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação no jogo e retorna um log detalhado da ação.
        """
        if self.is_over():
             # Log that action was attempted after game over?
             return {'action_type': 'game_over', 'message': 'Action ignored, game over.'}

        player = self.get_current_player()
        action_type = action_data.get("type")

        if self.phase == "discard" and action_type != "discard":
             return {'action_type': 'illegal_phase', 'message': f'Tried {action_type} during discard phase.'}
        elif self.phase == "playing" and action_type == "discard":
             return {'action_type': 'illegal_phase', 'message': 'Tried discard during playing phase.'}


        kwargs = action_data.copy()

        action_type = kwargs.pop('type', None)
        if not action_type:
            return {'action_type': 'error', 'message': 'Missing action type.'}

        card = kwargs.pop('card', None) # Card object associated with the action

        action_log = {
            'action_type': action_type,
            'card_name': card.nome if card else 'N/A',
            'card_type': card.tipo if card else 'N/A',
            'target_player': kwargs.get('target_player_id'),
            'played_ingredient': kwargs.get('ingredient_name'),
            'position': kwargs.get('position'),
            'pos1': kwargs.get('pos1'),
            'pos2': kwargs.get('pos2'),
            'num_copies': kwargs.get('num_copies'),
            'target_ingredient_type': kwargs.get('target_ingredient_type'),
            'success': True,
            'message': ''
        }

        try:
            if action_type == "play_ingredient":
                if card and card.is_ingredient():
                    play_result = self.play_card(player, card, **kwargs)
                    action_log.update(play_result) # play_card returns success/message now
                else:
                    action_log['success'] = False
                    action_log['message'] = "Invalid card for play_ingredient."
                    self.end_action_phase()

            elif action_type == "play_action":
                if card and (card.is_action() or card.is_wildcard()):
                    play_result = self.play_card(player, card, **kwargs)
                    action_log.update(play_result)
                else:
                    action_log['success'] = False
                    action_log['message'] = "Invalid card for play_action."
                    self.end_action_phase()

            elif action_type == "pass":
                self.end_action_phase()
                action_log['message'] = "Player passed turn."

            elif action_type == "discard":
                if self.phase != "discard":
                     action_log['success'] = False
                     action_log['message'] = "Cannot discard now."
                elif card:
                    discarded = self.discard_from_hand(player, card)
                    if discarded:
                         action_log['message'] = f"Discarded {card.nome}."
                         # Check if discard phase is over *after* discarding
                         if len(player.hand) <= self.max_hand_size:
                             self.next_player() # Hand size OK, move to next player
                         else:
                             self.phase = "discard" # Stay in discard phase
                    else:
                         action_log['success'] = False
                         action_log['message'] = f"Card {card.nome} not found in hand to discard."
                         # Stay in discard phase if failed
                         self.phase = "discard"

                else:
                    action_log['success'] = False
                    action_log['message'] = "Discard action missing card."
                    self.phase = "discard" # Stay in discard phase if failed

            else:
                 action_log['success'] = False
                 action_log['message'] = f"Unknown action type: {action_type}"
                 self.end_action_phase()

        except Exception as e:
             # Catch unexpected errors during action processing
             print(f"ERROR during step execution: {e}")
             action_log['success'] = False
             action_log['message'] = f"Internal error during action: {e}"
             # Try to recover by ending the action phase?
             if not self.is_over():
                  try:
                       self.end_action_phase()
                  except Exception as e2:
                       print(f"ERROR during recovery end_action_phase: {e2}")
                       self.game_over = True # Force game over if recovery fails


        if not self.game_over:
             # Check victory for the player who just acted
             if player.check_victory_condition():
                 self.game_over = True
                 self.winner = player.player_id
                 self.phase = "game_over"
                 action_log['message'] += " Player wins!"


        return action_log

    def draw_card(self, player: Player, count: int = 1) -> List[Card]:
        """
        Faz um jogador comprar cartas do baralho principal. Handles deck reshuffling.
        Returns list of cards drawn (can be empty if deck is empty).
        """
        drawn_cards = []
        for _ in range(count):
            if not self.main_deck:
                if self.discard_pile:
                    #print("Reshuffling discard pile into deck.") # Optional debug log
                    self.main_deck = self.discard_pile[:]
                    self.discard_pile.clear()
                    random.shuffle(self.main_deck)
                else:
                    #print("Deck and discard pile are empty. Cannot draw.") # Optional debug log
                    # Game might end here based on rules if draw is required
                    break # Stop trying to draw
            if self.main_deck:
                try:
                    card = self.main_deck.pop(0) # Draw from the top
                    player.add_card_to_hand(card)
                    drawn_cards.append(card)
                except IndexError:
                     # Should not happen if self.main_deck check passed, but safety first
                     break
        return drawn_cards

    def discard_card(self, card: Card):
        """Descarta uma carta na pilha de descarte."""
        if card: # Avoid discarding None
             self.discard_pile.append(card)

    def discard_from_hand(self, player: Player, card: Card) -> bool: # Return bool for success
        """Remove uma carta da mão do jogador e a coloca na pilha de descarte."""
        # Need to handle removing the correct card *instance* if duplicates exist
        try:
             # Find the first matching card instance by identity or attributes if needed
             player.hand.remove(card)
             self.discard_card(card)
             return True
        except ValueError:
             # Card wasn't found in hand
             return False


    def play_card(self, player: Player, card: Card, **kwargs) -> Dict[str, Any]:
        """
        Executa o efeito de uma carta jogada. Returns result dict.
        Handles removing card from hand and discarding (unless moved elsewhere).
        """
        # Double check card is in hand before proceeding
        if card not in player.hand:
            # This check might be redundant if step() already checks, but good safeguard
            # If called internally, maybe raise error? If from step, return failure.
            self.end_action_phase() # Fail safe if reached here somehow
            return {"success": False, "message": "Carta não está na mão do jogador"}

        # Log initial state for debugging if needed
        # print(f"Player {player.player_id} playing {card.nome}. Hand before: {[c.nome for c in player.hand]}")

        result = {"success": True, "message": f"Jogou {card.nome}.", "effects": [], "log_info": {}}

        # Remove card from hand *first*
        try:
             player.hand.remove(card)
        except ValueError:
             # Should not happen if check above passed
             print(f"ERROR: Card {card.nome} was in hand check but not found for removal!")
             self.end_action_phase()
             return {"success": False, "message": "Erro interno ao remover carta da mão"}

        card_discarded = True # Assume card is discarded unless effect moves it

        try:
            if card.is_ingredient():
                # Check result area limit
                if len(player.result_area) < 10:
                    position = kwargs.get('position') # For specific placement if needed
                    player.add_card_to_result(card, position)
                    result["effects"].append(f"Ingrediente {card.nome} adicionado à área de resultado")
                    card_discarded = False # Ingredient moves to result area
                else:
                    result["success"] = False
                    result["message"] = f"Falha ao jogar {card.nome}: Área de resultado cheia."
                    card_discarded = True # Failed play, card goes to discard

            elif card.is_action():
                effect_log = self._execute_action_effect(player, card, result, **kwargs)
                result['log_info'].update(effect_log)
                # Check specific actions that don't discard the card
                if card.nome == "Erro de Sintaxe":
                     # Card moved to opponent's bug area in the effect method
                     card_discarded = False

            elif card.is_wildcard():
                effect_log = self._execute_wildcard_effect(player, card, result, **kwargs)
                result['log_info'].update(effect_log)
                # Check for failure cases like illegal Lançamento
                if card.nome == "Lançamento em Produção" and not result["success"]:
                    # The effect method should handle putting card back or state
                    # Let's assume failed play discards the card here
                    card_discarded = True

            # Discard the card if it wasn't moved elsewhere or if play failed
            if card_discarded:
                 self.discard_card(card)

        except Exception as e:
             # Catch errors during card effect execution
             print(f"ERROR executing effect for {card.nome}: {e}")
             result['success'] = False
             result['message'] = f"Erro ao executar efeito de {card.nome}: {e}"
             if card not in self.discard_pile and card not in player.result_area and card not in player.bugs: # Check if it ended up somewhere else
                  # Check opponents' bugs too? Complex. Assume discard on error for now.
                  self.discard_card(card)

        # Do NOT check victory here. Let step() handle it after play_card returns.
        # Do NOT call end_action_phase here. Let step() handle it.
        return result


    def _execute_action_effect(self, player: Player, card: Card, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Executa o efeito de uma carta de ação e retorna info para log."""
        log_info = {}
        nome = card.nome # The card being played

        if nome == "Ponto de Interrupção":
            target_player_id = kwargs.get('target_player_id', player.player_id) # Default to self
            if 0 <= target_player_id < self.num_players:
                 target_player = self.players[target_player_id]
                 # Call remove_bug *without* arguments, assuming it removes one bug (e.g., the first)
                 # and *returns* the Card object that was removed.
                 removed_bug_card = target_player.remove_bug()
                 if removed_bug_card:
                     # Discard the actual bug card object that was removed
                     self.discard_card(removed_bug_card)
                     log_info['target_player'] = target_player_id
                     result["effects"].append(f"Bug ({removed_bug_card.nome}) removido do Jogador {target_player_id}")
                 else:
                     result["effects"].append(f"Nenhum bug para remover do Jogador {target_player_id}")
            else:
                 result["effects"].append(f"ID de jogador alvo inválido: {target_player_id}")
        elif nome == "Ordem Perfeita":
            # Rule: Draw 3. Play all ingredients found in order. Discard others.
            drawn_cards = self.draw_card(player, 3)
            ingredients_to_play = []
            cards_to_discard = []
            for c in drawn_cards:
                 if c.is_ingredient():
                     ingredients_to_play.append(c)
                 else:
                     cards_to_discard.append(c)

            played_count = 0
            for ingredient in ingredients_to_play:
                 if len(player.result_area) < 10:
                    # Card was added to hand by draw_card, need to remove from hand
                    if player.remove_card_from_hand(ingredient):
                        player.add_card_to_result(ingredient)
                        result["effects"].append(f"Ordem Perfeita adicionou {ingredient.nome}")
                        played_count += 1
                    else:
                        print(f"Warning: Ordem Perfeita ingredient {ingredient.nome} not found in hand after draw?")
                 else:
                    # Result area full, discard instead of playing
                    if player.remove_card_from_hand(ingredient):
                         self.discard_card(ingredient)

            # Discard non-ingredients drawn by this effect
            for other_card in cards_to_discard:
                 if player.remove_card_from_hand(other_card):
                     self.discard_card(other_card)

        elif nome == "Fluxo Contínuo":
            # Rule: Play ingredient from hand without using action phase.
            ingredient_name = kwargs.get('ingredient_name')
            card_to_play_obj = kwargs.get('card_to_play_with') # Use object if passed

            card_to_play = card_to_play_obj if card_to_play_obj else next((c for c in player.hand if c.nome == ingredient_name and c.is_ingredient()), None)

            if card_to_play and card_to_play in player.hand: # Check it's actually in hand
                 if len(player.result_area) < 10:
                    player.remove_card_from_hand(card_to_play)
                    player.add_card_to_result(card_to_play)
                    log_info['played_ingredient'] = card_to_play.nome
                    result["effects"].append(f"Fluxo Contínuo jogou {card_to_play.nome}")
                    # This action does NOT end the phase automatically
                    # The main 'step' function or 'play_card' caller handles phase end
                 else:
                    result["effects"].append(f"Área de resultado cheia, não pôde usar Fluxo Contínuo com {card_to_play.nome}")
                    # Failed effect, Fluxo Continuo card itself is still discarded (handled by play_card)
            else:
                 result["effects"].append(f"Ingrediente para Fluxo Contínuo não encontrado na mão: {ingredient_name or 'N/A'}")


        elif nome == "Sub-rotina de Preparo":
            # Rule: Play ingredient from hand, then draw 1. Uses action phase.
            ingredient_name = kwargs.get('ingredient_name')
            card_to_play_obj = kwargs.get('card_to_play_with')

            card_to_play = card_to_play_obj if card_to_play_obj else next((c for c in player.hand if c.nome == ingredient_name and c.is_ingredient()), None)

            if card_to_play and card_to_play in player.hand:
                 if len(player.result_area) < 10:
                     player.remove_card_from_hand(card_to_play)
                     player.add_card_to_result(card_to_play)
                     drawn = self.draw_card(player, 1) # Draw card *after* playing
                     log_info['played_ingredient'] = card_to_play.nome
                     result["effects"].append(f"Sub-rotina jogou {card_to_play.nome} e comprou {len(drawn)} carta")
                 else:
                     result["effects"].append(f"Área de resultado cheia, não pôde usar Sub-rotina com {card_to_play.nome}")
                     # Failed effect, Sub-rotina card is discarded. Don't draw.
            else:
                 result["effects"].append(f"Ingrediente para Sub-rotina não encontrado na mão: {ingredient_name or 'N/A'}")
                 # Failed effect, Sub-rotina card is discarded. Don't draw.

        elif nome == "Erro de Sintaxe":
            # Rule: Add this card to opponent's bug area.
            target_player_id = kwargs.get('target_player_id')
            if target_player_id is not None and 0 <= target_player_id < self.num_players and target_player_id != player.player_id:
                target_player = self.players[target_player_id]
                # The 'card' object IS the Erro de Sintaxe card. Add it directly.
                target_player.add_bug(card)
                log_info['target_player'] = target_player_id
                result["effects"].append(f"Erro de Sintaxe adicionado ao Jogador {target_player_id}")
                # Card moves, not discarded. Flag handled in play_card.
            else:
                 result["success"] = False # Failed to apply effect
                 result["message"] = f"Alvo inválido para Erro de Sintaxe: {target_player_id}"
                 # Card will be discarded by play_card due to failure


        elif nome == "Valor Nulo":
             # Rule says discard anytime for 1 card, no action cost.
             # If played as action: Draw 1 card.
             drawn = self.draw_card(player, 1)
             result["effects"].append(f"Valor Nulo jogado como ação, comprou {len(drawn)} carta")

        elif nome == "Reorganizar Etapas":
            # Rule: Swap two *adjacent* ingredients in result area.
            pos1 = kwargs.get('pos1')
            pos2 = kwargs.get('pos2')
            # Validate positions passed from legal_actions
            if (pos1 is not None and pos2 is not None and
                abs(pos1 - pos2) == 1 and
                0 <= pos1 < len(player.result_area) and
                0 <= pos2 < len(player.result_area)):
                 swapped = player.swap_cards_in_result(pos1, pos2)
                 if swapped:
                     result["effects"].append(f"Ingredientes nas posições {pos1} e {pos2} trocados")
                 else:
                     # Should not fail if indices are valid, but maybe log?
                     result["effects"].append(f"Falha inesperada ao trocar posições {pos1} e {pos2}")
            else:
                 result["success"] = False
                 result["message"] = f"Posições inválidas para Reorganizar Etapas: {pos1}, {pos2}"

        elif nome == "Fundamento Sólido":
             # Rule: Discard a Bread from hand -> draw 2. Else, draw 1.
             bread_card = next((c for c in player.hand if c.tipo == "Pão"), None)
             if bread_card:
                  # Discard the specific bread card instance
                  discarded = self.discard_from_hand(player, bread_card)
                  if discarded:
                       drawn = self.draw_card(player, 2)
                       result["effects"].append(f"Descartou {bread_card.nome} e comprou {len(drawn)}")
                  else: # Bread disappeared? Should not happen. Draw 1.
                       drawn = self.draw_card(player, 1)
                       result["effects"].append(f"Erro ao descartar Pão, comprou {len(drawn)}")
             else: # No bread in hand
                  drawn = self.draw_card(player, 1)
                  result["effects"].append(f"Não tinha Pão, comprou {len(drawn)}")

        elif nome == "Ingrediente Secreto":
             # Rule: Name ingredient. Target checks hand. If found, give to player.
             target_player_id = kwargs.get('target_player_id')
             ingredient_name = kwargs.get('ingredient_name') # Agent MUST specify this

             if (target_player_id is not None and 0 <= target_player_id < self.num_players and
                 target_player_id != player.player_id and ingredient_name):
                  target_player = self.players[target_player_id]
                  # Find first matching card instance in target's hand
                  found_card = next((c for c in target_player.hand if c.nome == ingredient_name), None)
                  if found_card:
                       # Move card from target to player
                       if target_player.remove_card_from_hand(found_card):
                           player.add_card_to_hand(found_card)
                           result["effects"].append(f"Roubou {ingredient_name} do Jogador {target_player_id}")
                       else:
                           result["effects"].append(f"Erro ao remover {ingredient_name} da mão do Jogador {target_player_id}")
                  else:
                       result["effects"].append(f"Jogador {target_player_id} não tinha {ingredient_name}")
             else:
                  result["success"] = False
                  result["message"] = f"Alvo ou ingrediente inválido para Ingrediente Secreto."


        elif nome == "Alternativa Saudável":
            # Rule: Choose Protein/Bread in result. Replace with Veggie from hand. If so, draw 1.
            pos_to_replace = kwargs.get('position_to_replace')
            veggie_card_to_use = kwargs.get('veggie_card_from_hand') # Card object

            if (pos_to_replace is not None and veggie_card_to_use is not None and
                0 <= pos_to_replace < len(player.result_area) and
                veggie_card_to_use in player.hand and # Check specific instance
                veggie_card_to_use.tipo == "Vegetal"):

                 card_being_replaced = player.result_area[pos_to_replace]
                 if card_being_replaced.tipo in ["Proteína", "Pão"]:
                     # Perform the replacement
                     player.result_area[pos_to_replace] = veggie_card_to_use
                     # Remove veggie from hand (use discard_from_hand to handle discard pile)
                     # NO - veggie goes to result, not discard. Just remove from hand.
                     try:
                          player.hand.remove(veggie_card_to_use)
                     except ValueError:
                           result["success"] = False
                           result["message"] = "Erro: Vegetal desapareceu da mão."
                           # Attempt to revert? Complex. Let state be inconsistent for now.
                           return log_info # Exit early

                     # Discard the old card
                     self.discard_card(card_being_replaced)

                     # Draw a card
                     drawn = self.draw_card(player, 1)
                     result["effects"].append(f"Substituiu {card_being_replaced.nome}(pos {pos_to_replace}) por {veggie_card_to_use.nome}, comprou {len(drawn)}")
                 else:
                     result["success"] = False
                     result["message"] = f"Carta na posição {pos_to_replace} ({card_being_replaced.nome}) não era Proteína/Pão."
            else:
                 result["success"] = False
                 result["message"] = "Argumentos inválidos ou carta não encontrada para Alternativa Saudável."


        elif nome == "Ciclo de Sabor":
            # Rule: Choose ingredient name in result area. Search deck/discard for 1 or 2 copies, add to hand. Shuffle deck.
            ingredient_name_target = kwargs.get('ingredient_name_target')
            num_copies = kwargs.get('num_copies', 1)

            if ingredient_name_target and any(c.nome == ingredient_name_target for c in player.result_area):
                found_cards : List[Card] = []
                
                # Search Deck (preserve order for now, shuffle later)
                deck_copy = self.main_deck[:]
                self.main_deck.clear()
                for c in deck_copy:
                    if c.nome == ingredient_name_target and len(found_cards) < num_copies:
                        found_cards.append(c)
                    else:
                        self.main_deck.append(c) # Put back cards not taken

                # Search Discard if needed
                if len(found_cards) < num_copies:
                    discard_copy = self.discard_pile[:]
                    self.discard_pile.clear()
                    for c in discard_copy:
                        if c.nome == ingredient_name_target and len(found_cards) < num_copies:
                            found_cards.append(c)
                        else:
                            self.discard_pile.append(c) # Put back cards not taken
                
                # Add found cards to hand
                for c in found_cards:
                     player.add_card_to_hand(c)
                
                # Shuffle main deck
                random.shuffle(self.main_deck)
                result["effects"].append(f"Pegou {len(found_cards)} cópia(s) de {ingredient_name_target} para a mão. Baralho embaralhado.")
            else:
                 result["success"] = False
                 result["message"] = f"Ingrediente alvo '{ingredient_name_target}' não encontrado na área de resultado."


        elif nome == "Loop da Sorte":
             # Rule: Reveal top card. If Ingred, take to hand & REPEAT. Stop when non-Ingred revealed or player chooses.
             # VERY complex loop for agent/simulation.
             # Simplified: Reveal 1. If ingredient, take. If not, discard.
             if self.main_deck:
                  # Draw from top
                  top_card = self.main_deck.pop(0)
                  if top_card.is_ingredient():
                       player.add_card_to_hand(top_card)
                       result["effects"].append(f"Loop da Sorte (simplificado) pegou {top_card.nome}")
                  else:
                       self.discard_card(top_card)
                       result["effects"].append(f"Loop da Sorte (simplificado) revelou {top_card.nome} (não ingrediente), descartado")
             else:
                  result["effects"].append("Loop da Sorte: Baralho vazio")


        elif nome == "For Each de Ingrediente":
             # Rule: Count distinct ingredient types in result area. Draw that many cards.
             types_in_result = set(c.tipo for c in player.result_area if c.is_ingredient())
             num_to_draw = len(types_in_result)
             if num_to_draw > 0:
                 drawn = self.draw_card(player, num_to_draw)
                 result["effects"].append(f"Comprou {len(drawn)} cartas ({num_to_draw} tipos na área)")
             else:
                 result["effects"].append("Nenhum tipo de ingrediente na área, não comprou cartas")


        elif nome == "Variáveis Trocadas":
            # Rule: Choose opponent. Each secretly chooses Ingred from hand. Swap them.
            target_player_id = kwargs.get('target_player_id')
            # Agent needs to provide card_to_swap_player (Card obj from player hand)
            card_from_player = kwargs.get('card_from_player')
            # Agent also needs to *know* or guess opponent's card? Impossible for simple agent.
            # Simulation simplification: Assume agent can see opponent's hand to pick one.
            # card_from_opponent = kwargs.get('card_from_opponent') # Or maybe agent just gets a random one?

            if (target_player_id is not None and 0 <= target_player_id < self.num_players and
                target_player_id != player.player_id and card_from_player and card_from_player in player.hand and card_from_player.is_ingredient()):

                 target_player = self.players[target_player_id]
                 # Simplification: Target gives a random ingredient if they have one
                 target_ingredient = next((c for c in target_player.hand if c.is_ingredient()), None)

                 if target_ingredient:
                      # Perform swap
                      p_removed = player.remove_card_from_hand(card_from_player)
                      t_removed = target_player.remove_card_from_hand(target_ingredient)

                      if p_removed and t_removed:
                           player.add_card_to_hand(target_ingredient)
                           target_player.add_card_to_hand(card_from_player)
                           result["effects"].append(f"Trocou {card_from_player.nome} por {target_ingredient.nome} com Jogador {target_player_id}")
                      else:
                           # Put cards back if removal failed? Complex recovery.
                           result["success"] = False
                           result["message"] = "Erro ao remover cartas para troca."
                           # Attempt to return cards maybe?
                           if p_removed and not t_removed: player.add_card_to_hand(card_from_player)
                           if t_removed and not p_removed: target_player.add_card_to_hand(target_ingredient)
                 else:
                      result["effects"].append(f"Jogador {target_player_id} não tinha ingrediente para trocar.")
            else:
                 result["success"] = False
                 result["message"] = "Argumentos inválidos ou carta não encontrada para Variáveis Trocadas."


        elif nome == "Escopo Local":
            # Rule: Look top 2. Choose 1 for hand. Playable *this turn*. Discard end of turn if still in hand.
            # Requires tracking card state. Very complex for this structure.
            # Simplified: Look top 2. Agent chooses 1 (e.g., first ingredient). Add to hand. Discard other.
            card1 = self.main_deck.pop(0) if self.main_deck else None
            card2 = self.main_deck.pop(0) if self.main_deck else None
            options = [c for c in [card1, card2] if c]

            if options:
                 # Agent choice needed. Simple: prefer ingredient.
                 chosen_card = next((c for c in options if c.is_ingredient()), options[0])
                 other_cards = [c for c in options if c != chosen_card]

                 player.add_card_to_hand(chosen_card)
                 for other in other_cards:
                      self.discard_card(other)
                 result["effects"].append(f"Escopo Local pegou {chosen_card.nome}, descartou {len(other_cards)}")
            else:
                 result["effects"].append("Escopo Local: Baralho vazio")


        elif nome == "Chamada de Método":
             # Rule: Choose Action card from discard. Effect triggers again.
             # Needs target card name/obj from discard. COMPLEX search & re-trigger.
             # Simplest viable effect: Draw 1 card?
             drawn = self.draw_card(player, 1)
             result["effects"].append("Chamada de Método (Simplificado: Comprou 1)")


        elif nome == "Limpeza de Cache":
             # Rule: Discard rest of hand, draw same number.
             # Card playing this effect ('Limpeza de Cache') was already removed from hand by play_card.
             hand_before_discard = player.hand[:] # Copy list
             count = len(hand_before_discard)

             if count > 0:
                 discarded_count = 0
                 for c in hand_before_discard:
                      if self.discard_from_hand(player, c):
                           discarded_count += 1
                 # Draw based on how many were successfully discarded
                 drawn = self.draw_card(player, discarded_count)
                 result["effects"].append(f"Limpou {discarded_count} cartas da mão, comprou {len(drawn)}")
             else:
                 result["effects"].append("Limpeza de Cache: Mão já estava vazia")


        else:
             # Default for unhandled actions
             result["effects"].append(f"Efeito de {nome} não implementado")


        return log_info


    def _execute_wildcard_effect(self, player: Player, card: Card, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Executa o efeito de uma carta coringa e retorna info para log."""
        log_info = {}
        nome = card.nome

        if nome == "Lançamento em Produção":
            # Rule: Play only if 4+ ingredients in result area
            if len(player.result_area) >= 4:
                # Player instantly wins
                # Setting flags here, step() will confirm win after this returns
                player.has_won = True # Mark player directly
                self.winner = player.player_id # Set game winner state
                self.game_over = True
                self.phase = "game_over"
                result["effects"].append("Vitória por Lançamento em Produção!")
                # Card is discarded normally after effect resolves in play_card
            else:
                # Card played illegally according to its own text
                result["success"] = False
                result["message"] = "Tentou jogar Lançamento em Produção ilegalmente (menos de 4 ingredientes)."
                # Card was removed from hand by play_card, playing illegally means it's just discarded
                result["effects"].append("Lançamento em Produção falhou.")


        elif nome == "Reengenharia Culinária":
            # Rule: Discard hand & result. Draw 10. Can mount new sandwich (optional/complex).
            discarded_hand_count = 0
            for c in list(player.hand): # Iterate copy
                 if self.discard_from_hand(player, c):
                      discarded_hand_count += 1

            discarded_result_count = 0
            for c in list(player.result_area): # Iterate copy
                 player.result_area.remove(c)
                 self.discard_card(c)
                 discarded_result_count +=1

            drawn = self.draw_card(player, 10)
            result["effects"].append(f"Reiniciou (descartou {discarded_hand_count} mão, {discarded_result_count} área), comprou {len(drawn)}.")
            # The "mount new sandwich" part is too complex / ambiguous for simulation


        elif nome == "Rascunho Estratégico":
            # Rule: Inspect top 3. Take 1 to hand. Put others top/bottom in any order.
            top_3 = []
            if len(self.main_deck) >= 3:
                 top_3 = [self.main_deck.pop(0) for _ in range(3)]
            elif self.main_deck:
                 top_3 = self.main_deck[:]
                 self.main_deck.clear()

            if top_3:
                 # Agent needs to choose 1. Simplified: take first ingredient, else first card.
                 chosen_card = next((c for c in top_3 if c.is_ingredient()), top_3[0])
                 remaining_cards = [c for c in top_3 if c != chosen_card]

                 player.add_card_to_hand(chosen_card)
                 # Agent needs to choose order and top/bottom. Simplified: put remaining back on top.
                 self.main_deck = remaining_cards + self.main_deck
                 result["effects"].append(f"Rascunho pegou {chosen_card.nome}, retornou {len(remaining_cards)} ao topo")
            else:
                 result["effects"].append("Rascunho: Baralho vazio ou com < 3 cartas")


        elif nome == "Fluxo de Ideias":
             # Rule: Draw 2. For each INGREDIENT found, MAY discard 1 -> draw 1.
             drawn_initial = self.draw_card(player, 2)
             ingredients_drawn_count = sum(1 for c in drawn_initial if c.is_ingredient())
             
             # Agent needs to decide for each ingredient if they want to cycle.
             # Simplified: Always cycle if possible.
             num_cycles_to_attempt = ingredients_drawn_count
             discarded_count = 0
             drawn_cycle = 0

             for _ in range(num_cycles_to_attempt):
                  if player.hand: # Can only discard if hand not empty
                       # Agent needs to choose discard. Simplified: discard first non-ingredient if possible, else first card.
                       card_to_discard = next((c for c in player.hand if not c.is_ingredient()), player.hand[0])
                       
                       if self.discard_from_hand(player, card_to_discard):
                            new_cards = self.draw_card(player, 1)
                            discarded_count += 1
                            drawn_cycle += len(new_cards)
                       else:
                            # Failed to discard, stop cycling
                            break
                  else:
                       # Hand became empty during cycling
                       break
             result["effects"].append(f"Fluxo comprou {len(drawn_initial)} ({ingredients_drawn_count} ingred.), ciclou {discarded_count}x (comprou {drawn_cycle})")


        elif nome == "Recurso Compartilhado":
             # Rule: Each player draws 1. Then, you MAY take 1 Ingredient from opponent hand.
             # 1. All players draw
             for p_idx in range(self.num_players):
                  self.draw_card(self.players[p_idx], 1)
             result["effects"].append("Todos os jogadores compraram 1 carta.")

             # 2. Optionally take ingredient from opponent
             target_player_id = kwargs.get('target_player_id') # Agent MUST choose target

             if (target_player_id is not None and 0 <= target_player_id < self.num_players and
                 target_player_id != player.player_id):
                 target_player = self.players[target_player_id]
                 # Agent needs to choose *which* ingredient if multiple? Or just take *one*?
                 # Assume take the first one found for simplification.
                 target_ingredient = next((c for c in target_player.hand if c.is_ingredient()), None)
                 
                 if target_ingredient:
                      # Move card from target to player
                      if target_player.remove_card_from_hand(target_ingredient):
                          player.add_card_to_hand(target_ingredient)
                          result["effects"].append(f"Roubou {target_ingredient.nome} do Jogador {target_player_id}.")
                      else:
                          result["effects"].append(f"Erro ao remover {target_ingredient.nome} da mão do Jogador {target_player_id}.")
                 else:
                      result["effects"].append(f"Jogador {target_player_id} não tinha ingrediente para roubar.")
             else:
                  # This happens if agent chose not to target or target was invalid
                   result["effects"].append("Nenhum ingrediente roubado.") # Append this message? Or just the draw message?


        elif nome == "API de Sabor":
             # Rule: Announce type. Look top 4. Take 1 of type to hand, discard rest. If none, discard 4, draw 1.
             target_type = kwargs.get('target_ingredient_type') # Agent MUST choose

             if target_type not in ["Pão", "Proteína", "Vegetal", "Condimento"]:
                  result["success"] = False
                  result["message"] = f"Tipo alvo inválido para API de Sabor: {target_type}"
                  return log_info # Exit early

             top_4 : List[Card] = []
             if len(self.main_deck) >= 4:
                  top_4 = [self.main_deck.pop(0) for _ in range(4)]
             elif self.main_deck:
                  top_4 = self.main_deck[:]
                  self.main_deck.clear()

             found_card : Optional[Card] = None
             if top_4:
                  # Find first matching card
                  found_card = next((c for c in top_4 if c.tipo == target_type), None)

             if found_card:
                  player.add_card_to_hand(found_card)
                  remaining_cards = [c for c in top_4 if c != found_card]
                  for c in remaining_cards:
                       self.discard_card(c)
                  result["effects"].append(f"API buscou {target_type}, pegou {found_card.nome}, descartou {len(remaining_cards)}")
             else:
                  # None found among the top_4 (or deck was empty)
                  for c in top_4: # Discard whatever was revealed
                       self.discard_card(c)
                  drawn = self.draw_card(player, 1) # Draw 1 as compensation
                  result["effects"].append(f"API não encontrou {target_type} no topo. Descartou {len(top_4)}, comprou {len(drawn)}")


        else:
             result["effects"].append(f"Efeito Coringa {nome} não implementado")

        return log_info


    def end_action_phase(self):
        """
        Finaliza a fase de ação (após 1 ação ser jogada ou passar).
        Verifica a condição da mão e transita para 'discard' ou 'next_player'.
        Não verifica mais vitória aqui, step() e play_card() cuidam disso.
        """
        if self.game_over or self.phase == "discard": # Don't proceed if game ended or already in discard
            return

        current_player = self.get_current_player()

        if len(current_player.hand) > self.max_hand_size:
            self.phase = "discard"
            # Stay on the current player for the discard action
        else:
            # Hand size OK, move to the next player
            self.next_player()


    def next_player(self):
        """Passa o turno para o próximo jogador e inicia sua fase de compra."""
        if self.game_over:
             return

        self.current_player_id = (self.current_player_id + 1) % self.num_players
        # Phase should transition back to 'playing' for the start of the new turn
        # self.phase = "playing" # Let start_turn set this? No, set here.

        if self.current_player_id == 0:
            self.turn_count += 1
            #print(f"--- Turn {self.turn_count} ---") # Optional debug log

        # Start next player's turn (sets phase, draws card) if game isn't over
        self.start_turn()


    def is_over(self) -> bool:
        """Verifica se o jogo terminou (por vitória ou limite de turnos)."""
        max_turns = 100 # Example limit to prevent infinite games
        if not self.game_over and self.turn_count >= max_turns:
            #print(f"Game over: Turn limit {max_turns} reached.") # Optional debug log
            self.game_over = True
            self.winner = None # Draw due to turn limit

        # Check if any player has the 'has_won' flag set
        if not self.game_over:
             for p in self.players:
                  if p.has_won:
                       self.game_over = True
                       self.winner = p.player_id
                       self.phase = "game_over"
                       break # Found a winner

        return self.game_over


    def get_winner(self) -> Optional[int]:
        """Retorna o ID do jogador vencedor, se houver."""
        self.is_over()
        return self.winner


    def get_legal_actions(self, player: Player) -> List[Dict[str, Any]]:
        """
        Retorna as ações legais disponíveis para um jogador, incluindo alvos.
        Handles different game phases.
        """
        actions = []
        if self.is_over():
             return [] # No actions if game is over

        if self.phase == "discard":
            # Only discard actions are legal
            return [{"type": "discard", "card": card, "description": f"Descartar {card.nome}"}
                    for card in player.hand]

        if self.phase != "playing": # Only allow main actions during playing phase
            # If somehow in another phase (e.g., setup error), maybe allow pass?
             return [{"type": "pass", "description": "Passar a vez (Fase Inválida)"}]

        # --- Playing Phase Actions ---

        # 1. Play Ingredient
        if len(player.result_area) < 10: # Check result area limit
            for card in player.hand:
                if card.is_ingredient():
                     actions.append({"type": "play_ingredient", "card": card, "description": f"Jogar ingrediente: {card.nome}"})

        # 2. Play Action / Wildcard
        for card in player.hand:
            if card.is_action() or card.is_wildcard():
                base_action = {"type": "play_action", "card": card}
                card_name = card.nome

                # --- Add logic for complex actions based on rules ---

                # A) Cards needing opponent target
                if card_name in ["Erro de Sintaxe", "Variáveis Trocadas", "Ingrediente Secreto", "Recurso Compartilhado"]:
                    for p in self.players:
                        if p.player_id != player.player_id:
                            action_with_target = base_action.copy()
                            action_with_target['target_player_id'] = p.player_id
                            desc = f"Usar {card_name} no Jogador {p.player_id}"
                            # Add ingredient detail for specific cards
                            if card_name == "Ingrediente Secreto":
                                 # Need to specify ingredient. Generate option for each possible ingredient name?
                                 # Or require agent to provide it? For simulation, pick a default.
                                 action_with_target['ingredient_name'] = "Bacon" # Example default
                                 desc += " (nomeando Bacon)"
                            elif card_name == "Variáveis Trocadas":
                                 # Needs player to choose card from *own* hand to offer
                                 player_ingredients = [c for c in player.hand if c.is_ingredient()]
                                 if not player_ingredients: continue # Cannot play if no ingredient to offer
                                 # Generate action for *each* ingredient player could offer?
                                 for offer_card in player_ingredients:
                                      action_offer = action_with_target.copy()
                                      action_offer['card_from_player'] = offer_card # Pass card object
                                      action_offer['description'] = f"Usar {card_name} no Jogador {p.player_id} (oferecendo {offer_card.nome})"
                                      actions.append(action_offer)
                                 continue # Skip adding the base action_with_target for this card

                            action_with_target['description'] = desc
                            actions.append(action_with_target)

                # B) Cards targeting self or opponent (with condition)
                elif card_name == "Ponto de Interrupção":
                     # Target self (only if player has bugs)
                     if player.bugs:
                         actions.append({**base_action, 'target_player_id': player.player_id, 'description': f"Usar {card_name} em si mesmo"})
                     # Target others (only if opponent has bugs)
                     for p in self.players:
                         if p.player_id != player.player_id and p.bugs:
                             actions.append({**base_action, 'target_player_id': p.player_id, 'description': f"Usar {card_name} no Jogador {p.player_id}"})

                # C) Cards needing ingredient from hand parameter
                elif card_name in ["Sub-rotina de Preparo", "Fluxo Contínuo"]:
                     if len(player.result_area) < 10: # Check result area limit
                         # Generate one action per *specific card instance* in hand
                         ingredients_in_hand = [c for c in player.hand if c.is_ingredient()]
                         for ing_card in ingredients_in_hand:
                             action_with_ing = base_action.copy()
                             action_with_ing['ingredient_name'] = ing_card.nome # Keep name for logging maybe
                             action_with_ing['card_to_play_with'] = ing_card # Pass the actual card obj
                             action_with_ing['description'] = f"Usar {card_name} com {ing_card.nome} ({ing_card.id})"
                             actions.append(action_with_ing)

                # D) Cards needing positions in result area
                elif card_name == "Reorganizar Etapas":
                     if len(player.result_area) >= 2:
                          for i in range(len(player.result_area) - 1):
                               action_swap = base_action.copy()
                               action_swap['pos1'] = i
                               action_swap['pos2'] = i + 1
                               action_swap['description'] = f"Usar {card_name} trocando pos {i}({player.result_area[i].nome}) e {i+1}({player.result_area[i+1].nome})"
                               actions.append(action_swap)

                # E) Complex conditional cards (generate all valid options)
                elif card_name == "Alternativa Saudável":
                     replaceable_indices = [i for i, c in enumerate(player.result_area) if c.tipo in ["Proteína", "Pão"]]
                     veggies_in_hand = [c for c in player.hand if c.tipo == "Vegetal"]
                     if replaceable_indices and veggies_in_hand:
                          for pos in replaceable_indices:
                               for veggie_card in veggies_in_hand:
                                    actions.append({
                                         **base_action,
                                         'position_to_replace': pos,
                                         'veggie_card_from_hand': veggie_card, # Pass card obj
                                         'description': f"Usar {card_name}: trocar {player.result_area[pos].nome}(pos {pos}) por {veggie_card.nome}"
                                    })

                elif card_name == "Ciclo de Sabor":
                     # Requires ingredient *name* from result area
                     unique_names_in_result = {c.nome for c in player.result_area if c.is_ingredient()}
                     for ing_name in unique_names_in_result:
                          # Add options for getting 1 or 2 copies
                          actions.append({**base_action, 'ingredient_name_target': ing_name, 'num_copies': 1, 'description': f"Usar {card_name} pegando 1 {ing_name}"})
                          actions.append({**base_action, 'ingredient_name_target': ing_name, 'num_copies': 2, 'description': f"Usar {card_name} pegando 2 {ing_name}"})

                # F) Cards with play conditions
                elif card_name == "Lançamento em Produção":
                     if len(player.result_area) >= 4:
                          base_action['description'] = f"Usar {card_name} (Vitória!)"
                          actions.append(base_action)
                     # Else: not a legal action to play

                # G) Cards requiring agent choice parameter
                elif card_name == "API de Sabor":
                     # Generate option for each possible type
                     for type_name in ["Pão", "Proteína", "Vegetal", "Condimento"]:
                          actions.append({**base_action, 'target_ingredient_type': type_name, 'description': f"Usar {card_name} buscando {type_name}"})

                # H) Default for simple actions / wildcards without extra params
                else:
                    base_action['description'] = f"Usar {card.nome}"
                    actions.append(base_action)


        # 3. Pass Action (always available in playing phase)
        actions.append({"type": "pass", "description": "Passar a vez"})

        # Add unique IDs to actions if needed for agents
        # for i, action in enumerate(actions):
        #    action['action_id'] = i

        return actions


    def get_num_players(self) -> int:
        """Retorna o número de jogadores."""
        return self.num_players

    def get_num_actions(self) -> int:
        """Retorna um número máximo seguro de ações possíveis."""
        # Recalculate based on detailed legal_actions:
        # Discard: 5
        # Play Ing: 5
        # Play Action/Wildcard:
        #   Targeted (Erro, Var, IngSec, Rec): (4 cards * 3 targets) = 12 (Var needs offer card ~ *5 = 60?)
        #   Ponto: (1 card * 4 targets max) = 4
        #   IngParam (Sub, Fluxo): (2 cards * 5 ingredients) = 10
        #   PosParam (Reorg): (1 card * 9 pairs) = 9
        #   Complex (Alt Saud): (1 card * 10 pos * 5 veggies) = 50
        #   Complex (Ciclo): (1 card * ~10 names * 2 amounts) = 20
        #   TypeParam (API): (1 card * 4 types) = 4
        #   Conditional (Lanc): 1
        #   Simple: ~25 other actions/wildcards = 25
        # Pass: 1
        # Total approx (worst case): 5 + 60 + 4 + 10 + 9 + 50 + 20 + 4 + 1 + 25 + 1 = ~189
        # Let's increase the upper bound slightly
        return 200

    def get_game_state(self) -> Dict[str, Any]:
        """Retorna o estado geral atual do jogo (visível a todos)."""
        return {
            "phase": self.phase,
            "current_player": self.current_player_id,
            "turn_count": self.turn_count,
            "game_over": self.is_over(),
            "winner": self.winner,
            "main_deck_size": len(self.main_deck),
            "discard_pile_size": len(self.discard_pile),
            "players": [
                {
                    "player_id": p.player_id,
                    "hand_size": len(p.hand), # Public info
                    "result_size": len(p.result_area), # Public info
                    "bugs_count": len(p.bugs), # Public info
                    "has_recipe": p.recipe_card is not None # Public info
                }
                for p in self.players
            ]
        }

    def get_state(self, player_id: int) -> Dict[str, Any]:
        """
        Retorna o estado bruto do jogo do ponto de vista de um jogador específico.
        Este é o método que a rlcard Env.get_state() espera que o *jogo* tenha.
        """
        if not 0 <= player_id < self.num_players:
            # Maybe return a generic state or raise error?
             # Let's return state for player 0 as a fallback, but log warning
             print(f"Warning: Invalid player_id {player_id} requested in get_state. Returning state for player 0.")
             player_id = 0
             # raise ValueError(f"ID de jogador inválido: {player_id}")


        player = self.players[player_id]

        # Determine legal actions based on *current* game state, not necessarily player_id's turn
        current_player_obj = self.get_current_player()
        # Only the current player has legal actions other than observing
        current_legal_actions = self.get_legal_actions(current_player_obj) if self.current_player_id == player_id else []


        player_state = {
            "player_id": player_id,
            # Use card representations (e.g., ID or dict) if agents need detail
            # Assuming Card has to_dict()
            "hand": [card.to_dict() if hasattr(card, 'to_dict') else str(card) for card in player.hand],
            "result_area": [card.to_dict() if hasattr(card, 'to_dict') else str(card) for card in player.result_area],
            "bugs": [card.to_dict() if hasattr(card, 'to_dict') else str(card) for card in player.bugs],
            # Assuming Recipe Card also has to_dict()
            "recipe": player.recipe_card.to_dict() if player.recipe_card and hasattr(player.recipe_card, 'to_dict') else (str(player.recipe_card) if player.recipe_card else None),
            "legal_actions": current_legal_actions, # Legal actions IF it's this player's turn
             # Also add the general game state info
            "game_info": self.get_game_state() # General info visible to everyone
        }

        # Add public info about opponents relative to player_id
        player_state['opponents_public'] = [
            {
                "player_id": p.player_id,
                "hand_size": len(p.hand),
                "result_size": len(p.result_area),
                "bugs_count": len(p.bugs),
                "has_recipe": p.recipe_card is not None
            }
            for p in self.players if p.player_id != player_id
        ]

        return player_state