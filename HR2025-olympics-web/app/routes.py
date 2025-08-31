# -*- encoding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, request, flash, url_for, jsonify
from .models import Match_info, Players, Matches, Houses, db
from sqlalchemy import select, and_
from datetime import datetime
from .forms import MatchScoreForm, MatchWinnerForm, MatchInitializationForm, EditPlayerForm, AddPlayerForm, CreateMatchesForm, UpdateHousePointsForm
from .config import SECRET_KEY
from .utils import *

bp = Blueprint('main', __name__)

@bp.route('/home')
@bp.route('/')
def home():
    # Retrieve matches from the database
    matches = Match_info.query.order_by(Match_info.status.desc()).all()
    print(f"DEBUG: Retrieved {len(matches)} matches from database.")
    
    # Debug print each match's hex_icon for clarity
    for match in matches:
        icon = match.hex_icon if match.hex_icon is not None else 'None'
        print(f"DEBUG: Match ID {match.id} has hex_icon '{icon}'")

    context = {
        'matches': matches,
        'route': 'home',
        'is_authenticated': False,  
    }
    return render_template('all_matches.html', **context)

@bp.route('/<key>/management/matches/all/', methods=['GET', 'POST'])
def management_matches_all(key):
    if key != SECRET_KEY:
        return redirect('/home')

    # Fetch all matches ordered by status
    matches = Match_info.query.order_by(Match_info.status.desc()).all()

    # Initialize the form
    form = MatchInitializationForm()

    # Handle form submission for adding a new match
    if request.method == 'POST':
        try:
            # Create a new match from the form data
            new_match = Match_info.new(
                name=request.form['name'],
                start_time=request.form['start_time'],
                end_time=request.form['end_time'],
                status=int(request.form['status']),
                description=request.form['description'],
                category=request.form['category']
            )

            # Add the new match to the database
            db.session.add(new_match)
            db.session.commit()

            # Redirect to the same page after successful form submission
            return redirect(url_for('main.management_matches_all', key=key))
        except Exception as e:
            print(f"Error: {e}")  # Log the error
            return f"Error: {e}"

    # Prepare matches summary with winner's name
    matches_summary = []
    for match in matches:
        # Fetch the winner's name using manual_1st_player_id
        winner_name = None
        if match.manual_1st_player_id:
            winner = Players.query.get(match.manual_1st_player_id)
            if winner:
                winner_name = winner.name

        matches_summary.append({
            'id': match.id,
            'name': match.name,
            'status': match.status,
            'start_time': match.start_time,
            'end_time': match.end_time,
            'winner': winner_name,  # Use the winner's name instead of ID
        })

    # Prepare context for the template
    context = {
        'matches': matches_summary,
        'route': 'management_matches_all',
        'is_authenticated': True,
        'form': form,
        'key': SECRET_KEY,
    }

    return render_template('management_matches.html', **context)

@bp.route('/<key>/management/matches/edit/<int:match_id>/', methods=['GET', 'POST'])
def edit_match(key, match_id):
    if key != SECRET_KEY:
        return redirect('/home')

    # Get the match info
    match_info = Match_info.query.get(match_id)
    if not match_info:
        return render_template('404.html'), 404

    # Pre-fill the form with existing match data
    form = MatchInitializationForm(
        name=match_info.name,
        start_time=match_info.start_time,
        end_time=match_info.end_time,
        status=match_info.status,
        category=match_info.category,
        description=match_info.description
    )

    # Check if the DELETE button was clicked
    if request.method == 'POST' and 'delete' in request.form:
        try:
            # Delete the match from the database
            db.session.delete(match_info)
            db.session.commit()

            # Redirect to the management matches page after deletion
            return redirect(url_for('main.management_matches_all', key=key))
        except Exception as e:
            print(f"Error deleting match: {e}")
            return "Error deleting match", 500

    # If the form is submitted and not deleted, update the match info
    if form.validate_on_submit():
        match_info.name = form.name.data
        match_info.start_time = form.start_time.data
        match_info.end_time = form.end_time.data
        match_info.status = form.status.data
        match_info.category = form.category.data
        match_info.description = form.description.data

        db.session.commit()

        # Redirect back to the management matches page
        return redirect(url_for('main.management_matches_all', key=key))

    context = {
        'form': form,
        'match_info': match_info,
        'route': 'edit_match',
        'key': SECRET_KEY
    }

    return render_template('edit_match.html', **context)

