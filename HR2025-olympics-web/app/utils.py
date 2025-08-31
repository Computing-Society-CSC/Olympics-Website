from .models import db, Matches, Players

def rnd02infinite(previous_matches_ids, rnd, info_id, start_id):
    """
    Create matches in pairs from a list of participant IDs.

    Args:
        previous_matches_ids (list): List of match IDs from the previous round.
        rnd (int): The current round number.
        info_id (int): The ID of the match info this match belongs to.
        start_id (int): The starting match ID for this set of matches.

    Returns:
        int: The last unpaired participant ID if the number of participants is odd.
    """
    match = None

    for i, match_id in enumerate(previous_matches_ids):
        if i % 2 == 0:
            # Create a new match and set the first player
            match = Matches()
            match.last_match1_id = match_id
            match.player1_id = Matches.query.get(match_id).winner_player_id  # Set player1_id to the winner of last_match1
        else:
            # Set the second player and save the match
            match.last_match2_id = match_id
            match.player2_id = Matches.query.get(match_id).winner_player_id  # Set player2_id to the winner of last_match2
            match.match_info_id = info_id
            match.score1 = 0
            match.score2 = 0
            match.round = rnd
            db.session.add(match)
            match = None  # Reset for the next match

    db.session.commit()

    # If there's an odd number of participants, return the last player ID
    if match is not None:
        return previous_matches_ids[-1]

def create_matches_from_names(participant_names, info_id):
    """
    Create matches from a list of participant names.

    Args:
        participant_names (list): List of participant names.
        info_id (int): The ID of the match info this match belongs to.
    """
    # Fetch player IDs based on their names
    participants = []
    for name in participant_names:
        player = Players.query.filter_by(name=name).first()
        if not player:
            raise ValueError(f"Player '{name}' not found.")
        participants.append(player.id)

    # Create initial matches for round 0
    max_id = db.session.query(db.func.max(Matches.id)).scalar() or 0
    start_id = max_id + 1  # Starting match ID for this set of matches

    for player_id in participants:
        match = Matches()
        match.match_info_id = info_id
        match.winner_player_id = player_id
        match.round = 0
        db.session.add(match)

    db.session.commit()

    # Create matches for subsequent rounds
    max_id = db.session.query(db.func.max(Matches.id)).scalar()
    lst = [mx_id for mx_id in range(start_id, max_id + 1)]
    duo1 = rnd02infinite(previous_matches_ids=lst, rnd=1, info_id=info_id, start_id=start_id)
    start_id = max_id + 1
    max_id = db.session.query(db.func.max(Matches.id)).scalar()
    lst = [mx_id for mx_id in range(start_id, max_id + 1)]
    duo2 = rnd02infinite(previous_matches_ids=lst, rnd=2, info_id=info_id, start_id=start_id)

    # Handle odd number of participants
    if duo1:
        match = Matches()
        match.last_match1_id = duo2
        match.last_match2_id = duo1
        match.player1_id = Matches.query.get(duo2).winner_player_id  # Set player1_id to the winner of last_match1
        match.player2_id = Matches.query.get(duo1).winner_player_id  # Set player2_id to the winner of last_match2
        match.score1 = 0
        match.score2 = 0
        match.match_info_id = info_id
        match.round = 2
        db.session.add(match)

    db.session.commit()

    # Create the final round of matches
    create_final_round(info_id=info_id, three_matches=[max_id + 1, max_id + 2, max_id + 3])

def create_final_round(info_id, three_matches):
    """
    Create the final round of matches between the top 3 players.

    Args:
        info_id (int): The ID of the match info this match belongs to.
        three_matches (list): The three match IDs for the final round.
    """
    # Get the IDs of the last 3 matches
    match_ids = three_matches

    # Fetch the winners of the last 3 matches
    winner1 = Matches.query.get(match_ids[0]).winner_player_id
    winner2 = Matches.query.get(match_ids[1]).winner_player_id
    winner3 = Matches.query.get(match_ids[2]).winner_player_id

    # Create the final matches
    match1 = Matches()
    match1.last_match1_id = match_ids[0]
    match1.last_match2_id = match_ids[1]
    match1.player1_id = winner1  # Set player1_id to the winner of last_match1
    match1.player2_id = winner2  # Set player2_id to the winner of last_match2
    match1.score1 = 0
    match1.score2 = 0
    match1.round = 3
    match1.match_info_id = info_id
    db.session.add(match1)

    match2 = Matches()
    match2.last_match1_id = match_ids[1]
    match2.last_match2_id = match_ids[2]
    match2.player1_id = winner2  # Set player1_id to the winner of last_match1
    match2.player2_id = winner3  # Set player2_id to the winner of last_match2
    match2.score1 = 0
    match2.score2 = 0
    match2.round = 3
    match2.match_info_id = info_id
    db.session.add(match2)

    match3 = Matches()
    match3.last_match1_id = match_ids[0]
    match3.last_match2_id = match_ids[2]
    match3.player1_id = winner1  # Set player1_id to the winner of last_match1
    match3.player2_id = winner3  # Set player2_id to the winner of last_match2
    match3.score1 = 0
    match3.score2 = 0
    match3.round = 3
    match3.match_info_id = info_id
    db.session.add(match3)

    db.session.commit()