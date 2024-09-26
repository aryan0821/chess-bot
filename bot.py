import random
import copy
from chess_logic import (
    get_valid_moves, make_move, in_check, copy_castling_rights
)

class Bot:
    def __init__(self, color):
        self.color = color  # 'w' for white, 'b' for black
        self.opponent_color = 'b' if color == 'w' else 'w'

        # Piece values
        self.piece_values = {
            'p': 100,
            'N': 320,
            'B': 330,
            'R': 500,
            'Q': 900,
            'K': 20000
        }

        # Positional tables for each piece
        self.pawn_table = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]

        self.knight_table = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 0, 0, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 20, 20, 15, 0, -30],
            [-30, 5, 10, 15, 15, 10, 5, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]

        self.bishop_table = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 5, 10, 10, 5, 5, -10],
            [-10, 0, 10, 10, 10, 10, 0, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]

        self.rook_table = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [0, 0, 0, 5, 5, 0, 0, 0]
        ]

        self.queen_table = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [0, 0, 5, 5, 5, 5, 0, -5],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20]
        ]

        self.king_table = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20]
        ]

        # Flip tables for black pieces
        if self.color == 'b':
            self.pawn_table = self.pawn_table[::-1]
            self.knight_table = self.knight_table[::-1]
            self.bishop_table = self.bishop_table[::-1]
            self.rook_table = self.rook_table[::-1]
            self.queen_table = self.queen_table[::-1]
            self.king_table = self.king_table[::-1]

    def get_move(self, board, turn, en_passant_possible, castling_rights, move_log):
        best_move = None
        best_evaluation = float('-inf')
        depth = 3  # Adjust depth for performance vs. strength

        all_moves = self.get_all_possible_moves(board, turn, en_passant_possible, castling_rights)
        if not all_moves:
            return None  # No legal moves

        # Move ordering: prioritize captures and checks
        ordered_moves = self.order_moves(all_moves, board, turn, en_passant_possible, castling_rights)

        for move in ordered_moves:
            start_pos, end_pos = move
            # Copy the game state
            board_copy = copy.deepcopy(board)
            en_passant_copy = en_passant_possible
            castling_rights_copy = copy_castling_rights(castling_rights)
            move_log_copy = move_log.copy()
            # Make the move
            captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
            )
            evaluation = self.minimax(
                depth - 1, board_copy, float('-inf'), float('inf'), False, self.opponent_color, new_en_passant_possible, new_castling_rights, move_log_copy
            )
            if evaluation > best_evaluation:
                best_evaluation = evaluation
                best_move = move
        return best_move

    def minimax(self, depth, board, alpha, beta, maximizing_player, turn, en_passant_possible, castling_rights, move_log):
        if depth == 0:
            return self.evaluate_board(board)

        all_moves = self.get_all_possible_moves(board, turn, en_passant_possible, castling_rights)
        if not all_moves:
            if in_check(board, turn):
                return float('-inf') if maximizing_player else float('inf')
            else:
                return 0  # Stalemate

        # Move ordering
        ordered_moves = self.order_moves(all_moves, board, turn, en_passant_possible, castling_rights)

        if maximizing_player:
            max_eval = float('-inf')
            for move in ordered_moves:
                start_pos, end_pos = move
                # Copy the game state
                board_copy = copy.deepcopy(board)
                en_passant_copy = en_passant_possible
                castling_rights_copy = copy_castling_rights(castling_rights)
                move_log_copy = move_log.copy()
                # Make the move
                captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                    board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                )
                evaluation = self.minimax(
                    depth - 1, board_copy, alpha, beta, False, self.opponent_color, new_en_passant_possible, new_castling_rights, move_log_copy
                )
                max_eval = max(max_eval, evaluation)
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break  # Beta cut-off
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                start_pos, end_pos = move
                # Copy the game state
                board_copy = copy.deepcopy(board)
                en_passant_copy = en_passant_possible
                castling_rights_copy = copy_castling_rights(castling_rights)
                move_log_copy = move_log.copy()
                # Make the move
                captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                    board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                )
                evaluation = self.minimax(
                    depth - 1, board_copy, alpha, beta, True, self.color, new_en_passant_possible, new_castling_rights, move_log_copy
                )
                min_eval = min(min_eval, evaluation)
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break  # Alpha cut-off
            return min_eval

    def evaluate_board(self, board):
        evaluation = 0
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '--':
                    piece_type = piece[1]
                    color = piece[0]
                    value = self.piece_values.get(piece_type, 0)
                    # Positional value
                    if piece_type == 'p':
                        positional_value = self.pawn_table[row][col]
                    elif piece_type == 'N':
                        positional_value = self.knight_table[row][col]
                    elif piece_type == 'B':
                        positional_value = self.bishop_table[row][col]
                    elif piece_type == 'R':
                        positional_value = self.rook_table[row][col]
                    elif piece_type == 'Q':
                        positional_value = self.queen_table[row][col]
                    elif piece_type == 'K':
                        positional_value = self.king_table[row][col]
                    else:
                        positional_value = 0

                    if color == self.color:
                        evaluation += value + positional_value
                    else:
                        evaluation -= value + positional_value
        return evaluation

    def get_all_possible_moves(self, board, turn, en_passant_possible, castling_rights):
        moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col][0] == turn:
                    valid_moves = get_valid_moves(
                        board, (row, col), turn, en_passant_possible, castling_rights)
                    for end_pos in valid_moves:
                        moves.append(((row, col), end_pos))
        return moves

    def order_moves(self, moves, board, turn, en_passant_possible, castling_rights):
        """
        Orders moves to improve alpha-beta pruning efficiency.
        Captures and checks are considered first.
        """
        def move_priority(move):
            start_pos, end_pos = move
            piece_moved = board[start_pos[0]][start_pos[1]]
            piece_captured = board[end_pos[0]][end_pos[1]]

            priority = 0
            if piece_captured != '--':
                priority += self.piece_values.get(piece_captured[1], 0) - self.piece_values.get(piece_moved[1], 0)

            # Simulate move to check for checks
            board_copy = [row[:] for row in board]
            en_passant_copy = en_passant_possible
            castling_rights_copy = copy_castling_rights(castling_rights)
            move_log_copy = []
            make_move(board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy)
            if in_check(board_copy, self.opponent_color if turn == self.color else self.color):
                priority += 50  # Assign higher priority to moves that result in check

            return -priority  # Negative for descending order

        ordered_moves = sorted(moves, key=move_priority)
        return ordered_moves