@bp.route('/<int:match_id>/')
def match_view(match_id):
    match_info = Match_info.query.get(match_id)
    if not match_info:
        return render_template('404.html'), 404  

    manual_3places = [
        Players.query.get(match_info.manual_1st_player_id),
        Players.query.get(match_info.manual_2nd_player_id),
        Players.query.get(match_info.manual_3rd_player_id)
    ]

    round_matches_list = []
    round_number = 1
    while round_matches := Matches.query.filter_by(round=round_number, match_info_id=match_id).all():
        # Check if this is a football match and it's Round 1
        if "Football" in match_info.name and round_number == 1:
            # Combine matches in pairs for Round 1
            combined_matches = []
            for i in range(0, len(round_matches), 2):
                if i + 1 < len(round_matches):
                    match1 = round_matches[i]
                    match2 = round_matches[i + 1]
                    combined_match = {
                        'team1': [match1.player1, match2.player1],  # A3 & A4
                        'team2': [match1.player2, match2.player2],  # A5 & A6
                        'score1': match1.score1,    # Combined scores
                        'score2': match1.score2,
                        'winner_player_id': match1.winner_player_id or match2.winner_player_id  # Winner logic
                    }
                    combined_matches.append(combined_match)
            round_matches_list.append(combined_matches)
        else:
            # For non-football matches or other rounds, proceed as usual
            round_matches_list.append(round_matches)
        round_number += 1

    context = {
        'match_info': match_info,
        'manual_3places': manual_3places,
        'round_matches_list': round_matches_list,
        'route': 'match_view',
        'is_football': "Football" in match_info.name,  # Add a flag to indicate if it's a football match
    }

    # Render the football-specific template if it's a football match
    if "Football" in match_info.name:
        return render_template('football_match_view.html', **context)
    else:
        return render_template('match_view.html', **context)

@bp.route('/<key>/management/upload/ini/', methods=['GET', 'POST'])
def management_upload_ini(key):
    if key != SECRET_KEY:
        return redirect('/home')

    form = MatchInitializationForm()
    if form.validate_on_submit():
        new_match = Match_info(
            name=form.name.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            status=form.status.data
        )
        db.session.add(new_match)
        db.session.commit()
        flash("Match initialized successfully!", "success")
        return redirect(f'/{key}/management/matches/all/')

    flash("Failed to initialize match. Check input fields.", "error")
    return redirect(f'/{key}/management/matches/all/')

