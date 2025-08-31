from sqlalchemy import select, and_
from flask_sqlalchemy import SQLAlchemy
from . import db

# Initialize SQLAlchemy instance


# Expose models for import
__all__ = ['Houses', 'Players', 'Match_info', 'Matches']


# Represents a house (team/house in the competition)
class Houses(db.Model):
    __tablename__ = "houses"

    # Primary key, a short identifier for the house
    id = db.Column(db.String(2), primary_key=True)
    # Full name of the house
    name = db.Column(db.TEXT)
    # Color associated with the house
    color = db.Column(db.TEXT)
    # Points scored by the house
    points = db.Column(db.Integer, default=0, nullable=False)

    @classmethod
    def new(cls, id_, name, color, points=0):
        # Class method to create a new house instance and add it to the database
        instance = cls()
        instance.id = id_
        instance.name = name
        instance.color = color
        instance.points = points  # Assigning the points value
        db.session.add(instance)
        return instance
    
    @staticmethod
    def create_default_houses():
        default_houses = [
            {"id": "A3", "name": "Bari", "color": "#FFD733", "points": 0},
            {"id": "A4", "name": "Ikhaya", "color": "#FFFFFF", "points": 0},
            {"id": "A5", "name": "Ruka", "color": "#14B4B7", "points": 0},
            {"id": "A6", "name": "Meraki", "color": "#0B7FCF", "points": 0},
            {"id": "B3", "name": "Baile", "color": "#0F5D10", "points": 0},
            {"id": "B4", "name": "Hogan", "color": "#7D0D0D", "points": 0},
            {"id": "B5", "name": "Heimat", "color": "#4F0606", "points": 0},
            {"id": "C3", "name": "Bandele", "color": "#620071", "points": 0},
            {"id": "C4", "name": "Bayt", "color": "#0B8FAD", "points": 0},
            {"id": "C5", "name": "Efie", "color": "#E78715", "points": 0},
            {"id": "C6", "name": "Ohana", "color": "#EF5DC7", "points": 0},
            {"id": "F0", "name": "Faculty Team", "color": "#000000", "points": 0},
        ]

        for house_data in default_houses:
            # Check if the house with this id already exists in the database.
            if not Houses.query.get(house_data["id"]):
                new_house = Houses(**house_data)
                db.session.add(new_house)
        
        # Commit all new additions
        db.session.commit()


# Represents players/participants in the competition
class Players(db.Model):
    __tablename__ = "players"

    # Primary key, unique ID for each player
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Name of the player
    name = db.Column(db.TEXT)
    # Number of medals won by the player
    medals = db.Column(db.Integer, default=0)
    # Primary house affiliation
    house_id1 = db.Column(db.String(2))
    # Optional secondary house affiliation
    house_id2 = db.Column(db.String(2), nullable=True)

    @staticmethod
    def create_default_players():
        # Retrieve all houses from the database
        houses = Houses.query.all()

        # For each house, ensure there is one player with the same name as the house.
        for house in houses:
            # Check if a player with this house as primary affiliation already exists
            existing_player = Players.query.filter_by(house_id1=house.id).first()
            if not existing_player:
                new_player = Players(
                    name=f"{house.id} {house.name}",   # Use the house name for the player's name
                    medals=0,
                    house_id1=house.id  # Set primary affiliation to this house
                )
                db.session.add(new_player)
        
        # Commit all new player additions
        db.session.commit()

    @classmethod
    def new(cls, name, medals, house_id1, house_id2=None):
        # Class method to create a new player and add them to the database
        instance = cls()
        instance.name = name
        instance.medals = medals or 0
        instance.house_id1 = house_id1
        instance.house_id2 = house_id2
        db.session.add(instance)
        return instance

    @staticmethod
    def house_from_id(id_):
        # Fetches the house instance based on the given ID
        return db.session.scalar(select(Houses).where(Houses.id == id_))

    @property
    def whole_name(self):
        # Returns the full name of the player, including their house
        if self.house_id2:
            return self.name
        return f"{self.house_id1} {self.name}"


# Represents information about a match/event
class Match_info(db.Model):
    __tablename__ = "match_info"

    # Primary key, unique ID for each match
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Name of the match/event
    name = db.Column(db.TEXT)
    # Start time of the match
    start_time = db.Column(db.TEXT)
    # End time of the match
    end_time = db.Column(db.TEXT)
    # Description of the match
    description = db.Column(db.TEXT)
    # IDs of players who placed 1st, 2nd, and 3rd
    manual_1st_player_id = db.Column(db.Integer)
    manual_2nd_player_id = db.Column(db.Integer)
    manual_3rd_player_id = db.Column(db.Integer)
    # Optional hexadecimal icon for the match
    hex_icon = db.Column(db.TEXT)
    # Status of the match (0=not started, 1=in process, 2=ended)
    status = db.Column(db.Integer, default=0)
    # Optional pair ID for matches that are linked
    pair_id = db.Column(db.Integer, nullable=True)
    # Match category ('individual' or 'team')
    category = db.Column(db.String(20))

    def __init__(self, row=None):
        # Optional initialization from a row
        if row:
            self.id = row[4]
            self.name = row[0]
            self.start_time = row[1]
            self.end_time = row[2]
            self.description = row[3]
            self.category = row[5]

    @classmethod
    def new(cls, name, start_time, end_time, description, category, hex_icon=None, status=None):
        # Class method to create a new match/event and add it to the database
        instance = cls()
        instance.name = name
        instance.start_time = start_time
        instance.end_time = end_time
        instance.description = description
        instance.category = category
        instance.hex_icon = hex_icon
        instance.status = status or 1
        db.session.add(instance)
        return instance

    @property
    def has_pair(self):
        # Checks if this match has a paired match
        return self.pair_id and self.pair_id != self.id


# Represents individual matches within an event
class Matches(db.Model):
    __tablename__ = "matches"

    # Primary key, unique ID for each match instance
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Foreign key linking to the match information
    match_info_id = db.Column(db.Integer, db.ForeignKey('match_info.id'))
    # Relationship with Match_info
    rel_match_info = db.relationship('Match_info', backref=db.backref('matches', lazy=True))

    player1_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    player1 = db.relationship('Players', foreign_keys=[player1_id], backref=db.backref('matches_as_player1', lazy=True))
    player2_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    player2 = db.relationship('Players', foreign_keys=[player2_id], backref=db.backref('matches_as_player2', lazy=True))
    winner_player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    winner_player = db.relationship('Players', foreign_keys=[winner_player_id], backref=db.backref('matches_won', lazy=True))

    # IDs of previous matches in the bracket
    last_match1_id = db.Column(db.Integer, db.ForeignKey('matches.id'))
    score1 = db.Column(db.Integer, default=0, nullable=True)
    last_match2_id = db.Column(db.Integer, db.ForeignKey('matches.id'))
    score2 = db.Column(db.Integer, default=0, nullable=True)
    # The round number of the match
    round = db.Column(db.Integer, default=0)

    def __init__(self, row=None):
        # Optional initialization from a row
        if row:
            self.match_info_id = row[0]
            if row[1]:
                self.winner_player_id = row[1]
            self.last_match1_id = row[2]
            self.last_match2_id = row[3]
            self.id = row[4]

        # Determine the round of this match based on previous matches
        try:
            last_match_round = max(
                db.session.get(self.last_match1_id).round,
                db.session.get(self.last_match2_id).round
            )
            self.round = last_match_round + 1
        except:
            self.round = 0