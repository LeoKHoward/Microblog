from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])  # what comes up on login page
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # if user is already logged in, they will be redirected to the index page
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()  # .first() returns the user object if it exists or None if it does not
        if user is None or not user.check_password(form.password.data):  # if user does not exist above or if the password is wrong
            flash('Incorrect username or password. Please try again!')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)  # happens if username and password exist/are correct
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':  # url_parse ensures redirect stays on the same website rather than going to malicious external website
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)  # links to login.html / title of tab is Sign In / passes in line above


@bp.route('/logout')  # offer users option to log out of session
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You have now registered your details!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect (url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions on how to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has now been reset')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