@bp.route('/<key>/management/<int:match_id>/', methods=['GET', 'POST'])
def management_match_view(key, match_id):
    if key != SECRET_KEY:
        return redirect('/home')  

    # Fetch the match info by match_id
    match_info = Match_info.query.get(match_id)
    if not match_info:
        return render_template('404.html'), 404  

    # Handle form submission for updating manual rankings
    if request.method == 'POST':
        if 'manual_1st_player_id' in request.form:
            match_info.manual_1st_player_id = request.form['manual_1st_player_id']
            match_info.manual_2nd_player_id = request.form['manual_2nd_player_id']
            match_info.manual_3rd_player_id = request.form['manual_3rd_player_id']
        if 'status' in request.form:
            match_info.status = request.form['status']

        db.session.commit()

    # Fetch the top 3 players (manual rankings)
    manual_3places = [
        Players.query.get(match_info.manual_1st_player_id),
        Players.query.get(match_info.manual_2nd_player_id),
        Players.query.get(match_info.manual_3rd_player_id)
    ]

    # Fetch all matches for this match_info_id, grouped by round
    round_matches_list = []
    round_number = 1
    while round_matches := Matches.query.filter_by(round=round_number, match_info_id=match_id).all():
        round_matches_list.append(round_matches)
        round_number += 1

    # Prepare match details for the template
    match_details = []
    for round_matches in round_matches_list:
        round_details = []
        for match in round_matches:
            # Fetch player names and winner
            player1 = Players.query.get(match.player1_id)
            player2 = Players.query.get(match.player2_id)
            winner = Players.query.get(match.winner_player_id)

            round_details.append({
                'match_id': match.id,
                'player1': player1.name if player1 else 'TBD',
                'player2': player2.name if player2 else 'TBD',
                'score1': match.score1,
                'score2': match.score2,
                'winner': winner.name if winner else 'TBD',
            })
        match_details.append(round_details)

    # Prepare context for the template
    context = {
        'key': SECRET_KEY,
        'match_info': match_info,
        'manual_3places': manual_3places,
        'match_details': match_details,  # Pass match details to the template
        'route': 'management_match_view',
        'is_authenticated': True,
    }

    return render_template('management_match_view.html', **context)

@bp.route('/about/')
def about():
    context = {
        'route': 'about',  
    }
    return render_template('about.html', **context)

@bp.route('/timetable/')
def timetable():
    matches = Match_info.query.order_by(Match_info.start_time).all()

    timetable_data = {}
    for match in matches:
        date = match.start_time.split(" ")[0]  
        if date not in timetable_data:
            timetable_data[date] = []
        timetable_data[date].append(match)

    context = {
        'route': 'timetable',
        'timetable_data': timetable_data,
    }

    return render_template('timetable.html', **context)

@bp.route('/houses_status/')
def houses_status():
    # Fetch all houses and sort them by points in descending order
    houses = Houses.query.order_by(Houses.points.desc()).all()

    # Prepare data for the template
    house_rankings = []
    color_map = {}

    for index, house in enumerate(houses):
        house_rankings.append({
            'rank': index + 1,
            'name': house.name,
            'points': house.points,
        })
        color_map[house.name] = house.color  # Store house colors for styling

    return render_template('houses_status.html', house_rankings=house_rankings, color_map=color_map)

@bp.route('/<key>/management/players/', methods=['GET', 'POST'])
def manage_players(key):
    if key != SECRET_KEY:
        return redirect('/home')

    # Fetch all players from the database and sort by name
    players = Players.query.order_by(Players.name.asc()).all()

    # Initialize the form for adding new players
    form = AddPlayerForm()

    if form.validate_on_submit():
        # Create a new player and add to the database
        new_player = Players.new(
            name=form.name.data,
            medals=form.medals.data,
            house_id1=form.house1.data,
            house_id2=form.house2.data
        )
        db.session.commit()
        flash('Player added successfully!', 'success')
        return redirect(url_for('main.manage_players', key=key))

    # Handle player deletion
    if request.method == 'POST' and 'delete_player' in request.form:
        player_id = request.form['delete_player']
        player = Players.query.get(player_id)
        if player:
            db.session.delete(player)
            db.session.commit()
            flash('Player deleted successfully!', 'success')
        return redirect(url_for('main.manage_players', key=key))

    return render_template('manage_players.html', players=players, form=form, key=key)

@bp.route('/<key>/management/players/edit/<int:player_id>/', methods=['GET', 'POST'])
def edit_player(key, player_id):
    if key != SECRET_KEY:
        return redirect('/home')

    player = Players.query.get_or_404(player_id)
    form = EditPlayerForm(obj=player)  # Pre-fill form with existing data

    if form.validate_on_submit():
        player.name = form.name.data
        player.medals = form.medals.data
        player.house_id1 = form.house1.data  
        player.house_id2 = form.house2.data  

        db.session.commit()
        flash('Player details updated successfully!', 'success')
        return redirect(f'/{key}/management/players/')  # Redirect to player list

    return render_template('edit_player.html', form=form, player=player, key=key)

