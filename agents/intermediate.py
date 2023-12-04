# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time
import random


@register_agent("student_agent")
class StudentAgent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    def __init__(self):
        super(StudentAgent, self).__init__()
        self.name = "StudentAgent"
        self.dir_map = {
            "u": 0,
            "r": 1,
            "d": 2,
            "l": 3,
        }

    def evaluate(self, chess_board, my_pos, my_dir, adv_pos):
        score = 0

        # 1. Immediate threat of being trapped
        if self.is_three_sided(my_pos, chess_board):
            score -= 500  # Heavy penalty for being nearly trapped

        # 2. Evaluate the possibility of trapping the opponent
        if self.is_three_sided(adv_pos, chess_board):
            score += 500  # High reward for nearly trapping the opponent

        # 3. Mobility - Number of move options
        my_move_options = self.count_move_options(my_pos, chess_board)
        score += my_move_options * 10

        # 4. Opponent's mobility
        opp_move_options = self.count_move_options(adv_pos, chess_board)
        score -= opp_move_options * 10

        # 5. Distance from the opponent - less emphasis as depth is 1
        distance_to_opponent = self.calculate_distance(my_pos, adv_pos)
        score -= distance_to_opponent * 5

        # 6. Check if the wall placement extends a wall
        if self.is_extending_wall(my_pos, my_dir, chess_board):
            score += 100  # Reward for extending a wall

        # 7. Check if the wall placement helps in trapping the opponent
        if self.is_trapping_opponent(my_pos, my_dir, adv_pos, chess_board):
            score += 200  # Additional reward for moves that help in trapping the opponent

        # 8. Evaluate wall placement in terms of cutting off areas
        accessible_area_proportion = self.does_wall_cut_off_area(my_pos, my_dir, chess_board, adv_pos)
        # Calculate the score based on the area cut off
        # For example, if 70% of the area is cut off, subtract 70% of a maximum cutoff score
        max_cutoff_score = 300  # Maximum score for completely cutting off the opponent
        score += (1 - accessible_area_proportion) * max_cutoff_score

        return score

    ### Helper functions for evaluate (implement these based on game logic) ###

    # 1. Check for being surrounded by 3 walls
    def is_three_sided(self, pos, chess_board):
        r, c = pos
        sides_with_walls = 0

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # Check each side for a wall
        for i, move in enumerate(moves):
            new_r, new_c = r + move[0], c + move[1]
            if chess_board[r, c, i] or not (0 <= new_r < chess_board.shape[0] and 0 <= new_c < chess_board.shape[1]):
                sides_with_walls += 1

        return sides_with_walls == 3

    # 2. Check for how many move options you would have after ending
    def count_move_options(self, pos, chess_board):
        r, c = pos
        move_options = 0

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # Count viable moves
        for i, move in enumerate(moves):
            new_r, new_c = r + move[0], c + move[1]
            if not chess_board[r, c, i] and 0 <= new_r < chess_board.shape[0] and 0 <= new_c < chess_board.shape[1]:
                move_options += 1

        return move_options

    # 3. Check your distance from opponent
    def calculate_distance(self, pos1, pos2):

        # Manhattan distance
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # 4. “continuing” a wall or pattern is more effective than moving to purely free space
    def is_extending_wall(self, pos, dir, chess_board):
        # Determine if placing a wall in the given direction extends an existing wall
        r, c = pos

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # Check the adjacent cell in the direction of the wall placement
        new_r, new_c = r + moves[dir][0], c + moves[dir][1]
        if 0 <= new_r < chess_board.shape[0] and 0 <= new_c < chess_board.shape[1]:
            # Check if there's already a wall in the opposite direction
            return chess_board[new_r, new_c, (dir + 2) % 4]
        return False
    
    # 5. predicting whether placing a wall in a given direction will significantly limit the opponent's mobility or potentially lead to their entrapment
    def is_trapping_opponent(self, my_pos, my_dir, adv_pos, chess_board):
        # Simulate placing the wall
        new_chess_board = deepcopy(chess_board)
        r, c = my_pos
        new_chess_board[r, c, my_dir] = True

        # Count the opponent's move options before and after placing the wall
        original_move_options = self.count_move_options(adv_pos, chess_board)
        new_move_options = self.count_move_options(adv_pos, new_chess_board)

        # If the number of move options is significantly reduced, return True
        return new_move_options < original_move_options
    
    # 6. Score depend on the portion of the area cut off by the wall placement
    def does_wall_cut_off_area(self, pos, dir, chess_board, adv_pos):
        # Place the wall
        new_chess_board = deepcopy(chess_board)
        r, c = pos
        new_chess_board[r, c, dir] = True

        # Perform a flood fill from the opponent's position
        accessible_area = self.flood_fill(adv_pos, new_chess_board)
        total_area = chess_board.shape[0] * chess_board.shape[1]

        # Return the proportion of the accessible area
        return accessible_area / total_area

    def flood_fill(self, start_pos, chess_board):
        queue = [start_pos]
        visited = set()
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Up, Right, Down, Left

        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited:
                continue
            visited.add((r, c))

            for i, (dr, dc) in enumerate(directions):
                new_r, new_c = r + dr, c + dc
                if 0 <= new_r < chess_board.shape[0] and 0 <= new_c < chess_board.shape[1]:
                    if not chess_board[r, c, i]:  # Check if no wall in the direction
                        queue.append((new_r, new_c))

        return len(visited)
    
    # 7. Counts barrier, good indicator for game development
    def count_barriers(self, chess_board):
        barrier_count = 0
        for row in chess_board:
            for cell in row:
                # Summing the boolean values for barriers in each direction
                barrier_count += sum(cell)  
                
        return barrier_count

    # 8. Check for end game
    def is_end_game_start(self, chess_board):

        board_size = chess_board.shape[0] * chess_board.shape[1] * chess_board.shape[2]
        barrier_count = self.count_barriers(chess_board)

        # Calculate the percentage of the board occupied by barriers
        percentage_occupied = (barrier_count / board_size) * 100

        # Define a threshold percentage to mark the start of the end game
        end_game_threshold = 28  # This is an example value, adjust based on your game dynamics

        return percentage_occupied >= end_game_threshold
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # def minimax(self, chess_board, depth, is_maximizing_player, my_pos, adv_pos, max_step, alpha, beta):

    #     if depth == 0:
    #         if is_maximizing_player:
    #             return self.evaluate(chess_board, my_pos, adv_pos)
    #         else:
    #             return self.evaluate(chess_board, adv_pos, my_pos)

    #     if is_maximizing_player:
    #         max_eval = float('-inf')
    #         moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
    #         for move in self.best_guess_moves(moves, adv_pos, chess_board):

    #             new_pos, barrier_dir = move
    #             r, c = new_pos

    #             new_chess_board = deepcopy(chess_board)
    #             new_chess_board[r, c, barrier_dir] = True

    #             eval = self.minimax(new_chess_board, depth - 1, False, new_pos, adv_pos, max_step, alpha, beta)
    #             max_eval = max(max_eval, eval)
    #             alpha = max(alpha, max_eval)
    #             if beta <= alpha:
    #                 break
    #         return max_eval
    #     else:
    #         min_eval = float('inf')
    #         moves = self.generate_moves(chess_board, adv_pos, my_pos, max_step)
    #         for move in self.best_guess_moves(moves, my_pos, chess_board):
                
    #             new_pos, barrier_dir = move
    #             r, c = new_pos
                
    #             new_chess_board = deepcopy(chess_board)
    #             new_chess_board[r, c, barrier_dir] = True
                
    #             eval = self.minimax(new_chess_board, depth - 1, True, my_pos, new_pos, max_step, alpha, beta)
    #             min_eval = min(min_eval, eval)
    #             beta = min(beta, min_eval)
    #             if beta <= alpha:
    #                 break
    #         return min_eval





    # def evaluate_endgame(self, chess_board, my_pos, my_dir, adv_pos, max_step):
    #     score = 0

    #     # 1. Territory Maximization
    #     my_territory = self.calculate_teritory(chess_board, my_pos)
    #     adv_territory = self.calculate_teritory(chess_board, adv_pos)
    #     score += (my_territory - adv_territory) * 30

    #     # 2. Threats to Opponent
    #     if self.is_direct_threat(my_pos, my_dir, adv_pos, chess_board):
    #         score += 150

    #     # 3. Defensive Play
    #     if my_territory > adv_territory:
    #         score += 75  # Bonus for maintaining a lead

    #     # 4. Opponent Move Prediction
    #     opponent_threat = self.predict_opponent_moves(chess_board, adv_pos, my_pos, max_step)
    #     threat_penalty = 75  # Adjust this value based on your game's strategy
    #     score -= opponent_threat * threat_penalty

    #     return score

    def evaluate_endgame(self, chess_board, my_pos, my_dir, adv_pos, max_step):
        score = 0

        # 1. Territory Maximization (Safe Expansion)
        my_territory = self.calculate_teritory(chess_board, my_pos)
        adv_territory = self.calculate_teritory(chess_board, adv_pos)
        score += (my_territory - adv_territory) * 25  # Slightly increased weight

        # 2. Threats to Opponent (Reduced Aggression)
        # Being less aggressive might be more effective against a random agent
        if self.is_direct_threat(my_pos, my_dir, adv_pos, chess_board):
            score += 75  # Reduced from 100

        # 3. Defensive Play (Emphasize in Late Game)
        # Increase the bonus for maintaining a lead in the late game
        if my_territory > adv_territory:
            late_game_multiplier = 1.5 if self.is_late_game(chess_board) else 1
            score += 50 * late_game_multiplier  # Bonus for maintaining a lead

        # 4. Opponent Move Prediction (Adaptive)
        # Adjust threat penalty based on game progress
        opponent_threat = self.predict_opponent_moves(chess_board, adv_pos, my_pos, max_step)
        threat_penalty = 75 if self.is_late_game(chess_board) else 50
        score -= opponent_threat * threat_penalty

        # 5. Wall Placement Strategy (Advanced)
        # Additional points for strategic wall placements
        if self.is_strategic_wall_placement(my_pos, my_dir, chess_board, adv_pos, max_step):
            score += 30  # Reward for strategic wall placement

        return score

    def is_late_game(self, chess_board):
        total_walls = np.sum(chess_board)
        board_size = chess_board.shape[0]
        late_game_threshold = board_size * 4  # Adjust as necessary
        return total_walls >= late_game_threshold

    def is_strategic_wall_placement(self, pos, dir, chess_board, adv_pos, max_step):
        # Place the wall in the specified direction
        r, c = pos
        new_chess_board = deepcopy(chess_board)
        new_chess_board[r, c, dir] = True

        # Check for area control improvement
        my_territory_before = self.calculate_teritory(chess_board, pos)
        my_territory_after = self.calculate_teritory(new_chess_board, pos)

        # Check if the wall limits opponent's mobility or cuts off paths
        opponent_mobility_reduced = self.does_wall_limit_opponent(new_chess_board, pos, dir, adv_pos, max_step)

        return my_territory_after > my_territory_before or opponent_mobility_reduced


    def does_wall_limit_opponent(self, chess_board, my_pos, dir, adv_pos, max_step):
        # Simulate wall placement
        r, c = my_pos
        new_chess_board = deepcopy(chess_board)
        new_chess_board[r, c, dir] = True

        # Calculate opponent's mobility before and after the wall placement
        original_mobility = self.count_move_options(adv_pos, chess_board)
        new_mobility = self.count_move_options(adv_pos, new_chess_board)

        # Check if the wall significantly reduces the opponent's mobility
        mobility_reduced = new_mobility < original_mobility

        # Additionally, check if the wall placement potentially leads to trapping the opponent
        is_trapping_move = self.is_potential_trap(new_chess_board, adv_pos, max_step)

        return mobility_reduced or is_trapping_move

    def is_potential_trap(self, chess_board, adv_pos, max_step):
        # Check if the opponent's position is becoming more restricted
        # This could involve checking for a reduced number of escape routes or enclosed areas
        move_options = self.generate_moves(chess_board, adv_pos, None, max_step)
        return len(move_options) <= 1  # Adjust the threshold as needed


    
    def calculate_teritory(self, chess_board, pos):
        visited = set()
        queue = [pos]
        territory_count = 0

        # Directions: Up, Right, Down, Left
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]

        while queue:
            current_pos = queue.pop(0)
            if current_pos in visited:
                continue

            visited.add(current_pos)
            territory_count += 1
            r, c = current_pos

            for i, (dr, dc) in enumerate(directions):
                new_r, new_c = r + dr, c + dc
                if 0 <= new_r < chess_board.shape[0] and 0 <= new_c < chess_board.shape[1]:
                    if not chess_board[r, c, i]:  # No wall in this direction
                        new_pos = (new_r, new_c)
                        if new_pos not in visited:
                            queue.append(new_pos)

        return territory_count
    

    def is_direct_threat(self, my_pos, my_dir, adv_pos, chess_board):
        new_chess_board = deepcopy(chess_board)
        r, c = my_pos

        # Place the wall in the specified direction
        new_chess_board[r, c, my_dir] = True

        # Check if the opponent has significantly fewer move options after the wall is placed
        original_move_options = self.count_move_options(adv_pos, chess_board)
        new_move_options = self.count_move_options(adv_pos, new_chess_board)

        # Consider it a direct threat if the opponent's move options are significantly reduced
        # You can adjust the threshold as needed
        return new_move_options < original_move_options
    

    def predict_opponent_moves(self, chess_board, adv_pos, my_pos, max_step):
        potential_threat = 0
        opponent_moves = self.generate_moves(chess_board, adv_pos, my_pos, max_step)

        # Evaluate each of the opponent's potential moves
        for move in opponent_moves:
            new_pos, barrier_dir = move
            new_chess_board = deepcopy(chess_board)
            new_chess_board[new_pos[0], new_pos[1], barrier_dir] = True

            # Check if any of these moves pose a direct threat to the player
            if self.is_direct_threat(adv_pos, barrier_dir, my_pos, new_chess_board):
                potential_threat += 1

        return potential_threat

    # def evaluate_minimax(self, chess_board, my_pos, adv_pos):
    #     score = 0

    #     # 1. Immediate threat of being trapped
    #     if self.is_three_sided(my_pos, chess_board):
    #         score -= 500  # Heavy penalty for being nearly trapped

    #     # 2. Evaluate the possibility of trapping the opponent
    #     if self.is_three_sided(adv_pos, chess_board):
    #         score += 500  # High reward for nearly trapping the opponent

    #     # 3. Mobility - Number of move options
    #     my_move_options = self.count_move_options(my_pos, chess_board)
    #     score += my_move_options * 10

    #     # 4. Opponent's mobility
    #     opp_move_options = self.count_move_options(adv_pos, chess_board)
    #     score -= opp_move_options * 10

    #     # 5. Distance from the opponent - less emphasis as depth is 1
    #     distance_to_opponent = self.calculate_distance(my_pos, adv_pos)
    #     score -= distance_to_opponent * 5

    #     return score

    # def minimax(self, chess_board, depth, is_maximizing_player, my_pos, adv_pos, max_step, alpha, beta):
        
    #     isEndGame, my_score, adv_score = self.check_endgame(chess_board, my_pos, adv_pos)

    #     if isEndGame:
    #         # print("wooooo    " + str(my_score) + "     " + str(adv_score))
    #         if is_maximizing_player:
    #             if my_score > adv_score:
    #                 return my_score, None
    #             elif my_score < adv_score:
    #                 return -adv_score, None
    #             else:
    #                 return 0, None
    #         else:
    #             if my_score > adv_score:
    #                 return -my_score, None
    #             elif my_score < adv_score:
    #                 return adv_score, None
    #             else:
    #                 return 0, None

    #     if is_maximizing_player:
    #         max_eval = float('-inf')
    #         best_move = None
    #         moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
    #         for move in self.best_guess_moves(moves, adv_pos, chess_board):
    #             new_pos, barrier_dir = move
    #             r, c = new_pos

    #             new_chess_board = deepcopy(chess_board)
    #             new_chess_board[r, c, barrier_dir] = True

    #             eval, _ = self.minimax(new_chess_board, depth - 1, False, new_pos, adv_pos, max_step, alpha, beta)
    #             if eval > max_eval:
    #                 max_eval = eval
    #                 best_move = move
    #             alpha = max(alpha, eval)
    #             if beta <= alpha:
    #                 break
    #         return max_eval, best_move
    #     else:
    #         min_eval = float('inf')
    #         best_move = None
    #         moves = self.generate_moves(chess_board, adv_pos, my_pos, max_step)
    #         for move in self.best_guess_moves(moves, my_pos, chess_board):
    #             new_pos, barrier_dir = move
    #             r, c = new_pos

    #             new_chess_board = deepcopy(chess_board)
    #             new_chess_board[r, c, barrier_dir] = True

    #             eval, _ = self.minimax(new_chess_board, depth - 1, True, my_pos, new_pos, max_step, alpha, beta)
    #             if eval < min_eval:
    #                 min_eval = eval
    #                 best_move = move
    #             beta = min(beta, eval)
    #             if beta <= alpha:
    #                 break
    #         return min_eval, best_move

    def minimax(self, chess_board, depth, is_maximizing_player, my_pos, adv_pos, max_step, alpha, beta):
    
        isEndGame, my_score, adv_score = self.check_endgame(chess_board, my_pos, adv_pos)

        if isEndGame or depth == 0:  # Terminate if it's endgame or depth is 0
            #print("wooooo    " + str(my_score) + "     " + str(adv_score))
            if my_score > adv_score:
                return my_score, None
            elif my_score < adv_score:
                return -adv_score, None
            else:
                return 0, None

        if is_maximizing_player:
            max_eval = float('-inf')
            best_move = None
            moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
            for move in self.best_guess_moves(moves, adv_pos, chess_board):
                new_pos, barrier_dir = move
                new_chess_board = deepcopy(chess_board)
                new_chess_board[new_pos[0], new_pos[1], barrier_dir] = True

                eval, _ = self.minimax(new_chess_board, depth - 1, False, new_pos, adv_pos, max_step, alpha, beta)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            moves = self.generate_moves(chess_board, adv_pos, my_pos, max_step)
            for move in self.best_guess_moves(moves, my_pos, chess_board):
                new_pos, barrier_dir = move
                new_chess_board = deepcopy(chess_board)
                new_chess_board[new_pos[0], new_pos[1], barrier_dir] = True

                eval, _ = self.minimax(new_chess_board, depth - 1, True, my_pos, new_pos, max_step, alpha, beta)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

        

    def step(self, chess_board, my_pos, adv_pos, max_step):

        if self.is_end_game_start(chess_board):
            #print("end_game!")
            best_move = None
            best_score = float('-inf')
            depth = 0

            alpha = float('-inf')
            beta = float('inf')

            if chess_board.shape[0] < 8:
                depth = 7
            elif chess_board.shape[0] >= 8 and chess_board.shape[0] <= 10:
                depth = 5
            else:
                depth = 3

            score, best_move = self.minimax(chess_board, depth, True, my_pos, adv_pos, max_step, alpha, beta)
            if best_move is None:
                moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
                best_moves = self.best_guess_moves(moves, adv_pos, chess_board)
                best_move = best_moves[0]

            return best_move
            # moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
            # best_move = self.best_guess_moves_endgame(moves, adv_pos, chess_board, max_step)

            # return best_move[0]
        else:
            moves = self.generate_moves(chess_board, my_pos, adv_pos, max_step)
            best_move = self.best_guess_moves(moves, adv_pos, chess_board)

            return best_move[0]
        

    def best_guess_moves(self, moves, adv_pos, chess_board):
        best_guess_moves_score = []
        for index, move in enumerate(moves):
            score = self.evaluate(chess_board, move[0], move[1], adv_pos)
            best_guess_moves_score.append((score, index))

        # Sort the moves by their scores in descending order
        best_guess_moves_score.sort(reverse=True, key=lambda x: x[0])

        # Get the indices of the top 10 moves
        top_indices = [move_score[1] for move_score in best_guess_moves_score[:3]]

        # Retrieve the top 3 moves using the indices
        top_moves = [moves[index] for index in top_indices]

        return top_moves
    
    def best_guess_moves_endgame(self, moves, adv_pos, chess_board, max_step):
        best_guess_moves_score = []
        for index, move in enumerate(moves):
            score = self.evaluate_endgame(chess_board, move[0], move[1], adv_pos, max_step)
            best_guess_moves_score.append((score, index))

        # Sort the moves by their scores in descending order
        best_guess_moves_score.sort(reverse=True, key=lambda x: x[0])

        # Get the indices of the top 10 moves
        top_indices = [move_score[1] for move_score in best_guess_moves_score[:3]]

        # Retrieve the top 3 moves using the indices
        top_moves = [moves[index] for index in top_indices]

        return top_moves
    
    
    def generate_moves(self, chess_board, my_pos, adv_pos, max_step):
        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        possible_moves = set()

        # Generate all possible positions after moving up to max_step steps
        for step in range(0, max_step + 1):
            for move in moves:
                new_r = my_pos[0] + move[0] * step
                new_c = my_pos[1] + move[1] * step

                # Check if the new position is valid
                if (0 <= new_r < chess_board.shape[0] and
                    0 <= new_c < chess_board.shape[1] and
                    not (new_r, new_c) == adv_pos and
                    self.is_path_clear(chess_board, my_pos, (new_r, new_c), adv_pos, move, moves.index(move))):

                    # For each valid position, generate possible barrier placements
                    for dir in range(4):
                        # Check if it's possible to place a barrier in this direction
                        if not chess_board[new_r, new_c, dir]:
                            possible_moves.add(((new_r, new_c), dir))

        return list(possible_moves)


    def is_path_clear(self, chess_board, start_pos, end_pos, adv_pos, move, dir):

        # Check if the path from start_pos to end_pos is clear of barriers
        r, c = start_pos
        while (r, c) != end_pos:

            # If there's a barrier in the direction of the move or adv is on path
            if chess_board[r, c, dir] or (r, c) == adv_pos:
                return False
            
            # continue checking path
            r += move[0]
            c += move[1]

        return True
    

    def check_endgame(self, chess_board, p0_pos, p1_pos):
        """
        ** edit end game function from world.py **
        Check if the game ends.

        Returns
        -------
        is_endgame : bool
            Whether the game ends.
        """

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        board_size = chess_board.shape[0]

        # Union-Find
        father = dict()
        for r in range(board_size):
            for c in range(board_size):
                father[(r, c)] = (r, c)

        def find(pos):
            if father[pos] != pos:
                father[pos] = find(father[pos])
            return father[pos]

        def union(pos1, pos2):
            father[pos1] = pos2

        for r in range(board_size):
            for c in range(board_size):
                for dir, move in enumerate(moves[1:3]):  # Only check down and right
                    if chess_board[r, c, dir + 1]:
                        continue
                    pos_a = find((r, c))
                    pos_b = find((r + move[0], c + move[1]))
                    if pos_a != pos_b:
                        union(pos_a, pos_b)

        for r in range(board_size):
            for c in range(board_size):
                find((r, c))
        p0_r = find(tuple(p0_pos))
        p1_r = find(tuple(p1_pos))
        p0_score = list(father.values()).count(p0_r)
        p1_score = list(father.values()).count(p1_r)

        # Game ends if players are in different regions
        return (p0_r != p1_r), p0_score, p1_score