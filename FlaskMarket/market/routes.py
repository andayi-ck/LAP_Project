import os
import smtplib
import ssl
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import check_password_hash, generate_password_hash
from market.forms import VetForm, RegisterForm, LoginForm, ChatForm, CampaignForm, TipForm, GeneralInfoForm
from flask_mail import Message as MailMessage



from uuid import uuid4
import sqlite3
from datetime import datetime
from sqlalchemy.sql import func
from email.message import EmailMessage

from flask_mail import Message, Mail

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from flask import request, Blueprint, flash, get_flashed_messages, jsonify, redirect, render_template, request, url_for, session
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from market import app, bcrypt, db, login_manager
from market.forms import CreateEventForm, LoginForm, PurchaseItemForm, RegisterForm
from market.models import Animalia, Specificia, Habitatty, AnimalsFeed, VaccinationTimetable, DiseasesInfection, ExpectedFeedIntake, ExpectedProduce, Event, SymptomCheckerDisease, Illness, Item, User, Campaign, Notification, Tip, Message, Vet, GeneralInfo, Appointment
import logging

from apscheduler.schedulers.background import BackgroundScheduler



# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

mail = Mail(app)

@app.route('/')
def welcome_page():
    return render_template('welcome-page.html')


@app.route('/home')
def home_page():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    else:
        unread_count = 0
    return render_template('home.html', unread_count=unread_count)
    #  we went on to call the home.html file as can be seen above.
    # 'render_template()' basically works by rendering files.

#@login_required
#below list of dictionaries is sent to the market page through the market.html
#       but we are going to look for a way to store information inside an organized
#       DATABASE which can be achieved through configuring a few things in our flask
#       application
# WE ARE THUS GOING TO USE SQLITE3 is a File WHich allows us to store information and we are going to
#   connect it to the Flask APplication.We thus have to install some flask TOOL THAT ENABLES THIS through the terminal


# Email configuration
email_sender = 'magero833@gmail.com'
EMAIL_PASSWORD = "dbvw amge uzvr secp"  # App-specific password for Gmail

# Token generator for email verification
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])



# VetConnect Alerts
def send_vetconnect_alert(recipient_email, subject, body):
    from market import mail
    msg = MailMessage(subject=subject, recipients=[recipient_email], body=body)
    try:
        mail.send(msg)
        print(f"Sent alert to {recipient_email}: {subject}")
    except Exception as e:
        print(f"Failed to send alert to {recipient_email}: {e}")



def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification')

def verify_verification_token(token, expiration=3600):  # 1 hour expiration
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification', max_age=expiration)
        return email
    except SignatureExpired:
        return None  # Token expired
    except BadSignature:
        return None  # Invalid token


