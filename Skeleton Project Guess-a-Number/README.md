#Full Stack Nanodegree Project Tic Tac Toe

## Instructions for playing the game:
- Install GAE for Python if it is not installed
- Navigate to the project folder and start the app by running `dev_appserver .`
- Open up `localhost:8080/_ah/api/explorer` to explore the endpoints
- Create a new user, new game and start making moves
 
##Game Description:
Tic Tac Toe is a simple game with played on a 3x3 board. Each game begins with an
empty 3x3 and players take turns to place either 'x' or 'o' on each of the 9 fields.
The player who manages to place their signs either diagonally, horizontally or 
vertically wins the game. 'Moves' are sent to the `make_move` endpoint which will reply
with either: `board_state`, 'draw', 'you win', or 'you lose' (if the other player
manages to fulfill the winning conditions). 
Many different Tic Tac Toe games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_user_games**
    - Path: 'user/games/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: UserGamesForm.
    - Description: Returns the urlsafe_game_key of all active games of the user. 
    
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage.
    - Description: Cancels the given with the provided urlsafe_game_key. 

 - **get_high_scores**
    - Path: 'scores/high_scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns sorted list of high scores.

 - **get_user_rankings**
    - Path: 'scores/user_rankings'
    - Method: GET
    - Parameters: None
    - Returns: UserRankingsForm.
    - Description: Returns the rankings of all users based on performance score (win/ loss ratio).

- **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage.
    - Description: Returns a list of moves from the game.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.