from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, PostForm
from app.models import User, Post
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])  # default home page
@bp.route('/index', methods=['GET', 'POST'])
@login_required  # stops people from viewing home page unless if they have logged in...now app opens on login page by default
def index():
    form = PostForm()
    if form.validate_on_submit(): # allows users to post on blog which are then saved to database
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now up!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False) # shows posts of user and the users that they follow
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='HOME', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore') # used to see all posts from users, not just from the ones an account follows
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your edits have been saved!')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} has not been found!'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You are unable to follow yourself you loser!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}}!'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} has not been found!'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You are unable to unfollow yourself you loser!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are now not following {}!'.format(username))
    return redirect(url_for('main.user', username=username))