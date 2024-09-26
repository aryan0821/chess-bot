import random
import copy
import time
from chess_logic import (
    get_valid_moves, make_move, in_check, copy_castling_rights
)

class Bot:
    def __init__(self, color):
        self.color = color  # 'w' for white, 'b' for black
        self.opponent_color = 'b' if color == 'w' else 'w'

        # Initialize the transposition table and Zobrist keys
        self.transposition_table = {}
        self.zobrist_table = self.initialize_zobrist_keys()

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
            [0,   0,   0,   0,   0,   0,   0,   0],
            [50,  50,  50,  50,  50,  50,  50,  50],
            [10,  10,  20,  30,  30,  20,  10,  10],
            [5,   5,  10,  25,  25,  10,   5,   5],
            [0,   0,   0,  20,  20,   0,   0,   0],
            [5,  -5, -10,   0,   0, -10,  -5,   5],
            [5,  10,  10, -20, -20,  10,  10,   5],
            [0,   0,   0,   0,   0,   0,   0,   0]
        ]

        self.knight_table = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20,   0,   0,   0,   0, -20, -40],
            [-30,   0,  10,  15,  15,  10,   0, -30],
            [-30,   5,  15,  20,  20,  15,   5, -30],
            [-30,   0,  15,  20,  20,  15,   0, -30],
            [-30,   5,  10,  15,  15,  10,   5, -30],
            [-40, -20,   0,   5,   5,   0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]

        self.bishop_table = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-10,   0,   5,  10,  10,   5,   0, -10],
            [-10,   5,   5,  10,  10,   5,   5, -10],
            [-10,   0,  10,  10,  10,  10,   0, -10],
            [-10,  10,  10,  10,  10,  10,  10, -10],
            [-10,   5,   0,   0,   0,   0,   5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]

        self.rook_table = [
            [0,   0,   0,   0,   0,   0,   0,   0],
            [5,  10,  10,  10,  10,  10,  10,   5],
            [-5,   0,   0,   0,   0,   0,   0,  -5],
            [-5,   0,   0,   0,   0,   0,   0,  -5],
            [-5,   0,   0,   0,   0,   0,   0,  -5],
            [-5,   0,   0,   0,   0,   0,   0,  -5],
            [-5,   0,   0,   0,   0,   0,   0,  -5],
            [0,   0,   0,   5,   5,   0,   0,   0]
        ]

        self.queen_table = [
            [-20, -10, -10,  -5,  -5, -10, -10, -20],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-10,   0,   5,   5,   5,   5,   0, -10],
            [ -5,   0,   5,   5,   5,   5,   0,  -5],
            [  0,   0,   5,   5,   5,   5,   0,  -5],
            [-10,   5,   5,   5,   5,   5,   0, -10],
            [-10,   0,   5,   0,   0,   0,   0, -10],
            [-20, -10, -10,  -5,  -5, -10, -10, -20]
        ]

        self.king_table = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20,   20,   0,   0,   0,   0,  20,  20],
            [20,   30,  10,   0,   0,  10,  30,  20]
        ]

        # Flip tables for black pieces
        if self.color == 'b':
            self.pawn_table = self.pawn_table[::-1]
            self.knight_table = self.knight_table[::-1]
            self.bishop_table = self.bishop_table[::-1]
            self.rook_table = self.rook_table[::-1]
            self.queen_table = self.queen_table[::-1]
            self.king_table = self.king_table[::-1]

        # Time management variables
        self.time_limit = 30.0  # Time limit in seconds
        self.start_time = None

        # Variables for move ordering and search enhancements
        self.killer_moves = {}
        self.history_heuristic = {}
        self.current_depth = 0

    def initialize_zobrist_keys(self):
        """
        Initializes Zobrist keys for all pieces on all squares.
        Each piece-square combination is assigned a random 64-bit integer.
        """
        random.seed(0)  # Ensures reproducibility

        zobrist_table = {}
        pieces = ['wp', 'wN', 'wB', 'wR', 'wQ', 'wK',
                  'bp', 'bN', 'bB', 'bR', 'bQ', 'bK']

        for piece in pieces:
            for row in range(8):
                for col in range(8):
                    zobrist_table[(piece, row, col)] = random.getrandbits(64)
        return zobrist_table

    def compute_zobrist_hash(self, board):
        """
        Computes the Zobrist hash for the given board state.
        """
        h = 0  # Initialize hash value
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '--':
                    h ^= self.zobrist_table[(piece, row, col)]
        return h

    def get_move(self, board, en_passant_possible, castling_rights, move_log):
        self.start_time = time.time()
        best_move = None
        max_depth = 1
        time_remaining = True

        # Generate all possible moves for the bot
        all_moves = self.get_all_possible_moves(board, self.color, en_passant_possible, castling_rights)
        if not all_moves:
            return None  # No legal moves

        # Iterative deepening loop
        while time_remaining:
            try:
                best_evaluation = float('-inf')
                # Move ordering: prioritize captures and checks
                ordered_moves = self.order_moves(all_moves, board, self.color, en_passant_possible, castling_rights)
                for move in ordered_moves:
                    self.check_time()
                    start_pos, end_pos = move
                    # Copy the game state
                    board_copy = copy.deepcopy(board)
                    en_passant_copy = copy.deepcopy(en_passant_possible)
                    castling_rights_copy = copy_castling_rights(castling_rights)
                    move_log_copy = move_log.copy()
                    # Make the move
                    captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                        board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                    )
                    self.current_depth = 1
                    evaluation = self.minimax(
                        max_depth - 1, board_copy, float('-inf'), float('inf'), False, self.opponent_color,
                        new_en_passant_possible, new_castling_rights, move_log_copy
                    )
                    if evaluation > best_evaluation:
                        best_evaluation = evaluation
                        best_move = move
                max_depth += 1
            except TimeoutError:
                break  # Time limit exceeded
            # Check if time limit is close
            if time.time() - self.start_time >= self.time_limit:
                time_remaining = False

        return best_move

    def check_time(self):
        """
        Checks if the time limit has been exceeded.
        Raises a TimeoutError if time is up.
        """
        if time.time() - self.start_time >= self.time_limit:
            raise TimeoutError

    def minimax(self, depth, board, alpha, beta, maximizing_player, turn,
                en_passant_possible, castling_rights, move_log):
        self.check_time()
        self.current_depth += 1
        alpha_original = alpha
        beta_original = beta
        # Compute the hash for the current board
        board_hash = self.compute_zobrist_hash(board)
        # Check if the position is in the transposition table
        if board_hash in self.transposition_table:
            entry = self.transposition_table[board_hash]
            if entry['depth'] >= depth:
                if entry['flag'] == 'exact':
                    return entry['value']
                elif entry['flag'] == 'lowerbound':
                    alpha = max(alpha, entry['value'])
                elif entry['flag'] == 'upperbound':
                    beta = min(beta, entry['value'])
                if alpha >= beta:
                    return entry['value']

        if depth == 0:
            eval = self.quiescence_search(alpha, beta, board, turn, en_passant_possible, castling_rights)
            # Store in transposition table
            self.transposition_table[board_hash] = {'value': eval, 'depth': depth, 'flag': 'exact'}
            return eval

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
                self.check_time()
                start_pos, end_pos = move
                # Copy the game state
                board_copy = copy.deepcopy(board)
                en_passant_copy = copy.deepcopy(en_passant_possible)
                castling_rights_copy = copy_castling_rights(castling_rights)
                move_log_copy = move_log.copy()
                # Make the move
                captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                    board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                )

                # Null Move Pruning
                if depth >= 3 and not in_check(board_copy, self.opponent_color):
                    self.check_time()
                    null_eval = -self.minimax(depth - 1 - 2, board_copy, -beta, -beta + 1, False, turn,
                                              en_passant_copy, castling_rights_copy, move_log_copy)
                    if null_eval >= beta:
                        return beta

                eval = self.minimax(
                    depth - 1, board_copy, alpha, beta, False, self.opponent_color,
                    new_en_passant_possible, new_castling_rights, move_log_copy
                )
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if alpha >= beta:
                    # Beta cutoff
                    # Killer moves and history heuristic
                    self.killer_moves.setdefault(depth, []).append(move)
                    self.history_heuristic[move] = self.history_heuristic.get(move, 0) + depth * depth
                    break
            # Store in transposition table
            if max_eval <= alpha_original:
                flag = 'upperbound'
            elif max_eval >= beta_original:
                flag = 'lowerbound'
            else:
                flag = 'exact'
            self.transposition_table[board_hash] = {'value': max_eval, 'depth': depth, 'flag': flag}
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                self.check_time()
                start_pos, end_pos = move
                # Copy the game state
                board_copy = copy.deepcopy(board)
                en_passant_copy = copy.deepcopy(en_passant_possible)
                castling_rights_copy = copy_castling_rights(castling_rights)
                move_log_copy = move_log.copy()
                # Make the move
                captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                    board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                )

                # Null Move Pruning
                if depth >= 3 and not in_check(board_copy, self.color):
                    self.check_time()
                    null_eval = -self.minimax(depth - 1 - 2, board_copy, -beta, -beta + 1, True, turn,
                                              en_passant_copy, castling_rights_copy, move_log_copy)
                    if null_eval <= alpha:
                        return alpha

                eval = self.minimax(
                    depth - 1, board_copy, alpha, beta, True, self.color,
                    new_en_passant_possible, new_castling_rights, move_log_copy
                )
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    # Alpha cutoff
                    # Killer moves and history heuristic
                    self.killer_moves.setdefault(depth, []).append(move)
                    self.history_heuristic[move] = self.history_heuristic.get(move, 0) + depth * depth
                    break
            # Store in transposition table
            if min_eval <= alpha_original:
                flag = 'upperbound'
            elif min_eval >= beta_original:
                flag = 'lowerbound'
            else:
                flag = 'exact'
            self.transposition_table[board_hash] = {'value': min_eval, 'depth': depth, 'flag': flag}
            return min_eval

    def quiescence_search(self, alpha, beta, board, turn, en_passant_possible, castling_rights):
        self.check_time()
        stand_pat = self.evaluate_board(board, en_passant_possible, castling_rights)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Limit the depth of quiescence search
        max_quiescence_depth = 5
        if getattr(self, 'quiescence_depth', 0) >= max_quiescence_depth:
            return stand_pat

        # Generate capture moves
        capture_moves = self.get_capture_moves(board, turn, en_passant_possible, castling_rights)
        if not capture_moves:
            return stand_pat

        # Move ordering can be applied here as well
        for move in capture_moves:
            self.check_time()
            self.quiescence_depth = getattr(self, 'quiescence_depth', 0) + 1
            start_pos, end_pos = move
            # Copy the game state
            board_copy = copy.deepcopy(board)
            en_passant_copy = copy.deepcopy(en_passant_possible)
            castling_rights_copy = copy_castling_rights(castling_rights)
            move_log_copy = []
            # Make the move
            captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy
            )
            score = -self.quiescence_search(-beta, -alpha, board_copy, self.opponent_color,
                                            new_en_passant_possible, new_castling_rights)
            self.quiescence_depth -= 1
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def evaluate_board(self, board, en_passant_possible, castling_rights):
        evaluation = 0
        # Material and positional evaluation
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

        # Mobility
        my_mobility = len(self.get_all_possible_moves(board, self.color, en_passant_possible, castling_rights))
        opp_mobility = len(self.get_all_possible_moves(board, self.opponent_color, en_passant_possible, castling_rights))
        evaluation += 10 * (my_mobility - opp_mobility)

        # King Safety
        evaluation += self.evaluate_king_safety(board, en_passant_possible, castling_rights)

        # Pawn Structure
        evaluation += self.evaluate_pawn_structure(board)

        # Piece Coordination
        evaluation += self.evaluate_piece_coordination(board)

        # Piece Safety
        evaluation += self.evaluate_piece_safety(board, en_passant_possible, castling_rights)

        return evaluation

    def evaluate_king_safety(self, board, en_passant_possible, castling_rights):
        evaluation = 0
        # Implement a simple king safety evaluation
        # For example, penalize if the king is exposed
        return evaluation

    def evaluate_pawn_structure(self, board):
        evaluation = 0
        my_pawns = []
        opp_pawns = []

        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece == f'{self.color}p':
                    my_pawns.append((row, col))
                elif piece == f'{self.opponent_color}p':
                    opp_pawns.append((row, col))

        # Evaluate isolated pawns
        evaluation -= 20 * self.count_isolated_pawns(my_pawns)
        evaluation += 20 * self.count_isolated_pawns(opp_pawns)

        # Evaluate doubled pawns
        evaluation -= 15 * self.count_doubled_pawns(my_pawns)
        evaluation += 15 * self.count_doubled_pawns(opp_pawns)

        # Evaluate passed pawns
        evaluation += 30 * self.count_passed_pawns(my_pawns, opp_pawns)
        evaluation -= 30 * self.count_passed_pawns(opp_pawns, my_pawns)

        return evaluation

    def count_isolated_pawns(self, pawns):
        isolated_pawns = 0
        for pawn in pawns:
            col = pawn[1]
            has_neighbor = any(p[1] in [col - 1, col + 1] for p in pawns if p != pawn)
            if not has_neighbor:
                isolated_pawns += 1
        return isolated_pawns

    def count_doubled_pawns(self, pawns):
        from collections import defaultdict
        file_counts = defaultdict(int)
        for pawn in pawns:
            file_counts[pawn[1]] += 1
        doubled_pawns = sum(count - 1 for count in file_counts.values() if count > 1)
        return doubled_pawns

    def count_passed_pawns(self, my_pawns, opp_pawns):
        passed_pawns = 0
        for pawn in my_pawns:
            row, col = pawn
            is_passed = True
            for opp_pawn in opp_pawns:
                opp_row, opp_col = opp_pawn
                if opp_col in [col - 1, col, col + 1]:
                    if (self.color == 'w' and opp_row < row) or (self.color == 'b' and opp_row > row):
                        is_passed = False
                        break
            if is_passed:
                passed_pawns += 1
        return passed_pawns

    def evaluate_piece_coordination(self, board):
        evaluation = 0
        # Implement a simple piece coordination evaluation
        # For example, encourage pieces that protect each other
        return evaluation

    def evaluate_piece_safety(self, board, en_passant_possible, castling_rights):
        evaluation = 0

        # Get all possible opponent moves to see which of our pieces are under attack
        opp_moves = self.get_all_possible_moves(board, self.opponent_color, en_passant_possible, castling_rights)
        opp_attack_squares = set(move[1] for move in opp_moves)

        # Get all possible our moves to see which of opponent's pieces are under attack
        my_moves = self.get_all_possible_moves(board, self.color, en_passant_possible, castling_rights)
        my_attack_squares = set(move[1] for move in my_moves)

        # Evaluate the safety of our pieces
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '--':
                    piece_type = piece[1]
                    color = piece[0]
                    position = (row, col)
                    value = self.piece_values.get(piece_type, 0)

                    if color == self.color:
                        if position in opp_attack_squares:
                            # Check if the piece is defended
                            defenders = self.get_defenders(board, position, self.color, en_passant_possible, castling_rights)
                            attackers = self.get_attackers(board, position, self.opponent_color, en_passant_possible, castling_rights)
                            if len(defenders) < len(attackers):
                                # Penalize based on the value of the piece
                                evaluation -= value * 0.5  # Adjust the multiplier as needed
                    else:
                        if position in my_attack_squares:
                            # Check if the piece is defended
                            defenders = self.get_defenders(board, position, self.opponent_color, en_passant_possible, castling_rights)
                            attackers = self.get_attackers(board, position, self.color, en_passant_possible, castling_rights)
                            if len(attackers) > len(defenders):
                                # Reward based on the value of the piece
                                evaluation += value * 0.5  # Adjust the multiplier as needed

        return evaluation

    def get_defenders(self, board, position, color, en_passant_possible, castling_rights):
        defenders = []
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '--' and piece[0] == color:
                    valid_moves = get_valid_moves(board, (row, col), color, en_passant_possible, castling_rights)
                    if position in valid_moves:
                        defenders.append((row, col))
        return defenders

    def get_attackers(self, board, position, color, en_passant_possible, castling_rights):
        attackers = []
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '--' and piece[0] == color:
                    valid_moves = get_valid_moves(board, (row, col), color, en_passant_possible, castling_rights)
                    if position in valid_moves:
                        attackers.append((row, col))
        return attackers

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

    def get_capture_moves(self, board, turn, en_passant_possible, castling_rights):
        capture_moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col][0] == turn:
                    valid_moves = get_valid_moves(board, (row, col), turn, en_passant_possible, castling_rights)
                    for end_pos in valid_moves:
                        target_piece = board[end_pos[0]][end_pos[1]]
                        if target_piece != '--' and target_piece[0] != turn:
                            capture_moves.append(((row, col), end_pos))
                        # Include en passant captures
                        elif board[row][col][1] == 'p' and end_pos == en_passant_possible:
                            capture_moves.append(((row, col), end_pos))
        return capture_moves

    def order_moves(self, moves, board, turn, en_passant_possible, castling_rights):
        """
        Orders moves using advanced heuristics for better pruning.
        """
        def move_priority(move):
            start_pos, end_pos = move
            piece_moved = board[start_pos[0]][start_pos[1]]
            piece_captured = board[end_pos[0]][end_pos[1]]

            priority = 0

            # MVV-LVA
            if piece_captured != '--':
                value_captured = self.piece_values.get(piece_captured[1], 0)
                value_moved = self.piece_values.get(piece_moved[1], 0)
                priority += 10 * value_captured - value_moved

            # Killer Moves
            if move in self.killer_moves.get(self.current_depth, []):
                priority += 50

            # History Heuristic
            priority += self.history_heuristic.get(move, 0)

            # Checks
            # Make the move and see if it results in a check
            board_copy = copy.deepcopy(board)
            en_passant_copy = copy.deepcopy(en_passant_possible)
            castling_rights_copy = copy_castling_rights(castling_rights)
            move_log_copy = []
            make_move(board_copy, start_pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy)
            if in_check(board_copy, self.opponent_color if turn == self.color else self.color):
                priority += 25

            return -priority  # Negative for descending order

        ordered_moves = sorted(moves, key=move_priority)
        return ordered_moves