#E-mail Verification on Account Creation
def send_verification_email(email_receiver, username, token):
    verification_url = url_for('verify_email', token=token, _external=True)
    subject = 'Verify Your Email to Create Your Account'
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding: 20px 0;
                background-color: #D2B48C;
                color: white;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px;
                color: #333;
            }}
            .content p {{
                line-height: 1.6;
                margin: 10px 0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 25px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            .footer {{
                text-align: center;
                padding: 10px;
                font-size: 12px;
                color: #777;
            }}
            .link {{
                word-break: break-all;
                color: #4CAF50;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://livestockanalytics.com/hs-fs/hubfs/Logos%20e%20%C3%ADconos/livestock.png?width=115&height=70&name=livestock.png" alt="Livestock Management" style="max-width: 150px;">
                <h1>Welcome to Livestock Management</h1>
            </div>
            <div class="content">
                <p>Hello {username},</p>
                <p>Thank you for joining the Livestock Management System! To complete your account creation, please verify your email by clicking the button below:</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">Create Account</a>
                </p>
                <p>If the button doesn’t work, copy and paste this link into your browser:</p>
                <p><a href="{verification_url}" class="link">{verification_url}</a></p>
                <p>This link expires in 1 hour.</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Livestock Management System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body, subtype='html')  # Ensure HTML subtype is set

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, EMAIL_PASSWORD)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        print(f"Verification email sent to {email_receiver}")
    except Exception as e:
        print(f"Email error: {str(e)}")


# Email sending function for appointment confirmation
def send_appointment_email(email_receiver, vet_name, appointment_date, appointment_time, animal_type, owner_name):
    subject = 'Appointment Confirmation - Livestock Management System'
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding: 20px 0;
                background-color: #D2B48C;
                color: white;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px;
                color: #333;
            }}
            .content p {{
                line-height: 1.6;
                margin: 10px 0;
            }}
            .footer {{
                text-align: center;
                padding: 10px;
                font-size: 12px;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://livestockanalytics.com/hs-fs/hubfs/Logos%20e%20%C3%ADconos/livestock.png?width=115&height=70&name=livestock.png" alt="Livestock Management" style="max-width: 150px;">
                <h1>Livestock Management System</h1>
            </div>
            <div class="content">
                <p>Hello {owner_name},</p>
                <p>Your appointment has been successfully booked with <strong>{vet_name}</strong> on <strong>{appointment_date}</strong> at <strong>{appointment_time}</strong> for your <strong>{animal_type}</strong>.</p>
                <p>We look forward to assisting you! If you need to reschedule or cancel, please contact us.</p>
            </div>
            <div class="footer">
                <p>© 2025 Livestock Management System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, EMAIL_PASSWORD)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        app.logger.info(f"Appointment confirmation email sent to {email_receiver}")
    except Exception as e:
        app.logger.error(f"Email error: {str(e)}")
        raise


def send_subscription_confirmation_email(email, username):
    msg = Message(
        subject="Welcome to Livestock Management System!",
        recipients=[email],
        body=f"""
        Hello {username},

        Thank you for subscribing to the Livestock Management System! You’ll now receive notifications about upcoming livestock events, campaigns, tips, and other communications.

        If you did not sign up for this, please ignore this email or contact us at support@livestockmgmt.com.

        Best regards,
        The Livestock Management Team
        """
    )
    mail.send(msg)

def send_event_notifications():
    with app.app_context():
        events = Event.query.filter_by(sent=False).all()
        subscribers = User.query.filter_by(role='subscriber').all()

        for event in events:
            for subscriber in subscribers:
                msg = Message(
                    subject=f"Upcoming Event: {event.title}",
                    recipients=[subscriber.email_address],
                    body=f"""
                    Hello {subscriber.username},

                    We have an upcoming event for you!

                    **{event.title}**
                    Date: {event.event_date.strftime('%Y-%m-%d')}
                    Details: {event.content}

                    Best regards,
                    The Livestock Management Team

                    To unsubscribe, click here: {url_for('unsubscribe', email=subscriber.email_address, _external=True)}
                    """
                )
                try:
                    mail.send(msg)
                except Exception as e:
                    app.logger.error(f"Failed to send event email to {subscriber.email_address}: {str(e)}")

            event.sent = True
            db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_event_notifications, trigger="interval", hours=24)
scheduler.start()


