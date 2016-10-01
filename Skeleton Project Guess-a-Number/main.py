#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import User


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        games = Game.query(Game.user == user.key)
        users_with_active_games = []
        for game in games:
            if not(game.game_over):
                users_with_active_games.append(game.user.key)
        for user_key in users_with_active_games:
            user = user_key.get()
            subject = 'This is a reminder that you have an active game!'
            body = 'Hello {}, go become a champion in Tic Tac Toe!'.format(user.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateAverageMoves(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        TicTacToeApi._cache_average_moves()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_moves', UpdateAverageMoves),
], debug=True)