@bp.route('/<key>/management/matches/all/<int:match_id>/', methods=['GET'])
def management_view_game_matches(key, match_id):
    if key != SECRET_KEY:
        return redirect('/home')

    # Fetch all matches related to this specific game
    game_matches = Matches.query.filter_by(match_info_id=match_id).all()

    if not game_matches:
        return "No matches found for this game.", 404

    # Prepare match data for display
    match_list = []
    for match in game_matches:
        if match.round != 0:
            match_list.append({
                "round_number": match.round, 
                "match_id": match_id,  # Game ID
                "match_uni_id": match.id,  # Unique match ID for score upload link
                "player1_name": match.player1.name if match.player1 else "No Player 1",
                "player2_name": match.player2.name if match.player2 else "No Player 2",
                "score1": match.score1 if match.score1 is not None else "-",
                "score2": match.score2 if match.score2 is not None else "-",
                "winner_name": match.winner_player.name if match.winner_player else "Not decided",
            })

    return render_template('management_view_game_matches.html', key=key, matches=match_list)

@bp.route('/<key>/management/matches/all/<int:match_id>/win/', methods=['GET', 'POST'])
def management_save_winner(key, match_id):
    if key != SECRET_KEY:
        return redirect('/home')

    # Fetch the match by match_id
    match = Match_info.query.get(match_id)
    if not match:
        return "Match not found", 404

    form = MatchWinnerForm()

    if form.validate_on_submit():
        # Fetch players based on names entered
        first_place = Players.query.filter_by(name=form.first_place.data).first()
        second_place = Players.query.filter_by(name=form.second_place.data).first()
        third_place = Players.query.filter_by(name=form.third_place.data).first()

        if first_place and second_place and third_place:
            # Update match winners
            match.manual_1st_player_id = first_place.id
            match.manual_2nd_player_id = second_place.id
            match.manual_3rd_player_id = third_place.id
            db.session.commit()
            # Determine the event type and assign points
            event_type = match.category  # Assuming 'category' field exists in Match_info
            if event_type == 'Individual':
                points = {'1st': 25, '2nd': 20, '3rd': 15}
            elif event_type == 'Team':
                points = {'1st': 50, '2nd': 45, '3rd': 40}
            elif event_type == 'House':
                points = {'1st': 75, '2nd': 65, '3rd': 55}
            else:
                flash("Invalid event type.", "error")
                return redirect(f'/{key}/management/matches/all/{match_id}/win/')

            # Function to calculate points with exception for B3 Baile and C5 Efie
            def calculate_points(player, position):
                house = player.house_id1  # Assuming house_id1 is the house of the player
                base_points = points[position]
                if house in ['B3', 'C5']:
                    return int(base_points * 1.0)
                return base_points

            # Fetch houses for winners
            first_place_house = Houses.query.filter_by(id=first_place.house_id1).first()
            second_place_house = Houses.query.filter_by(id=second_place.house_id1).first()
            third_place_house = Houses.query.filter_by(id=third_place.house_id1).first()

            # Update house points for winners
            if first_place_house:
                first_place_house.points += calculate_points(first_place, '1st')
            if second_place_house:
                second_place_house.points += calculate_points(second_place, '2nd')
            if third_place_house:
                third_place_house.points += calculate_points(third_place, '3rd')

            # Commit changes to the database
            db.session.commit()
            flash("Winners and house points updated successfully!", "success")
            return redirect(f'/{key}/management/matches/all/{match_id}/')
        else:
            flash("One or more players not found. Please check the names.", "error")

    return render_template('management_commit_winner.html', form=form, match=match, key=SECRET_KEY)

