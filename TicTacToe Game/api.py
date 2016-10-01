# -*- coding: utf-8 -*-`
"""api.py - contains game logic and high-level API Implementation"""


import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import (
    StringMessage, NewGameForm, GameForm, MakeMoveForm, ScoreForms, 
    GetHighScoresForm, UserRankingsForm, UserRankingForm, UserGamesForm)
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(GetHighScoresForm)
GET_USER_RANKINGS_REQUEST = endpoints.ResourceContainer()
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))
MEMCACHE_MOVES = 'MOVES'

@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email,
                    games_won=0, games_lost=0, performance=0.0)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        opponent = User.query(User.name == request.opponent_name).get()

        if not user or not opponent:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        if user == opponent:
            raise endpoints.ForbiddenException(
                'A user can not play by themselves')
        game = Game.new_game(user.key, opponent.key)

        # Use a task queue to update the average moves.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_moves')
        return game.to_form('Good luck playing Tic Tac Toe!')

    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms, 
                      path='scores/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns a list of high scores is descending order"""
        sorted_scores = sorted(Score.query(), 
            key=lambda x: x.moves, reverse=True)
        return ScoreForms(items=[score.to_form() for score in sorted_scores])

    @endpoints.method(request_message=GET_USER_RANKINGS_REQUEST,
                      response_message=UserRankingsForm, 
                      path='scores/user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns ranking of all players by number of games won"""
        ranked_users = sorted(User.query(), 
            key=lambda x: x.performance)
        return UserRankingsForm(users=[user.to_rank_form() for user in ranked_users])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user_making_move = User.query(User.name == request.player_name).get()
        player_one = game.user.get()
        player_two = game.opponent.get()
        
        # Fetch opponent information
        if(user_making_move is player_one):
            opponent = player_two
        else:
            opponent = player_one

        # Validate the move format and make sure game is not over
        if game.game_over:
            raise endpoints.ForbiddenException(
                'Illegal Action: Game is already over.')
        if(request.move > 9 or request.move < 1):
            raise endpoints.ForbiddenException(
                'Illegal Action: Move outside the range (1-9)')

        board_ind = request.move - 1
        if(game.board_state[board_ind] == 0):
            if(user_making_move is player_one):
                game.board_state[board_ind] = 1    
                game.user_moves += 1
                game.moves_history.append("Player " + user_making_move.name + 
                    " moved to: " + str(request.move))
            else: 
                game.board_state[board_ind] = 2
                game.opponent_moves += 1
                game.moves_history.append("Player " + opponent.name + 
                    " moved to: " + str(request.move))
        else:
            raise endpoints.ForbiddenException(
                'Illegal Move: The slot is already filled.')
        
        winner = game.is_game_over()
        if winner != 0:
            if(winner == 1):
                game.end_game(True)
                return game.to_form('You win!')
            else:
                game.end_game(False)
                return game.to_form('You lose!')
        game.put()
        return game.to_form(user_making_move.name + ' made a move!')
    
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game', 
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancels a game. Returns a message indicating deletion"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                raise endpoints.ForbiddenException('Game is already over!')
            game.key.delete()  
            return StringMessage(message="Game has been successfully deleted!")
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=GET_USER_GAMES_REQUEST, 
                      response_message=UserGamesForm, 
                      path='user/games/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all active games of the user"""
        user = User.query(User.name == request.user_name).get()
        active_games = [game.to_form("Active game") for game in Game.fetch_active_games(user)]
        return UserGamesForm(games=active_games)

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            moves = ", ".join(game.moves_history)
            return StringMessage(message=moves or '')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(response_message=StringMessage,
                      path='games/average_moves',
                      name='get_average_move',
                      http_method='GET')
    def get_average_moves(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES) or '')

    @staticmethod
    def _cache_average_moves():
        """Populates memcache with the average moves of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_moves = sum([game.user_moves for game in games])
            average = float(total_moves)/count
            memcache.set(MEMCACHE_MOVES,
                         'The average moves remaining is {:.2f}'.format(average))

api = endpoints.api_server([TicTacToeApi])
