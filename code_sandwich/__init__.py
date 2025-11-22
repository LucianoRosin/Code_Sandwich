"""
Este módulo implementa o ambiente do jogo Code Sandwich usando o framework RLCard.
"""

from .game import CodeSandwichGame
from .env import CodeSandwichEnv
from .heuristic_agent import HeuristicAgent

__all__ = [
    'CodeSandwichGame',
    'CodeSandwichEnv',
    'HeuristicAgent',
]