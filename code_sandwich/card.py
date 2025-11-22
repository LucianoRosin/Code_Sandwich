import json
from typing import List, Dict, Any, Optional

class Card:
    """Representa uma carta no jogo Code Sandwich."""

    def __init__(self, card_data: Dict[str, Any]):
        """
        Inicializa uma carta a partir de um dicionário de dados.

        Args:
            card_data: Dicionário contendo os dados da carta (ex: do JSON).
        """
        self.id: str = card_data.get('id', 'UNKNOWN_ID')
        self.nome: str = card_data.get('nome', 'Sem Nome')
        self.tipo: str = card_data.get('tipo', 'Desconhecido')
        self.texto_efeito: str = card_data.get('texto_efeito', '')
        self.kc_associado: List[str] = card_data.get('kc_associado', [])

        # Atributos específicos para certos tipos de cartas
        self.categoria_acao: Optional[str] = card_data.get('categoria_acao') # Para cartas de Ação/Coringa
        self.ingredientes: Optional[List[str]] = card_data.get('ingredientes') # Para cartas de Receita

    def is_ingredient(self) -> bool:
        """Verifica se a carta é um ingrediente."""
        return self.tipo in ["Pão", "Proteína", "Vegetal", "Condimento"]

    def is_action(self) -> bool:
        """Verifica se a carta é uma carta de Ação (não Coringa)."""
        return self.tipo == "Ação"

    def is_wildcard(self) -> bool:
        """Verifica se a carta é uma carta Coringa."""
        return self.tipo == "Coringa"

    def is_recipe(self) -> bool:
        """Verifica se a carta é uma Receita Final."""
        return self.tipo == "Receita Final"

    def to_dict(self) -> Dict[str, Any]:
        """Retorna uma representação da carta em dicionário."""
        data = {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "texto_efeito": self.texto_efeito,
            "kc_associado": self.kc_associado,
        }
        if self.categoria_acao:
            data["categoria_acao"] = self.categoria_acao
        if self.ingredientes:
            data["ingredientes"] = self.ingredientes
        return data

    def __str__(self) -> str:
        """Representação em string da carta."""
        return f"{self.nome} ({self.tipo})"

    def __repr__(self) -> str:
        """Representação detalhada da carta."""
        return f"Card(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')"

    # Permite comparar cartas (importante para remover da lista 'hand')
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.id == other.id
        return False

    def __hash__(self):
         return hash(self.id)


class CardDeck:
    """Gerencia o carregamento e a distribuição das cartas."""

    def __init__(self, cards_file: Optional[str] = None):
        """
        Inicializa o deck carregando as cartas do arquivo JSON.

        Args:
            cards_file: Caminho para o arquivo JSON com todas as cartas.
                        Se None, tenta carregar 'cartas.json'.
        """
        if cards_file is None:
            cards_file = 'cartas.json'

        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                all_card_data = json.load(f)
        except FileNotFoundError:
            print(f"Erro: Arquivo de cartas '{cards_file}' não encontrado.")
            raise
        except json.JSONDecodeError:
            print(f"Erro: Falha ao decodificar JSON do arquivo '{cards_file}'.")
            raise

        self.all_cards: List[Card] = [Card(data) for data in all_card_data]

        # Separa os decks por tipo para fácil acesso
        self.main_deck_cards: List[Card] = [
            card for card in self.all_cards
            if card.is_ingredient() or card.is_action() or card.is_wildcard()
        ]
        self.recipe_deck_cards: List[Card] = [
            card for card in self.all_cards if card.is_recipe()
        ]

        if not self.main_deck_cards:
             print("Aviso: Nenhuma carta de jogo principal (Ingrediente, Ação, Coringa) foi carregada.")
        if not self.recipe_deck_cards:
             print("Aviso: Nenhuma carta de Receita Final foi carregada.")


    def get_main_deck(self) -> List[Card]:
        """Retorna uma cópia das cartas do baralho principal."""
        return self.main_deck_cards[:]

    def get_recipe_deck(self) -> List[Card]:
        """Retorna uma cópia das cartas do baralho de receitas."""
        return self.recipe_deck_cards[:]

    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        """Encontra uma carta pelo seu ID."""
        return next((card for card in self.all_cards if card.id == card_id), None)

    def get_card_by_name(self, card_name: str) -> Optional[Card]:
        """Encontra a primeira carta com um nome específico."""
        return next((card for card in self.all_cards if card.nome == card_name), None)