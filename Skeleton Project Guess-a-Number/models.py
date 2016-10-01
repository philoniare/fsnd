"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    games_won = ndb.IntegerProperty()
    games_lost = ndb.IntegerProperty()
    performance = ndb.FloatProperty()

    def to_rank_form(self):
        """Returns a UserRanking representation of the User"""
        form = UserRankingForm()
        form.user_name = self.name
        form.performance = self.performance
        return form

class Game(ndb.Model):
    """Game object"""
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    board_state = ndb.IntegerProperty(repeated=True)
    moves = ndb.IntegerProperty(required=True)
    moves_history = ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user, game_over=False, 
            board_state=[0 for i in range(9)], moves=0)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.board_state = self.board_state
        form.game_over = self.game_over
        form.moves = self.moves
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        # Update user scores
        user = self.user.get()
        if(won):
            user.games_won += 1
        else:
            user.games_lost += 1
        if(user.games_lost != 0):
            user.performance = float(user.games_won) / user.games_lost
        user.put()

        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won, moves=self.moves)
        score.put()

    def is_game_over(self):
        board = self.board_state
        if((board[0] == board[1] == board[2] and board[0] == 1) or
           (board[3] == board[4] == board[5] and board[3] == 1) or
           (board[6] == board[7] == board[8] and board[6] == 1)):
            # horizontal wins
            return 1
        elif((board[0] == board[3] == board[6] and board[0] == 1) or
            (board[1] == board[4] == board[7] and board[1] == 1) or 
            (board[2] == board[5] == board[8] and board[2] == 1)):
            # vertical wins
            return 1
        elif((board[0] == board[4] == board[8] and board[0] == 1) or 
            (board[2] == board[4] == board[6] and board[2] == 1)):
            # diagonal wins
            return 1
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
    moves = messages.IntegerField(5, required=True)
    user_name = messages.StringField(6, required=True)
    
class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.IntegerField(1, required=True)

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
