# 表单可以参照之前的

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, DataRequired, ValidationError
from .models import Match_info, Players, Houses

class MatchInitializationForm(FlaskForm):
    name = StringField('Match Name', validators=[DataRequired()])
    start_time = StringField('Start Time', validators=[DataRequired()])
    end_time = StringField('End Time', validators=[DataRequired()])
    status = SelectField('Status', choices=[(0, 'Scheduled'), (1, 'In Progress'), (2, 'Completed')], validators=[DataRequired()])
    category = SelectField('Category', choices=[('Individual', 'Individual'), ('Team', 'Team'), ('House', 'House')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Initialize Match')


class MatchScoreForm(FlaskForm):
    score1 = IntegerField('Score 1', validators=[InputRequired(), NumberRange(min=0)])
    score2 = IntegerField('Score 2', validators=[InputRequired(), NumberRange(min=0)])
    winner = SelectField('Winner', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Scores')

    def __init__(self, match=None, *args, **kwargs):
        super(MatchScoreForm, self).__init__(*args, **kwargs)
        if match:
            # Ensure that match has valid player IDs before setting choices
            self.winner.choices = []
            if match.player1_id:
                player1 = Players.query.get(match.player1_id)
                if player1:
                    self.winner.choices.append((player1.id, player1.name))
            if match.player2_id:
                player2 = Players.query.get(match.player2_id)
                if player2:
                    self.winner.choices.append((player2.id, player2.name))
            # Debug: Print the winner choices
            print(f"Winner choices: {self.winner.choices}")


class MatchWinnerForm(FlaskForm):
    first_place = StringField('First Place (Winner)', validators=[DataRequired()])
    second_place = StringField('Second Place', validators=[DataRequired()])
    third_place = StringField('Third Place', validators=[DataRequired()])
    submit = SubmitField('Save Rankings')

class AddPlayerForm(FlaskForm):
    name = StringField('Player Name', validators=[InputRequired()])  # Use InputRequired
    medals = IntegerField('Number of Medals', validators=[InputRequired()])  # Use InputRequired
    house1 = SelectField('Primary House', coerce=str, validators=[InputRequired()])  # Use InputRequired
    house2 = SelectField('Secondary House (Optional)', coerce=str)
    submit = SubmitField('Add Player')

    def __init__(self, *args, **kwargs):
        super(AddPlayerForm, self).__init__(*args, **kwargs)
        self.house1.choices = [(h.id, h.name) for h in Houses.query.all()]
        self.house2.choices = [(0, 'None')] + [(h.id, h.name) for h in Houses.query.all()]


class EditPlayerForm(FlaskForm):
    name = StringField('Player Name', validators=[InputRequired()])  # Use InputRequired
    medals = IntegerField('Number of Medals', validators=[InputRequired()])  # Use InputRequired
    house1 = SelectField('Primary House', coerce=str, validators=[InputRequired()])  # Use InputRequired
    house2 = SelectField('Secondary House (Optional)', coerce=str)
    submit = SubmitField('Update Player')

    def __init__(self, *args, **kwargs):
        super(EditPlayerForm, self).__init__(*args, **kwargs)
        self.house1.choices = [(h.id, h.name) for h in Houses.query.all()]
        self.house2.choices = [(0, 'None')] + [(h.id, h.name) for h in Houses.query.all()]


class CreateMatchesForm(FlaskForm):
    participant_names = StringField('Participant Names (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Create Matches')


class UpdateHousePointsForm(FlaskForm):
    points = IntegerField("Points", validators=[InputRequired(), NumberRange(min=0)], default=0)
    submit = SubmitField("Update Points")
