"""models.py - contains the class definitions for the Datastore
entities used by the Tic Tac Toe."""

from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    games_won = ndb.IntegerProperty(default=0)
    games_lost = ndb.IntegerProperty(default=0)
    performance = ndb.FloatProperty(default=0.0)

    def to_rank_form(self):
        """Returns a UserRanking representation of the User"""
        form = UserRankingForm()
        form.user_name = self.name
        form.performance = self.performance
        return form

    @classmethod
    def fetch_users_with_active_games(cls):
        users, users_with_active_games = User.query(), []
        for user in users:
            # User can be both user and opponent in a game
            user_active_games = Game.query(ndb.OR(Game.user == user.key, Game.opponent == user.key))
            # Filter only games that are active
            user_game_count = user_active_games.filter(Game.game_over == False).count()
            if user_game_count != 0:
                users_with_active_games.append(user)
        return users_with_active_games


class Game(ndb.Model):
    """Game object"""
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    opponent = ndb.KeyProperty(required=True, kind='User')
    board_state = ndb.IntegerProperty(repeated=True)
    user_moves = ndb.IntegerProperty(required=True, default=0)
    opponent_moves = ndb.IntegerProperty(required=True, default=0)
    moves_history = ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user, opponent):
        """Creates and returns a new game"""
        game = Game(user=user, opponent=opponent, board_state=[0 for i in range(9)])
        game.put()
        return game

    @classmethod
    def fetch_active_games(cls, user):
        return Game.query(Game.user == user.key, Game.game_over == False)

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.opponent_name = self.opponent.get().name
        form.board_state = self.board_state
        form.game_over = self.game_over
        form.user_moves = self.user_moves
        form.opponent_moves = self.opponent_moves
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the user won. - if won is False,
        the player lost and the opponent won the game."""
        self.game_over = True
        self.put()

        # Update scores of both players
        user = self.user.get()
        opponent = self.opponent.get()
        if(won):
            user.games_won += 1
            opponent.games_lost += 1
        else:
            user.games_lost += 1
            opponent.games_won += 1
        if(user.games_lost != 0):
            user.performance = float(user.games_won) / user.games_lost
        if(opponent.games_lost != 0):
            opponent.performance = float(opponent.games_won) / opponent.games_lost
        user.put()
        opponent.put()

        # Add the game results to the score 'board'
        score_user = Score(user=self.user, date=date.today(), 
            won=won, moves=self.user_moves)
        score_user.put()
        score_opponent = Score(user=self.user, date=date.today(), 
            won=not(won), moves=self.opponent_moves)
        score_opponent.put()

    def is_game_over(self):
        board, player_one, player_two = self.board_state, 1, 2
        x_states, o_states = set(), set()
        possible_wins = [
            {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, # horizontal win
            {0, 3, 6}, {1, 4, 7}, {2, 5, 8}, # vertical win
            {0, 4, 8}, {6, 4, 2}             # diagonal win
        ]
        for i in range(len(board)):
            if(board[i] == player_one):
                x_states.add(i)
            elif(board[i] == player_two):
                o_states.add(i)
        for win in possible_wins:
            if(len(win.intersection(x_states)) == 3):
                return 1    # Player one won
            elif(len(win.intersection(o_states)) == 3):
                return 2    # Player two won
        return 0


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    moves = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), moves=self.moves)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    board_state = messages.IntegerField(2, repeated=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_moves = messages.IntegerField(5, required=True)
    opponent_moves = messages.IntegerField(6, required=True)
    user_name = messages.StringField(7, required=True)
    opponent_name = messages.StringField(8, required=True)
    
class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    opponent_name = messages.StringField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.IntegerField(1, required=True)
    player_name = messages.StringField(2, required=True)

class GetHighScoresForm(messages.Message):
    number_of_results = messages.IntegerField(1)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    moves = messages.IntegerField(4, required=True)

class UserRankingForm(messages.Message):
    """UserRanking for outbound Rank information"""
    user_name = messages.StringField(1, required=True)
    performance = messages.FloatField(2, required=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserRankingsForm(messages.Message):
    """Return multiple UserRankings"""
    users = messages.MessageField(UserRankingForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class UserGamesForm(messages.Message):
    """Return all of the active games of the user"""
    games = messages.MessageField(GameForm, 1, repeated=True)