import atexit
atexit.register(lambda: scheduler.shutdown())


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()

    if form.validate_on_submit():
        # Debug: Print the submitted role to verify
        print(f"Submitted role: {form.role.data}")

        # Check for existing username or email
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", category='danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email_address=form.email_address.data).first():
            flash("Email already exists.", category='danger')
            return render_template('register.html', form=form)

        # Create new user with the selected role
        new_user = User(
            username=form.username.data,
            email_address=form.email_address.data,
            password_hash=generate_password_hash(form.password1.data),
            role=form.role.data,
            email_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Create account creation notification with "account" category
        notification = Notification(
            user_id=new_user.id,
            content=f"Welcome, {new_user.username}! Your account has been created successfully. Please verify your email to continue.",
            read=False,
            created_at=datetime.utcnow(),
            category="account"  # Set category for styling in notifications.html
        )
        db.session.add(notification)
        db.session.commit()

        # Generate verification token and send email
        token = generate_verification_token(new_user.email_address)
        try:
            send_verification_email(new_user.email_address, new_user.username, token)
            flash("Account created! Please check your email to verify your account.", category='success')
        except Exception as e:
            flash("Failed to send verification email. Please try again later.", category='danger')
            print(f"Email sending failed: {str(e)}")
            # Optionally delete the user if email fails
            db.session.delete(new_user)
            db.session.delete(notification)
            db.session.commit()
            return render_template('register.html', form=form)

        # Redirect to verify pending page for new users
        return redirect(url_for('verify_pending', email=new_user.email_address))

    return render_template('register.html', form=form)


@app.route('/verify-pending/<email>')
def verify_pending(email):
    return render_template('verify_pending.html', email=email)


@app.route('/resend-verification/<email>')
def resend_verification(email):
    user = User.query.filter_by(email_address=email, email_verified=False).first()
    if user:
        token = generate_verification_token(user.email_address)  # Assume this function exists
        try:
            send_verification_email(user.email_address, user.username, token)
            flash("A new verification email has been sent!", category='info')
        except Exception as e:
            flash("Failed to send verification email. Please try again later.", category='danger')
            print(f"Email sending failed: {str(e)}")
    else:
        flash("No unverified account found for this email.", category='danger')
    return redirect(url_for('verify_pending', email=email))



@app.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    email = verify_verification_token(token)
    if not email:
        flash("The verification link is invalid or has expired.", category='danger')
        return redirect(url_for('login_page'))

    user = User.query.filter_by(email_address=email).first()
    if not user:
        flash("User not found.", category='danger')
        return redirect(url_for('login_page'))

    if user.email_verified:
        flash("Email already verified. Please log in.", category='info')
        return redirect(url_for('login_page'))

    # Verify the email
    user.email_verified = True
    db.session.commit()

    # Create a notification for successful verification
    notification = Notification(
        user_id=user.id,
        content="Your email has been successfully verified!",
        read=False,
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()

    # Log in the user after verification
    login_user(user)

    flash("Email verified successfully! Welcome aboard!", category='success')

    # Redirect based on role
    if user.role == 'admin':
        return redirect(url_for('create_event'))
    return redirect(url_for('home_page'))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                if user.email_verified:
                    login_user(user)
                    session.permanent = True  # Make session permanent
                    # Create login notification with "login" category
                    notification = Notification(
                        user_id=user.id,
                        content=f"Welcome back, {user.username}! You have successfully logged in.",
                        read=False,
                        created_at=datetime.utcnow(),
                        category="login"  # Set category for styling in notifications.html
                    )
                    db.session.add(notification)
                    db.session.commit()
                    
                    # Redirect based on role
                    if user.role == 'admin':
                        return redirect(url_for('create_event'))
                    return redirect(url_for('home_page'))
                else:
                    flash("Please verify your email before logging in.", category='warning')
                    return redirect(url_for('verify_pending', email=user.email_address))
            else:
                flash("Incorrect password. Please try again.", category='danger')
                return render_template('login.html', form=form)
        else:
            flash("Username not found. Please register to create an account.", category='danger')
            return redirect(url_for('register_page'))
    
    return render_template('login.html', form=form)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    form = ChatForm()
    user = current_user
    
    if user.role == 'farmer':
        form.receiver_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='vet').all()]
    else:
        form.receiver_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='farmer').all()]
    
    if form.validate_on_submit():
        message = Message(
            sender_id=user.id,
            receiver_id=form.receiver_id.data,
            content=form.content.data
        )
        db.session.add(message)
        notification = Notification(
            user_id=form.receiver_id.data,
            content=f"New message from {user.username}"
        )
        db.session.add(notification)
        receiver = User.query.get(form.receiver_id.data)
        send_vetconnect_alert(
            receiver.email_address,
            "New Message in VetApp",
            f"Hi {receiver.username},\n\nYou have a new message from {user.username}: {form.content.data}\n\nCheck it at {url_for('chat', _external=True)}"
        )
        db.session.commit()
        flash("Message sent!", category='success')
        return redirect(url_for('chat'))
    
    sent = Message.query.filter_by(sender_id=user.id).order_by(Message.timestamp.desc()).all()
    received = Message.query.filter_by(receiver_id=user.id).order_by(Message.timestamp.desc()).all()
    
    return render_template('chat.html', form=form, sent=sent, received=received)


@app.route('/tips', methods=['GET', 'POST'])
@login_required
def tips():
    form = TipForm()
    if current_user.role == 'vet' and form.validate_on_submit():
        try:
            tip = Tip(
                title=form.title.data,
                content=form.content.data,
                author_id=current_user.id
            )
            db.session.add(tip)
            db.session.commit()
            
            # Create notification for the vet (confirmation)
            vet_notification = Notification(
                content=f"Tip Posted: {form.title.data}",
                category='tip_confirmation',
                user_id=current_user.id
            )
            db.session.add(vet_notification)
            db.session.commit()
            
            flash("Tip posted successfully!", category='success')
            return redirect(url_for('tips'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error posting tip: {str(e)}", category='error')
            app.logger.error(f"Error saving tip: {str(e)}")
    
    tips_list = Tip.query.order_by(Tip.posted_at.desc()).all()
    return render_template('tips.html', form=form, tips_list=tips_list)


        






        