# ✅ API route for player name autocomplete
@bp.route('/autocomplete/players', methods=['GET'])
def autocomplete_players():
    query = request.args.get('q', '').strip()
    players = Players.query.filter(Players.name.ilike(f"%{query}%")).limit(5).all()
    return jsonify([player.name for player in players])

@bp.route('/<key>/management/matches/create/<int:match_info_id>/', methods=['GET', 'POST'])
def create_matches(key, match_info_id):
    if key != SECRET_KEY:
        return redirect('/home')

    form = CreateMatchesForm()

    if form.validate_on_submit():
        # Split the input into a list of participant names
        participant_names = [name.strip() for name in form.participant_names.data.split(',')]

        try:
            # Delete existing matches for this match_info_id
            Matches.query.filter_by(match_info_id=match_info_id).delete()
            db.session.commit()

            # Create matches from participant names
            create_matches_from_names(participant_names, info_id=match_info_id)
            flash("Matches created successfully!", "success")
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(url_for('main.create_matches', key=SECRET_KEY, match_info_id=match_info_id))

    return render_template('create_matches.html', form=form, key=key)

@bp.route('/<key>/management/')
def management_homepage(key):
    if key != SECRET_KEY:
        return redirect("/home")
    return render_template('management_home.html', key=key)

@bp.route("/<key>/management/house_rankings/", methods=["GET", "POST"])
def house_rankings(key):
    if key != SECRET_KEY:
        return redirect("/home")

    houses = Houses.query.order_by(Houses.points.desc()).all()

    # Dictionary to store a form instance for each house
    forms = {house.id: UpdateHousePointsForm(obj=house) for house in houses}

    if request.method == "POST":
        house_id = request.form.get("house_id")
        form = forms.get(house_id)

        if form and form.validate_on_submit():
            house = Houses.query.get(house_id)
            if house:
                house.points = form.points.data
                db.session.commit()
                flash(f"Updated points for {house.name}!", "success")
            else:
                flash("House not found!", "danger")

        return redirect(url_for("main.house_rankings", key=key))

    return render_template("management_house_rankings.html", key=key, houses=houses, forms=forms)

@bp.route('/<key>/management/matches/all/<int:match_info_id>/<int:match_id>/', methods=['GET', 'POST'])
def management_upload_scores(key, match_info_id, match_id):
    if key != SECRET_KEY:
        return redirect('/home')

    # Fetch the specific match by match_id
    current_match = Matches.query.get(match_id)
    if not current_match:
        return "Match not found", 404

    # Initialize the form with the current match
    form = MatchScoreForm(match=current_match)

    if form.validate_on_submit():
        try:
            # Update match scores and winner
            current_match.score1 = form.score1.data
            current_match.score2 = form.score2.data
            current_match.winner_player_id = form.winner.data

            # Propagate the winner to the next round (for Rounds 1 and 2)
            if current_match.round in [1, 2]:
                next_round = current_match.round + 1
                next_matches = Matches.query.filter(
                    (Matches.last_match1_id == match_id) | (Matches.last_match2_id == match_id),
                    Matches.round == next_round,
                    Matches.match_info_id == match_info_id
                )

                # if next_matches:
                for next_match in next_matches:
                    if next_match.last_match1_id == match_id:
                        next_match.player1_id = current_match.winner_player_id
                    elif next_match.last_match2_id == match_id:
                        next_match.player2_id = current_match.winner_player_id

            # Commit changes to the database
            db.session.commit()
            flash("Scores updated successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(f'/{key}/management/matches/all/{match_info_id}/')

    # Pre-fill the form with existing match data
    if current_match:
        form.score1.data = current_match.score1
        form.score2.data = current_match.score2
        form.winner.data = current_match.winner_player_id

    # Render the form with the current match details
    context = {
        'form': form,
        'match': current_match,
        'route': 'management_upload_scores',
        'key': SECRET_KEY,
        'is_authenticated': True,
    }
    return render_template('management_upload_scores.html', **context)