# chess_logic.py

def is_valid_move(board, start_pos, end_pos, turn, en_passant_possible, castling_rights):
    """
    Checks if a move from start_pos to end_pos is valid for the current player.
    """
    piece = board[start_pos[0]][start_pos[1]]
    if piece == '--' or piece[0] != turn:
        return False  # Can't move empty squares or opponent's pieces
    valid_moves = get_valid_moves(board, start_pos, turn, en_passant_possible, castling_rights)
    return end_pos in valid_moves

def get_valid_moves(board, pos, turn, en_passant_possible, castling_rights):
    """
    Returns a list of valid moves for the piece at the given position.
    Filters out moves that would leave the king in check.
    """
    piece = board[pos[0]][pos[1]]
    if piece == '--' or piece[0] != turn:
        return []
    piece_type = piece[1]
    color = piece[0]
    moves = []
    if piece_type == 'p':
        potential_moves = get_pawn_moves(board, pos, color, en_passant_possible)
    elif piece_type == 'R':
        potential_moves = get_rook_moves(board, pos, color)
    elif piece_type == 'N':
        potential_moves = get_knight_moves(board, pos, color)
    elif piece_type == 'B':
        potential_moves = get_bishop_moves(board, pos, color)
    elif piece_type == 'Q':
        potential_moves = get_queen_moves(board, pos, color)
    elif piece_type == 'K':
        potential_moves = get_king_moves(board, pos, color, castling_rights)
    else:
        potential_moves = []

    # Filter out moves that leave the king in check
    valid_moves = []
    for end_pos in potential_moves:
        # Make copies of the board and game state
        board_copy = [row[:] for row in board]
        en_passant_copy = en_passant_possible
        castling_rights_copy = copy_castling_rights(castling_rights)
        move_log_copy = []
        # Simulate the move
        make_move(board_copy, pos, end_pos, en_passant_copy, castling_rights_copy, move_log_copy)
        # Check if king is in check
        if not in_check(board_copy, color):
            valid_moves.append(end_pos)
    return valid_moves

def get_pawn_moves(board, pos, color, en_passant_possible):
    """
    Generates valid moves for a pawn at the given position.
    """
    moves = []
    direction = -1 if color == 'w' else 1
    start_row = 6 if color == 'w' else 1
    row, col = pos
    # Move forward
    next_row = row + direction
    if is_in_bounds(next_row, col) and board[next_row][col] == '--':
        moves.append((next_row, col))
        # Double move from starting position
        if row == start_row:
            next_row_2 = row + 2 * direction
            if is_in_bounds(next_row_2, col) and board[next_row_2][col] == '--':
                moves.append((next_row_2, col))
    # Captures
    for offset in [-1, 1]:
        new_col = col + offset
        new_row = row + direction
        if is_in_bounds(new_row, new_col):
            target_piece = board[new_row][new_col]
            if target_piece != '--' and target_piece[0] != color:
                moves.append((new_row, new_col))
            elif (new_row, new_col) == en_passant_possible:
                moves.append((new_row, new_col))
    return moves

def get_rook_moves(board, pos, color):
    """
    Generates valid moves for a rook at the given position.
    """
    moves = []
    row, col = pos
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, down, left, right
    for d in directions:
        for i in range(1, 8):
            new_row = row + d[0]*i
            new_col = col + d[1]*i
            if is_in_bounds(new_row, new_col):
                target_piece = board[new_row][new_col]
                if target_piece == '--':
                    moves.append((new_row, new_col))
                elif target_piece[0] != color:
                    moves.append((new_row, new_col))
                    break  # Can't move past opponent's piece
                else:
                    break  # Blocked by own piece
            else:
                break  # Out of bounds
    return moves

def get_knight_moves(board, pos, color):
    """
    Generates valid moves for a knight at the given position.
    """
    moves = []
    row, col = pos
    knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                    (1, -2), (1, 2), (2, -1), (2, 1)]
    for move in knight_moves:
        new_row = row + move[0]
        new_col = col + move[1]
        if is_in_bounds(new_row, new_col):
            target_piece = board[new_row][new_col]
            if target_piece == '--' or target_piece[0] != color:
                moves.append((new_row, new_col))
    return moves

def get_bishop_moves(board, pos, color):
    """
    Generates valid moves for a bishop at the given position.
    """
    moves = []
    row, col = pos
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonals
    for d in directions:
        for i in range(1, 8):
            new_row = row + d[0]*i
            new_col = col + d[1]*i
            if is_in_bounds(new_row, new_col):
                target_piece = board[new_row][new_col]
                if target_piece == '--':
                    moves.append((new_row, new_col))
                elif target_piece[0] != color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
            else:
                break
    return moves

