from typing import List, Optional
from .card import Card


class Player:
    # ... (outros métodos como __init__, add_card_to_hand, etc. permanecem iguais) ...
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand: List[Card] = []
        self.result_area: List[Card] = []
        self.recipe_card: Optional[Card] = None
        self.has_won = False
        self.bugs: List[Card] = []

    def add_card_to_hand(self, card: Card):
        self.hand.append(card)

    def remove_card_from_hand(self, card: Card) -> bool:
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def add_card_to_result(self, card: Card, position: Optional[int] = None):
        if position is None:
            self.result_area.append(card)
        else:
            self.result_area.insert(position, card)

    def remove_card_from_result(self, card: Card) -> bool:
        if card in self.result_area:
            self.result_area.remove(card)
            return True
        return False

    def swap_cards_in_result(self, pos1: int, pos2: int) -> bool:
        if 0 <= pos1 < len(self.result_area) and 0 <= pos2 < len(self.result_area):
            self.result_area[pos1], self.result_area[pos2] = self.result_area[pos2], self.result_area[pos1]
            return True
        return False

    def set_recipe_card(self, recipe_card: Card):
        if recipe_card.is_recipe():
            self.recipe_card = recipe_card

    def check_victory_condition(self) -> bool:
        if self.bugs:
            return False
        if not self.recipe_card:
            return False
        # Correção: A regra original não especifica mínimo de 5, apenas correspondência exata.
        # if len(self.result_area) < 5:
        #     return False
        if not hasattr(self.recipe_card, 'ingredientes') or not self.recipe_card.ingredientes:
             return False # Receita inválida

        recipe_ingredients = self.recipe_card.ingredientes
        result_names = [card.nome for card in self.result_area]

        return result_names == recipe_ingredients # Verifica correspondência exata

    def add_bug(self, bug_card: Card):
        self.bugs.append(bug_card)

    def remove_bug(self, bug_card: Optional[Card] = None) -> Optional[Card]:
        """
        Remove uma carta de bug do jogador. Se nenhum bug_card específico
        for fornecido, remove o primeiro bug encontrado.

        Args:
            bug_card: A carta de bug específica a remover (opcional).

        Returns:
            A carta de bug que foi removida, ou None se nenhum bug foi removido.
        """
        card_to_remove = None
        if bug_card and bug_card in self.bugs:
            card_to_remove = bug_card
            self.bugs.remove(bug_card)
        elif not bug_card and self.bugs: # Se nenhum card específico foi passado E há bugs
            card_to_remove = self.bugs.pop(0) # Remove o primeiro bug da lista

        return card_to_remove # Retorna o card removido ou None
    def get_hand_size(self) -> int:
        return len(self.hand)

    def get_result_size(self) -> int:
        return len(self.result_area)

    def get_ingredient_types_in_result(self) -> set:
        return {card.tipo for card in self.result_area if card.is_ingredient()}

    def has_card_in_hand(self, card_name: str) -> bool:
        return any(card.nome == card_name for card in self.hand)

    def get_cards_by_type_in_hand(self, card_type: str) -> List[Card]:
        return [card for card in self.hand if card.tipo == card_type]

    def __str__(self) -> str:
        return f"Player {self.player_id} - Hand: {len(self.hand)}, Result: {len(self.result_area)}, Bugs: {len(self.bugs)}"

    def __repr__(self) -> str:
        return f"Player(id={self.player_id}, hand_size={len(self.hand)}, result_size={len(self.result_area)})"