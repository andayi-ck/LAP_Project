from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateTimeField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo


from datetime import datetime
from flask_mail import Mail, Message as MailMessage

from market import db, login_manager, bcrypt


from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'Item {self.name}'
    
    def buy(self, user):
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()
        
    def sell(self, user):
        self.owner = None
        user.budget += self.price
        db.session.commit()

    def can_sell(self, item_obj):
        return item_obj in self.items

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=1000)
    items = db.relationship('Item', backref='owned_user', lazy=True)
    email_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='normal_user')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    
    def get_id(self):
        
    
        return str(self.id)
    
    
    @property
    def prettier_budget(self):
        if len(str(self.budget)) >= 4:
            return f'{str(self.budget)[:-3]},{str(self.budget)[-3:]}$'
        else:
            return f"{self.budget}$"

    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self, plain_text_password):
        #self.password_hash = plain_text_password
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
        
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def can_purchase(self, item_obj):
        return self.budget >= item_obj.price
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)

class Illness(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.String(500), nullable=False)  # Comma-separated list of symptoms
    required_specialist = db.Column(db.String(100), nullable=False)  # Matches Veterinary.specialty

    def __repr__(self):
        return f"Illness('{self.name}', '{self.required_specialist}')"
    
# Forms (assumed based on usage)
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=30)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=50)])
    password1 = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Register')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=30)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    
class ChatForm(FlaskForm):
    receiver_id = SelectField('Send To', coerce=int, validators=[DataRequired()])
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send')
    
class TipForm(FlaskForm):
    content = TextAreaField('Tip', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Post Tip')


class CampaignForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    date = DateTimeField('Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    organizer = StringField('Organizer', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Post Campaign')

    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='notifications')
    category = db.Column(db.String(50), nullable=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref='tips')



class GeneralInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, nullable=True)  # e.g., health, feeding, medication, care
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vet_id = db.Column(db.Integer, nullable=False)  # Not linked to a Vet model since vet data is static in HTML
    vet_name = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    animal_type = db.Column(db.String(50), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_email = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
class Vet(db.Model):
    __tablename__ = 'vet'  # Explicitly specify the table name
    vet_id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    clinic = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.String(100), nullable=False)
    accepting = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.String(50), nullable=False)
    rating_score = db.Column(db.Float, nullable=False, default=0.0)  # New field for numeric rating
    review_count = db.Column(db.Integer, nullable=False, default=0)  # New field for review count
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    animal_types = db.Column(db.String(255))
    diseases = db.Column(db.String(255))
    reviews = db.Column(db.String(500), nullable=True)  # New field for reviews
    
    
    def __repr__(self):
        return f'<Vet {self.name}>'

class SymptomCheckerDisease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Disease name (e.g., "Foot-and-Mouth Disease")
    animal_type = db.Column(db.String(50), nullable=False)  # Animal type (e.g., "Cattle", "Poultry")
    symptoms = db.Column(db.String(500), nullable=False)  # Symptoms as a comma-separated string (e.g., "fever,blisters on mouth,lameness")
    action_to_take = db.Column(db.Text)
    
    
    def __repr__(self):
        return f'<SymptomCheckerDisease {self.name} for {self.animal_type}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM-DD
    time = db.Column(db.String(10), nullable=False)  # Format: HH:MM
    duration = db.Column(db.Integer, nullable=False)  # Duration in hours
    image_url = db.Column(db.String(200), nullable=True)  # Optional image URL
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


    def __repr__(self):
        return f'<Event {self.title}>'