def get_queen_moves(board, pos, color):
    """
    Generates valid moves for a queen at the given position.
    """
    # Queen's moves are the combination of rook and bishop moves
    return get_rook_moves(board, pos, color) + get_bishop_moves(board, pos, color)

def get_king_moves(board, pos, color, castling_rights):
    """
    Generates valid moves for a king at the given position, including castling.
    """
    moves = []
    row, col = pos
    king_moves = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    for move in king_moves:
        new_row = row + move[0]
        new_col = col + move[1]
        if is_in_bounds(new_row, new_col):
            target_piece = board[new_row][new_col]
            if target_piece == '--' or target_piece[0] != color:
                moves.append((new_row, new_col))
    # Castling moves
    if castling_rights[color]['king_side'] and can_castle(board, pos, color, 'king_side'):
        moves.append((row, col + 2))
    if castling_rights[color]['queen_side'] and can_castle(board, pos, color, 'queen_side'):
        moves.append((row, col - 2))
    return moves

def is_in_bounds(row, col):
    """
    Checks if a given position is within the bounds of the board.
    """
    return 0 <= row < 8 and 0 <= col < 8

def make_move(board, start_pos, end_pos, en_passant_possible, castling_rights, move_log):
    """
    Executes a move on the board and returns any captured piece.
    Also returns updated en_passant_possible and castling_rights.
    """
    piece_moved = board[start_pos[0]][start_pos[1]]
    piece_captured = board[end_pos[0]][end_pos[1]]

    board[end_pos[0]][end_pos[1]] = piece_moved
    board[start_pos[0]][start_pos[1]] = '--'

    move_log.append((start_pos, end_pos, piece_moved, piece_captured))

    # Update en passant possibility
    new_en_passant_possible = ()
    if piece_moved[1] == 'p':
        if abs(start_pos[0] - end_pos[0]) == 2:
            new_en_passant_possible = ((start_pos[0] + end_pos[0]) // 2, start_pos[1])
        else:
            new_en_passant_possible = ()
        # En passant capture
        if end_pos == en_passant_possible:
            if piece_moved[0] == 'w':
                board[end_pos[0] + 1][end_pos[1]] = '--'
            else:
                board[end_pos[0] - 1][end_pos[1]] = '--'
    else:
        new_en_passant_possible = ()

    # Handle castling
    new_castling_rights = update_castling_rights(piece_moved, start_pos, castling_rights)
    if piece_moved[1] == 'K':
        if abs(start_pos[1] - end_pos[1]) == 2:
            if end_pos[1] > start_pos[1]:  # King-side castling
                board[start_pos[0]][start_pos[1] + 1] = board[start_pos[0]][7]
                board[start_pos[0]][7] = '--'
            else:  # Queen-side castling
                board[start_pos[0]][start_pos[1] - 1] = board[start_pos[0]][0]
                board[start_pos[0]][0] = '--'

    return piece_captured, new_en_passant_possible, new_castling_rights

def undo_move(board, move_log, en_passant_possible, castling_rights):
    """
    Reverses the last move made.
    """
    if len(move_log) == 0:
        return
    last_move = move_log.pop()
    start_pos, end_pos, piece_moved, piece_captured = last_move
    board[start_pos[0]][start_pos[1]] = piece_moved
    board[end_pos[0]][end_pos[1]] = piece_captured

    # Update en passant possible
    # For simplicity, reset en_passant_possible and castling_rights
    en_passant_possible = ()
    # You may need to implement a more sophisticated method to fully restore previous states
    # For now, this should suffice for basic functionality

def update_castling_rights(piece_moved, start_pos, castling_rights):
    """
    Updates the castling rights after a move.
    Returns the updated castling_rights dictionary.
    """
    new_castling_rights = copy_castling_rights(castling_rights)
    if piece_moved[1] == 'K':
        new_castling_rights[piece_moved[0]]['king_side'] = False
        new_castling_rights[piece_moved[0]]['queen_side'] = False
    elif piece_moved[1] == 'R':
        if start_pos == (7, 0):  # White queen-side rook
            new_castling_rights['w']['queen_side'] = False
        elif start_pos == (7, 7):  # White king-side rook
            new_castling_rights['w']['king_side'] = False
        elif start_pos == (0, 0):  # Black queen-side rook
            new_castling_rights['b']['queen_side'] = False
        elif start_pos == (0, 7):  # Black king-side rook
            new_castling_rights['b']['king_side'] = False
    return new_castling_rights

def copy_castling_rights(castling_rights):
    """
    Returns a deep copy of the castling rights dictionary.
    """
    return {
        'w': {'king_side': castling_rights['w']['king_side'], 'queen_side': castling_rights['w']['queen_side']},
        'b': {'king_side': castling_rights['b']['king_side'], 'queen_side': castling_rights['b']['queen_side']}
    }

def can_castle(board, pos, color, side):
    """
    Determines if castling is possible for the given side (king_side or queen_side).
    """
    row, col = pos
    if in_check(board, color):
        return False
    if side == 'king_side':
        # Squares between king and rook must be empty
        if board[row][col + 1] != '--' or board[row][col + 2] != '--':
            return False
        # Squares king passes through must not be under attack
        if square_under_attack(board, (row, col + 1), color) or square_under_attack(board, (row, col + 2), color):
            return False
        # Rook must be in correct position
        if board[row][7] != color + 'R':
            return False
    elif side == 'queen_side':
        # Squares between king and rook must be empty
        if board[row][col - 1] != '--' or board[row][col - 2] != '--' or board[row][col - 3] != '--':
            return False
        # Squares king passes through must not be under attack
        if square_under_attack(board, (row, col - 1), color) or square_under_attack(board, (row, col - 2), color):
            return False
        # Rook must be in correct position
        if board[row][0] != color + 'R':
            return False
    else:
        return False
    return True

def in_check(board, color):
    """
    Determines if the current player is in check.
    """
    king_pos = find_king(board, color)
    return square_under_attack(board, king_pos, color)

def square_under_attack(board, pos, color):
    """
    Checks if the given square is under attack by the opponent.
    """
    opponent_color = 'b' if color == 'w' else 'w'
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != '--' and piece[0] == opponent_color:
                piece_moves = get_valid_moves_for_attack(board, (row, col), opponent_color)
                if pos in piece_moves:
                    return True
    return False

def get_valid_moves_for_attack(board, pos, color):
    """
    Returns a list of valid moves for attack purposes (excluding special moves like castling).
    """
    piece = board[pos[0]][pos[1]]
    piece_type = piece[1]
    if piece_type == 'p':
        return get_pawn_attack_moves(board, pos, color)
    elif piece_type == 'R':
        return get_rook_moves(board, pos, color)
    elif piece_type == 'N':
        return get_knight_moves(board, pos, color)
    elif piece_type == 'B':
        return get_bishop_moves(board, pos, color)
    elif piece_type == 'Q':
        return get_queen_moves(board, pos, color)
    elif piece_type == 'K':
        return get_king_attack_moves(board, pos, color)
    else:
        return []

def get_pawn_attack_moves(board, pos, color):
    """
    Generates attack moves for a pawn (used for checking attacks).
    """
    moves = []
    direction = -1 if color == 'w' else 1
    row, col = pos
    for offset in [-1, 1]:
        new_col = col + offset
        new_row = row + direction
        if is_in_bounds(new_row, new_col):
            moves.append((new_row, new_col))
    return moves

def get_king_attack_moves(board, pos, color):
    """
    Generates attack moves for a king (excluding castling).
    """
    moves = []
    row, col = pos
    king_moves = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    for move in king_moves:
        new_row = row + move[0]
        new_col = col + move[1]
        if is_in_bounds(new_row, new_col):
            moves.append((new_row, new_col))
    return moves

def get_all_possible_moves(board, color, en_passant_possible, castling_rights):
    """
    Generates all possible legal moves for the current player.
    """
    moves = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != '--' and piece[0] == color:
                valid_moves = get_valid_moves(board, (row, col), color, en_passant_possible, castling_rights)
                for end_pos in valid_moves:
                    # Make the move
                    board_copy = [row[:] for row in board]
                    en_passant_copy = en_passant_possible
                    castling_rights_copy = copy_castling_rights(castling_rights)
                    move_log_copy = []
                    captured_piece, new_en_passant_possible, new_castling_rights = make_move(
                        board_copy, (row, col), end_pos, en_passant_copy, castling_rights_copy, move_log_copy
                    )
                    # Check if move puts player in check
                    if not in_check(board_copy, color):
                        moves.append(((row, col), end_pos))
                    # No need to undo move since we're using a copy
    return moves

def find_king(board, color):
    """
    Finds the position of the king for the given color.
    """
    for row in range(8):
        for col in range(8):
            if board[row][col] == color + 'K':
                return (row, col)
    return None