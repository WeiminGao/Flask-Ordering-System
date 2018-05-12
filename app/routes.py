from app import app, db, login_manager
from flask import render_template, flash, redirect, request, url_for, jsonify, send_from_directory, session
from app.models import User, Cake, Cart, Store
from werkzeug.urls import url_parse
from functools import wraps
from werkzeug.utils import secure_filename
import os
from decimal import *
from sqlalchemy import func, or_, desc
from flask_login import current_user, login_user, logout_user
from datetime import datetime

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


########################################################################################################################
# Customer without login_required


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))
            urole = current_user.role_id
            boo = False
            for role in roles:
                if urole == role:
                    boo = True
            if not boo:
                return login_manager.unauthorized()
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


@app.route('/index')
def index():
    store_address = int(session['store_address'])
    if current_user.is_authenticated:
        cakes = db.session.query(Cart).filter(Cart.user_id == current_user.id, Cart.order_id is not None).order_by(
            desc(Cart.order_id)).all()
        return render_template('index.html', cakes=cakes)
    if store_address == 1:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store1)).all()
    elif store_address == 2:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store2)).all()
    elif store_address == 3:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store3)).all()
    elif store_address == 4:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store4)).all()
    elif store_address == 5:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store5)).all()
    elif store_address == 6:
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store6)).all()
    else:  # store_address == 7
        cakes = db.session.query(Cake).filter(Cake.cake_name != "Custom Cake").order_by(desc(Cake.store7)).all()

    return render_template('index.html', cakes=cakes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role_id == 7:
            return redirect(url_for('manager', id=current_user.id))
        if current_user.role_id == 6:
            return redirect(url_for('cook'))
        if current_user.role_id == 5:
            return redirect(url_for('deliver'))
        else:
            return redirect(url_for('index'))
    if request.method == 'POST':
        e = User.query.filter_by(email=request.values.get('email')).first()
        if e is None:
            flash("Our system does not have your record. "
                  "Please check your Email or password. "
                  "Or create a new account.")
        elif e is not None and e.check_password(request.values.get('password')) \
                and e.blacklist == 0:
            login_user(e)
            if e.role_id == 1 or e.role_id == 3 or e.role_id == 4:
                first_index = session['user_address'][0]
                second_index = session['user_address'][1]
                print(first_index)
                print(second_index)
                e.address = str(first_index) + "," + str(second_index)
                db.session.commit()
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                if current_user.role_id == 7:
                    next_page = url_for('manager', id=current_user.id)
                elif current_user.role_id == 6:
                    next_page = url_for('cook')
                elif current_user.role_id == 5:
                    next_page = url_for('deliver')
                else:
                    next_page = url_for('index')
            return redirect(next_page)
        elif e.blacklist == 1:
            flash("Blacklist account will be blocked")
        else:
            flash('Invalid email or password')
    return render_template('login.html', title='Sign In')


@app.route('/menu')
def menu():
    cakes = Cake.query.filter(Cake.cake_name != "Custom Cake")

    return render_template('menu.html', cakes=cakes)


@app.route('/customize_cake', methods=['GET', 'POST'])
def customize_cake():
    cooks = User.query.filter_by(role_id=6, store_id=int(session['store_address']))  # store_id = ?
    if request.method == 'POST':
        description = request.values.get('cake flavors') + ", " + request.values.get('cake filling') + ", " + \
                      request.values.get('frosting') + ", " + request.values.get('toppings') + ", " + \
                      request.values.get('size')
        newCake = Cake(cake_name="Custom Cake",
                       visitor_price=120, customer_price=0.95 * 120, vip_price=0.9 * 120,
                       photo="CustomCake_Default.png", description=description)
        db.session.add(newCake)
        cake = Cake.query.filter_by(description=description).first()
        if current_user.is_anonymous:
            amount = int(request.values.get('amount'))
            if amount <= 0:
                flash("Invalid amount, Please enter a positive amount")
                return redirect(url_for('description', id=cake.id))
            cook_id = int(request.values.get('cook'))
            if str(cake.id) not in session:
                cook = User.query.filter_by(id=cook_id).first()
                session[str(cake.id)] = [cake.id, amount, cook.id, cake.cake_name,
                                         cook.first_name, cake.visitor_price]
                flash("Successful added your cake.")
                return redirect(url_for('menu'))
            else:
                flash("Initial amount: " + str(session[str(cake.id)][1]))
                session[str(cake.id)][1] += amount
                flash("After changed the amount: " + str(session[str(cake.id)][1]))
                return redirect(url_for('menu'))

        else:  # if current_user.id
            cart = Cart.query.filter_by(user_id=current_user.id, cake_id=cake.id,
                                        status="Not submitted").one_or_none()
            cook = request.form['cook']
            amount = int(request.values.get('amount'))
            if amount <= 0:
                flash("Invalid amount. Please enter a positive amount")
                return redirect(url_for('description', id=cake.id))
            if cart is None:
                if current_user.role.id == 4 and current_user.vip_store_id == int(session['store_address']):
                    price_of = cake.vip_price
                elif current_user.role.id == 3:
                    price_of = cake.customer_price
                else:
                    price_of = cake.visitor_price
                temp = Cart(cake_id=cake.id, user_id=current_user.id, amount=amount,
                            price=price_of, status="Not submitted", cook_id=cook, cake_rating=0,
                            deliver_rating=0, user_rating=0, store_rating=0, is_cake_drop=0, is_cook_warning=0,
                            is_delivery_warning=0, current_store_id=int(session['store_address']))
                db.session.add(temp)
                db.session.commit()
                flash('Added to your cart')
                return redirect(url_for('cart'))
        flash('Added to your cart successfully')
    return render_template('customers/customize_cake.html', cooks=cooks)


@app.route('/logout')
@login_required(1, 3, 4, 5, 6, 7)
def logout():
    logout_user()
    return redirect(url_for('mapforcust'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        if current_user.role_id == 7:
            return redirect(url_for('manager'))
        if current_user.role_id == 6:
            return redirect(url_for('cook'))
        if current_user.role_id == 5:
            return redirect(url_for('delivery'))
        else:
            return redirect(url_for('index'))

    if request.method == 'POST':
        idPic = request.files['identification']

        if request.values.get('password') == request.values.get('password2'):
            if idPic and allowed_file(idPic.filename):
                filename = secure_filename(idPic.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                idPic.save(path)
                newname = request.values.get('email') + '.png'
                target = os.path.join(app.config['UPLOAD_FOLDER'], newname)
                os.rename(path, target)

                print(request.values.get('address1'))

                u = User.query.filter_by(first_name=request.values.get('firstname'),
                                         last_name=request.values.get('lastname'),
                                         email=request.values.get('email')).first()
                if u is None:
                    try:
                        u = User(email=request.values.get('email'), address=(
                                str(session['user_address'][0]) + "," + str(session['user_address'][1])),
                                 role_id='1', first_name=request.values.get('firstname'),
                                 last_name=request.values.get('lastname'),
                                 id_photo=newname, rating=0.0, number_of_warning=0, order_made=0,
                                 blacklist=0, number_of_drop=0, vip_store_id=0, store_id=int(session['store_address']))

                        u.set_password(request.values.get('password'))
                        db.session.add(u)
                        db.session.commit()

                        flash('You have successfully registered! You may now login.')
                        return redirect(url_for('login'))
                    except:
                        flash("Error in requesting, db down")
                else:
                    if u.blacklist == 1:
                        flash("You have been banned from our system")
                    else:
                        if u.password_hash is None or u.password_hash == "":
                            exist_user = User.query.filter_by(first_name=request.values.get('firstname'),
                                                              last_name=request.values.get('lastname'),
                                                              email=request.values.get('email')).first()
                            exist_user.set_password(request.values.get('password'))
                            exist_user.store_id = session['store_address']
                            exist_user.address = (
                                    str(session['user_address'][0]) + "," + str(session['user_address'][1]))
                            db.session.commit()
                            flash('You have successfully registered! You may now login.')
                            return redirect(url_for('login'))
                        else:
                            flash("Provided information is duplicated in our system.")
            else:
                flash("invalid file")
        else:
            flash('The specified passwords do not match')
    return render_template('customers/registerform.html')


@app.route('/customer/description/<id>', methods=['GET', 'POST'])
def description(id):
    cake = Cake.query.filter_by(id=id).first()
    cooks = User.query.filter_by(role_id=6, store_id=int(session['store_address']))
    if request.method == 'POST' and current_user.is_anonymous:
        amount = int(request.values.get('amount'))
        if amount <= 0:
            flash("Invalid amount")
            return redirect(url_for('description', id=cake.id))
        cook_id = int(request.values.get('cook'))
        if str(cake.id) not in session:
            cook = User.query.filter_by(id=cook_id).first()
            session[str(cake.id)] = [cake.id, amount, cook.id, cake.cake_name,
                                     cook.first_name, cake.visitor_price]
            flash("Successful store to Session")
            return redirect(url_for('menu'))
        else:
            flash("Initial amount: " + str(session[str(cake.id)][1]))
            session[str(cake.id)][1] += amount
            flash("After changed the amount: " + str(session[str(cake.id)][1]))
            return redirect(url_for('menu'))
    elif request.method == 'POST' and current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id, cake_id=cake.id, status="Not submitted").first()
        cook = request.form['cook']
        amount = int(request.values.get('amount'))
        if current_user.role.id == 4 and current_user.vip_store_id == int(session['store_address']):
            price_of = cake.vip_price
        elif current_user.role.id == 3:
            price_of = cake.customer_price
        else:
            price_of = cake.visitor_price
        if amount <= 0:
            flash("Invalid amount. Please enter a positive amount")
            return redirect(url_for('description', id=cake.id))
        if cart is None:
            temp = Cart(cake_id=cake.id, user_id=current_user.id, amount=amount,
                        price=price_of, status="Not submitted", cook_id=cook, cake_rating=0,
                        deliver_rating=0, user_rating=0, store_rating=0, is_cake_drop=0, is_cook_warning=0,
                        is_delivery_warning=0, current_store_id=int(session['store_address']))
            db.session.add(temp)
            db.session.commit()
            flash('Added to your cart')
            return redirect(url_for('cart'))

        else:
            cart.amount += int(request.values.get('amount'))
            db.session.commit()
            flash('Added to your cart')
            return redirect(url_for('cart'))
    return render_template('customers/description.html', cake=cake, cooks=cooks)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    total = 0
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id, status="Not submitted")

        for i in cart:
            if i.current_store_id != int(session['store_address']):
                current_address = int(session['store_address'])
                if current_user.role.id == 4 and current_user.vip_store_id == current_address:
                    i.price = i.cake.vip_price
                elif current_user.role.id == 3:
                    i.price = i.cake.customer_price
                else:
                    i.price = i.cake.visitor_price
                current_cook_id = User.query.filter_by(id=i.cook_id).first()
                if current_cook_id.store_id != int(session['store_address']):
                    current_cook_id = User.query.filter_by(store_id=int(session['store_address']),
                                                           role_id=6).first()
                i.cook_id = current_cook_id.id
                i.current_store_id = current_address
                db.session.commit()
            total += i.price * i.amount
        return render_template('customers/cart.html', cart=cart, total=total)
    else:
        cart_array = []
        total = 0
        cake_total = db.session.query(func.max(Cake.id)).scalar()
        for j in range(1, int(cake_total) + 1):
            if str(j) in session:
                i = str(j)
                temp = []
                cake_id = session[i][0]
                amount = session[i][1]
                # current_cook_id = User.query.filter_by(id=int(session[i][2])).first()
                # if int(current_cook_id.store_id) != int(session['store_address']):
                #     current_cook_id = User.query.filter_by(store_id=int(session['store_address']),
                #                                            role_id=6).first()
                # cook_id = current_cook_id.id
                cook_id = session[i][2]
                cake_name = session[i][3]
                cook_first_name = session[i][4]
                visitor_price = session[i][5]
                temp.append(cake_id)
                temp.append(amount)
                temp.append(cook_id)
                temp.append(cake_name)
                temp.append(cook_first_name)
                temp.append(visitor_price)
                cart_array.append(temp)
                total += amount * visitor_price
        return render_template('customers/cart.html', cart_array=cart_array, total=total)


@app.route('/edit_cart', methods=['GET', 'POST'])
def edit_cart():
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id, status="Not submitted")
        cooks = User.query.filter_by(role_id=6, store_id=int(session['store_address']))
        if request.method == "POST":
            if request.form['action'] == "submit_submit":
                for i in cart:
                    if request.values.get('amount' + str(i.cake.id)) != "":
                        amount = int(request.values.get('amount' + str(i.cake.id)))
                        if amount <= 0:
                            flash("Invalid amount. Please reenter a amount")
                            return redirect(url_for('edit_cart'))
                        i.amount = request.values.get('amount' + str(i.cake.id))
                    if request.values.get('cook' + str(i.cake.id)) != "":
                        i.cook_id = int(request.values.get('cook' + str(i.cake.id)))
            else:  # submit_drop
                cake_id = request.form['action']
                cake_in_cart = Cart.query.filter_by(cake_id=cake_id, status="Not submitted").first()
                if cake_in_cart is not None:
                    db.session.delete(cake_in_cart)
            db.session.commit()
            flash("Successful edit your cart")
            return redirect(url_for('cart'))
        return render_template('customers/edit_cart.html', cart=cart, cooks=cooks)
    else:
        cart_array = []
        cooks = User.query.filter_by(role_id=6, store_id=int(session['store_address']))
        cake_total = db.session.query(func.max(Cake.id)).scalar()
        for j in range(1, int(cake_total) + 1):
            if str(j) in session:
                i = str(j)
                temp = []
                cake_id = session[i][0]
                amount = session[i][1]
                cake_name = session[i][3]
                cook_id = session[i][2]
                temp.append(cake_id)
                temp.append(amount)
                temp.append(cake_name)
                temp.append(cook_id)
                cart_array.append(temp)
        if current_user.is_anonymous and request.method == "POST":
            if request.form['action'] == "submit_submit":
                for j in range(1, int(cake_total) + 1):
                    if str(j) in session:
                        i = str(j)
                        if request.values.get('amount' + str(session[i][1])) != "":
                            if int(request.values.get('amount' + str(session[i][0]))) <= 0:
                                flash("Invalid, please enter again")
                                return redirect(url_for('edit_cart'))
                            session[i][1] = int(request.values.get('amount' + str(session[i][0])))
                            flash("Successful updated cake")
                        else:
                            flash("You must enter a number")
                        # if request.values.get('cook' + str(session[i][0])) != "":
                        #     session[i][2] = int(request.values.get('cook' + str(session[i][0])))
                return redirect(url_for('menu'))
            else:  # submit_drop
                cake_id = request.form['action']
                if str(cake_id) in session:
                    session.pop(str(cake_id), None)
                    flash("You cake has been dropped")
                    return redirect(url_for('cart'))
        return render_template('customers/edit_cart.html', cart_array=cart_array, cooks=cooks)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
        if user.payment is not None and request.method == 'GET':
            cardname, cardnumber, expired_month, expired_year, cvv = user.payment.split(',')
            return render_template('customers/checkout.html', user=user, cardname=cardname, cardnumber=cardnumber,
                                   expired_month=expired_month, expired_year=expired_year, cvv=cvv,
                                   billing_address=user.billing_address)
        if request.method == 'POST':
            user = User.query.filter_by(id=current_user.id).first()
            indexes = db.session.query(func.max(Cart.order_id)).scalar()
            if indexes is None:
                indexes = 1
            else:
                indexes += 1
            if user.payment is None or user.payment == "":
                flash("You payment is empty, please go to profile and add your payment")
                return redirect(url_for('customer_edit', id=user.id))
            cart_cake = Cart.query.filter_by(user_id=user.id, status="Not submitted").first()
            if cart_cake is None:
                flash("You have no cake to checkout")
                return redirect(url_for('menu'))
            store_address = int(session['store_address'])
            cart_cake = Cart.query.filter_by(user_id=user.id, status="Not submitted")
            for i in cart_cake:
                i.status = "Submitted"
                i.order_id = indexes
                i.checkout_address = user.address
                i.checkout_store = int(session['store_address'])
                i.time_submit = datetime.utcnow()
                store_based(i.id, store_address)
            db.session.commit()
            flash("You have successful checkout your Cart item")
            return redirect(url_for('order_history'))
        return render_template('customers/checkout.html', user=user)
    else:
        address = str(session['user_address'][0]) + "," + str(session['user_address'][1])

        if request.method == 'POST':
            first_name = request.values.get('first_name')
            last_name = request.values.get('last_name')
            email = request.values.get('email')
            card_name = request.values.get('cardname')
            card_number = request.values.get('cardnumber')
            expmonth = request.values.get('expmonth')
            expyear = request.values.get('expyear')
            cvv = request.values.get('cvv')
            billing = request.values.get('billing')
            if first_name == "" or last_name == "" or email == "" or address == "":
                flash("Personal field should not be empty.")
                return redirect(url_for('checkout'))
            if card_name == "" or card_number == "" or expmonth == "" or expyear == "" or cvv == "" or billing == "":
                flash("Payment field should not be empty")
                return redirect(url_for('checkout'))
            payment = card_name + "," + card_number + "," + expmonth + "," + expyear + "," + cvv

            exist_user = User.query.filter_by(email=email, first_name=first_name, last_name=last_name).first()

            if exist_user is None:
                add_user = User(email=email, address=address, role_id=1, first_name=first_name,
                                last_name=last_name, rating=0.0, number_of_warning=0,
                                order_made=0, blacklist=0, number_of_drop=0, payment=payment, billing_address=billing,
                                vip_store_id=0)
                db.session.add(add_user)
                db.session.commit()

            user = User.query.filter_by(email=email, first_name=first_name, last_name=last_name).first()

            cake_total = db.session.query(func.max(Cake.id)).scalar()
            index = db.session.query(func.max(Cart.order_id)).scalar() + 1
            count = 0
            for j in range(1, int(cake_total) + 1):
                if str(j) in session:
                    count += 1
                    i = str(j)
                    cake_id = session[i][0]
                    amount = session[i][1]
                    cook_id = session[i][2]
                    visitor_price = session[i][5]
                    temp = Cart(cake_id=cake_id, user_id=user.id, amount=amount,
                                price=visitor_price, status="Submitted", cook_id=cook_id, cake_rating=0,
                                deliver_rating=0, user_rating=0, store_rating=0, order_id=index,
                                time_submit=datetime.now(), is_cake_drop=0, is_cook_warning=0, is_delivery_warning=0
                                , checkout_address=address, checkout_store=session['store_address'])
                    db.session.add(temp)
                    session.pop(i, None)
            if count == 0:
                flash("You have no items in Cart")
                return redirect(url_for('menu'))
            db.session.commit()
            carts = Cart.query.filter_by(user_id=user.id, order_id=index)
            for cake in carts:
                store_based(cake.id, int(session['store_address']))
            flash("You have successful checkout your Cart items")
            return redirect(url_for('index'))
        return render_template('customers/checkout.html', address=address)


def store_based(id, store_address):
    cart = Cart.query.filter_by(id=id).first()
    if store_address == 1:
        if cart.cake.store1 is None:
            cart.cake.store1 = cart.amount
        else:
            cart.cake.store1 += cart.amount
    elif store_address == 2:
        if cart.cake.store2 is None:
            cart.cake.store2 = cart.amount
        else:
            cart.cake.store2 += cart.amount
    elif store_address == 3:
        if cart.cake.store3 is None:
            cart.cake.store3 = cart.amount
        else:
            cart.cake.store3 += cart.amount
    elif store_address == 4:
        if cart.cake.store4 is None:
            cart.cake.store4 = cart.amount
        else:
            cart.cake.store4 += cart.amount
    elif store_address == 5:
        if cart.cake.store5 is None:
            cart.cake.store5 = cart.amount
        else:
            cart.cake.store5 += cart.amount
    elif store_address == 6:
        if cart.cake.store6 is None:
            cart.cake.store6 = cart.amount
        else:
            cart.cake.store6 += cart.amount
    else:
        if cart.cake.store7 is None:
            cart.cake.store7 = cart.amount
        else:
            cart.cake.store7 += cart.amount
    db.session.commit()


#####################################################################################################
# Customer login required


@app.route('/customer/customer_profile/<id>')
@login_required(1, 3, 4)
def customer_profile(id):
    user = User.query.filter_by(id=id).first_or_404()
    return render_template('customers/customer_profile.html', user=user)


@app.route('/customer/customer_edit/<id>', methods=['GET', 'POST'])
@login_required(1, 3, 4)
def customer_edit(id):
    user = User.query.filter_by(id=id).first_or_404()
    if request.method == "POST":
        email = request.form.get('new_email')
        address = request.form.get('new_address')
        password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_new_password')
        new_cardname = request.form.get('cardname')
        new_cardnumber = request.form.get('cardnumber')
        new_expired_month = request.form.get('expmonth')
        new_expired_year = request.form.get('expyear')
        new_cvv = request.form.get('cvv')
        new_billing_addr = request.form.get('billingaddr')
        try:
            if email != "":
                user.email = email
            if address != "":
                user.address = address
            if password != "" and confirm_password != "":
                if password == confirm_password:
                    user.set_password(password)
            if new_billing_addr != "":
                user.billing_address = new_billing_addr
            if new_cardname != "" or new_cardnumber != "" or new_expired_month != "" \
                    or new_expired_year != "" or new_cvv != "":
                if user.payment is not None:
                    card_name, card_number, expired_month, expired_year, cvv = user.payment.split(',')
                    if new_cardname != "":
                        card_name = new_cardname
                    if new_cardnumber != "":
                        card_number = new_cardnumber
                    if new_expired_month != "":
                        expired_month = new_expired_month
                    if new_expired_year != "":
                        expired_year = new_expired_year
                    if new_cvv != "":
                        cvv = new_cvv
                else:
                    card_name = new_cardname
                    card_number = new_cardnumber
                    expired_month = new_expired_month
                    expired_year = new_expired_year
                    cvv = new_cvv
                payment = card_name + "," + card_number + "," + expired_month + "," + expired_year + "," + cvv
                user.payment = payment
            db.session.commit()
            flash('You have successfully edit your profile!')
            return redirect(url_for('customer_profile', id=current_user.id))
        except:
            flash("Either your information is duplicated in our system or your password is wrong")
    return render_template('customers/customer_edit.html', user=user)


@app.route('/customer/order_history')
@login_required(1, 3, 4)
def order_history():
    counts = db.session.query(func.max(Cart.order_id)).scalar()
    carts = Cart.query.filter(or_(Cart.status == "Submitted",
                                  Cart.status == "In Process", Cart.status == "Closed")) \
        .filter(Cart.user_id == current_user.id)
    return render_template('customers/order_history.html', carts=carts, counts=counts)


@app.route('/customer/rating/<id>', methods=['GET', 'POST'])
@login_required(1, 3, 4)
def rating(id):
    cart = Cart.query.filter_by(id=id).first()
    if request.method == "POST":
        if request.form.get('store_rating') is None:
            flash("Store rating is empty")
            return redirect(url_for('rating', id=id))
        store_rating = int(request.form.get('store_rating'))

        if request.form.get('deliver_rating') is None:
            flash("Deliver rating is empty")
            return redirect(url_for('rating', id=id))
        deliver_rating = int(request.form.get('deliver_rating'))

        if request.form.get('cake_rating') is None:
            flash("Cake rating is empty")
            return redirect(url_for('rating', id=id))
        cake_rating = int(request.form.get('cake_rating'))

        cake_comments = request.form.get('cake_comments')
        deliver_comments = request.form.get('deliver_comments')
        store_comments = request.form.get('store_comments')

        if store_rating < 3 and store_comments == '':
            flash("Rating lower than 3 must provide comments")
            return redirect(url_for('rating', id=id))
        if cake_rating < 3 and cake_comments == '':
            flash("Rating lower than 3 must provide comments")
            return redirect(url_for('rating', id=id))
        if deliver_rating < 3 and deliver_comments == '':
            flash("Rating lower than 3 must provide comments")
            return redirect(url_for('rating', id=id))

        cart.store_rating = store_rating
        cart.store_comments = store_comments
        cart.cake_rating = cake_rating
        cart.cake_comments = cake_comments
        if cart.cake.order_made is None:
            cart.cake.order_made = 0
        cart.cake.order_made += 1
        if cart.cake.order_made == 1:
            cart.cake.rating = cake_rating
        elif cart.cake.order_made == 2:
            cart.cake.rating = (cake_rating + cart.cake.rating) / Decimal(2.0)
        else:  # cart.cake.order_made >= 3
            cart.cake.rating = (cake_rating + (2 * cart.cake.rating)) / Decimal(3.0)
            if cart.cake.rating < Decimal(2.0):
                temp = Cake.query.filter_by(id=cart.cake.id).first()
                db.session.delete(temp)
                flash("Cake " + str(cart.cake.cake_name) + " has been dropped.")
                cart.cook.number_of_drop += 1
                cart.is_cake_drop = True  # record this order will send a cake drop to cook
                flash("Cook " + str(cart.cook_id) + " has been added a number of dropped")
                if cart.cook.number_of_drop >= 2:
                    cart.cook.number_of_warning += 1
                    cart.is_cook_warning = True  # record this order will send a warning to cook
                    flash("Cook has cake was dropped twice before, so there is a warning on his acc")
                    if cart.cook.number_of_warning > 3:
                        cart.cook.blacklist = 1
                        flash("Cook has more than 3 warnings, therefore he/she is laid off")
                    cart.cook.number_of_drop = 0

        cart.deliver_rating = deliver_rating
        cart.deliver_comments = deliver_comments
        if cart.deliver.order_made is None:
            cart.deliver.order_made = 0
        cart.deliver.order_made += 1
        if cart.deliver.order_made == 1:
            cart.deliver.rating = deliver_rating
        elif cart.deliver.order_made == 2:
            cart.deliver.rating = (deliver_rating + cart.deliver.rating) / Decimal(2.0)
        else:
            cart.deliver.rating = (deliver_rating + (2 * cart.deliver.rating)) / Decimal(3.0)
            if cart.deliver.rating < Decimal(2.0):
                cart.deliver.number_of_warning += 1
                cart.is_delivery_warning = True  # record this order will send a warning to delivery man
                flash("Deliver " + str(cart.deliver_id) + " has rating less than 2.0, therefore received a warning")
                if cart.deliver.number_of_warning > 3:
                    cart.deliver.blacklist = 1
                    flash("Deliver has more than 3 warnings, therefore he/she is laid off")
        db.session.commit()
        flash("Thank you for your rating")
        return redirect(url_for("order_history"))
    return render_template('customers/rating.html', cart=cart)


########################################################################################################################
# Deliver


@app.route('/deliver')
@login_required(5)
def deliver():
    logs = Cart.query.filter_by(deliver_id=current_user.id, status="In process", checkout_store=current_user.store_id)
    return render_template('deliveries/delivery.html', title='Deliver', logs=logs)


@app.route('/deliver_rating/<id>', methods=['GET', 'POST'])
@login_required(5)
def deliver_rating(id):
    cart = Cart.query.filter_by(id=id).first()
    if request.method == 'POST':
        update_cart = Cart.query.filter_by(order_id=cart.order_id)
        user = User.query.filter_by(id=cart.user_id).first()
        rating = int(request.form.get('rate_list'))
        comments = request.form.get('comments')
        if rating < 3 and comments == "":
            flash("Comments must be provided if rating is less than 3")
            return redirect(url_for('deliver_rating', id=id))
        for i in update_cart:
            i.user_rating = rating
            i.user_comments = comments
            i.status = "Closed"
        if user.order_made is None:
            user.order_made = 0
        user.order_made += 1
        user.rating = (user.rating + int(rating)) / Decimal(user.order_made)
        if user.order_made > 3 and user.rating > 4.0 and user.role_id == 3:
            user.vip_store_id = cart.checkout_store
            user.role_id = 4  # VIP
        if user.order_made > 3 and 1 < user.rating < 2.0:
            user.role_id = 1  # demote to visitor
            user.vip_store_id = 0
        if user.order_made > 3 and user.rating <= 1.0:
            user.blacklist = 1
            user.role_id = 1
        db.session.commit()
        flash("Thank you your rating and feedback")
        return redirect(url_for("deliver"))
    return render_template('deliveries/deliver_rating.html', cart=cart)


@app.route('/deliver/notification', methods=['GET', 'POST'])
@login_required(5)
def notification():
    delivery = User.query.filter_by(id=current_user.id).first()
    warnings = Cart.query.filter(Cart.status == "Closed", Cart.deliver_id == current_user.id,
                                 Cart.is_delivery_warning == 1)
    if request.method == "POST":
        target = int(request.form['delete'])
        cart_target = Cart.query.filter_by(id=target).first()
        cart_target.is_delivery_warning = False
        db.session.commit()
        flash("Delete Successfully!")
    return render_template('deliveries/notification.html', title='Deliver', delivery=delivery, warnings=warnings)


@app.route('/deliver/profile/<id>')
@login_required(5)
def deliver_profile(id):
    user = User.query.filter_by(id=id).first_or_404()
    return render_template('deliveries/profile.html', user=user)


@app.route('/deliver/edit/<id>', methods=['GET', 'POST'])
@login_required(5)
def deliver_edit(id):
    user = User.query.filter_by(id=id).first_or_404()
    if request.method == "POST":
        email = request.form.get('new_email')

        address = request.form.get('new_address')
        password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_new_password')
        try:
            if email != "":
                user.email = email
            if address != "":
                user.address = address
            if password != "" and confirm_password != "":
                if password == confirm_password:
                    user.set_password(password)
            db.session.commit()
            flash('You have successfully edit your profile!')
            return redirect(url_for('delivery_profile', id=current_user.id))
        except:
            flash("Either your information is duplicated in our system or your password is different")
    return render_template('deliveries/deliver_edit.html', user=user)


@app.route('/deliver/notification')
@login_required(5)
def deliver_notification():
    return render_template('deliveries/notification.html', title='Deliver')


########################################################################################################################
# Cook


@app.route('/cook')
@login_required(6)
def cook():
    cakes = Cake.query.filter(Cake.cake_name != "Custom Cake")
    return render_template('cooks/cook.html', title='Cook', cakes=cakes)


@app.route('/cook/additem', methods=['GET', 'POST'])
@login_required(6)
def additem():
    if request.method == 'POST':
        cakePic = request.files['cakePic']

        if cakePic and allowed_file(cakePic.filename):
            filename = secure_filename(cakePic.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cakePic.save(path)
            newname = (request.values.get('cakeName')).replace(" ", "") + '.png'
            target = os.path.join(app.config['UPLOAD_FOLDER'], newname)
            os.rename(path, target)

            customerPrice = 0.95 * float(request.values.get('price'))
            vipPrice = 0.9 * float(request.values.get('price'))

            newCake = Cake(cake_name=request.values.get('cakeName'),
                           visitor_price=request.values.get('price'), customer_price=customerPrice, vip_price=vipPrice,
                           photo=newname, description=request.values.get('description'), drop_amount=0, order_made=0,
                           rating=0.00)

            db.session.add(newCake)
            db.session.commit()

            flash('success')
        else:
            flash('invalid file')
    return render_template('cooks/cookadditem.html', title='Cook')


@app.route('/cook/dropitem', methods=['GET', 'POST'])
@login_required(6)
def dropitem():
    cakes = Cake.query.all()

    if request.method == "POST":
        cake_name = request.values.get('cake')
        drop_cake = Cake.query.filter_by(cake_name=cake_name).first()
        if drop_cake is not None:
            db.session.delete(drop_cake)
            db.session.commit()
            flash("Successful delete item")

    return render_template('cooks/drop_item.html', title='Cook', cakes=cakes)


@app.route('/cook/edititem', methods=['GET', 'POST'])
@login_required(6)
def edititem():
    cakes = Cake.query.all()

    if request.method == "POST":
        cake_name = request.values.get('cake')
        edit_cake = Cake.query.filter_by(cake_name=cake_name).first()

        price = request.form.get('price')
        description = request.form.get('description')

        if price != "":
            edit_cake.visitor_price = price
            edit_cake.customer_price = 0.95 * float(price)
            edit_cake.vip_price = 0.9 * float(price)
        if description != "":
            edit_cake.description = description
        db.session.commit()
        flash('You have successfully edit item!')
    return render_template('cooks/edit_item.html', title='Cook', cakes=cakes)


@app.route('/cook/cook_profile/<id>')
@login_required(6)
def cook_profile(id):
    user = User.query.filter_by(id=id).first_or_404()
    return render_template('cooks/cook_profile.html', user=user)


@app.route('/cook/cook_edit/<id>', methods=['GET', 'POST'])
@login_required(6)
def cook_edit(id):
    user = User.query.filter_by(id=id).first_or_404()
    if request.method == "POST":
        email = request.form.get('new_email')
        address = request.form.get('new_address')
        password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_new_password')
        try:
            if email != "":
                user.email = email
            if address != "":
                user.address = address
            if password != "" and confirm_password != "":
                if password == confirm_password:
                    user.set_password(password)
            db.session.commit()
            flash('You have successfully edit your profile!')
            return redirect(url_for('cook_profile', id=current_user.id))
        except:
            flash("Either your information is duplicated in our system or your password is different")
    return render_template('cooks/cook_edit.html', user=user)


@app.route('/cook/dropped_notification', methods=['GET', 'POST'])
@login_required(6)
def dropped_notification():
    cook = User.query.filter_by(id=current_user.id).first()
    dropped_cakes = Cart.query.filter(Cart.status == "Closed", Cart.cook_id == current_user.id,
                                      Cart.is_cake_drop == 1)
    if request.method == "POST":
        target = int(request.form['delete'])
        cart_target = Cart.query.filter_by(id=target).first()
        cart_target.is_cake_drop = False
        db.session.commit()
        flash("Delete Successfully!")

    return render_template('cooks/dropped_noti.html', title='Cook', cook=cook, dropped_cakes=dropped_cakes)


@app.route('/cook/warning_notification', methods=['GET', 'POST'])
@login_required(6)
def warning_notification():
    cook = User.query.filter_by(id=current_user.id).first()
    warnings = Cart.query.filter(Cart.status == "Closed", Cart.cook_id == current_user.id,
                                 Cart.is_cook_warning == 1)
    if request.method == "POST":
        target = int(request.form['delete'])
        cart_target = Cart.query.filter_by(id=target).first()
        cart_target.is_cook_warning = False
        db.session.commit()
        flash("Delete Successfully!")

    return render_template('cooks/warning_noti.html', title='Cook', cook=cook, warnings=warnings)


########################################################################################################################
# Manager


@app.route('/manager/<id>')
@login_required(7)
def manager(id):
    user = User.query.filter_by(id=id).first_or_404()
    return render_template('managers/manager.html', user=user)


@app.route('/manager/edit/<id>', methods=['GET', 'POST'])
@login_required(7)
def manager_edit(id):
    user = User.query.filter_by(id=id).first_or_404()
    if request.method == "POST":
        email = request.form.get('new_email')

        address = request.form.get('new_address')
        password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_new_password')
        try:
            if email != "":
                user.email = email
            if address != "":
                user.address = address
            if password != "" and confirm_password != "":
                if password == confirm_password:
                    user.set_password(password)
            db.session.commit()
            flash('You have successfully edit your profile!')
            return redirect(url_for('manager', id=current_user.id))
        except:
            flash("Either your information is duplicated in our system or your password is different")
    return render_template('managers/manager_edit.html', user=user)


@app.route('/manager/CookWarning', methods=['GET', 'POST'])
@login_required(7)
def cookwarning():
    cook = User.query.filter_by(role_id=6, store_id=current_user.store_id)
    if request.method == "POST":
        target = int(request.form['erase'])
        cook_target = User.query.filter_by(id=target).first()
        if cook_target.number_of_warning > 0:
            cook_target.number_of_warning = cook_target.number_of_warning - 1
            db.session.commit()
            flash("Erase Successfully!")
    return render_template('managers/CookWarning.html', cook=cook)


@app.route('/manager/CustomerApplication', methods=['GET', 'POST'])
@login_required(7)
def application():
    me = User.query.filter(User.role_id == 1, User.blacklist != 1, User.store_id == current_user.store_id).all()
    if request.method == 'POST':
        if request.values.get('approve'):
            user_id = int(request.values.get('approve'))
            user = User.query.filter_by(id=user_id).first()
            user.role_id = 3
            user.store_id = None
            db.session.commit()
            flash("Success to approve " + user.first_name + " visitor to registered customer")
        else:
            user_id = int(request.values.get('decline'))
            user = User.query.filter_by(id=user_id).first()
            flash(user.blacklist)
            user.blacklist = 1
            user.store_id = None
            flash(user.blacklist)
            db.session.commit()
            flash("Success to decline " + user.first_name)
    return render_template('managers/CustomerApplication.html', me=me)


@app.route('/manager/CustomerComplaint', methods=['GET', 'POST'])
@login_required(7)
def complaint():
    import datetime
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    message = "7 days ago"
    all_complaints = Cart.query.filter(Cart.status == "Closed", (Cart.store_rating < 3) | (Cart.deliver_rating < 3) |
                                       (Cart.cake_rating < 3), Cart.store_rating > 0, Cart.deliver_rating > 0,
                                       Cart.cake_rating > 0, Cart.time_submit > seven_days_ago)

    if request.method == "POST":
        message = "All Complaints"
        all_complaints = Cart.query.filter(Cart.status == "Closed",
                                           (Cart.store_rating < 3) | (Cart.deliver_rating < 3) |
                                           (Cart.cake_rating < 3), Cart.store_rating > 0, Cart.deliver_rating > 0,
                                           Cart.cake_rating > 0)
        db.session.commit()
        flash("Display All Customer Complaints!")

    return render_template('managers/CustomerComplaint.html', all_complaints=all_complaints, message=message)


@app.route('/manager/order')
@login_required(7)
def order():
    carts = Cart.query.filter_by(status="Submitted", checkout_store=current_user.store_id)
    return render_template('managers/order.html', carts=carts)


@app.route('/manager/assign_order/<id>', methods=['GET', 'POST'])
@login_required(7)
def assign_order(id):
    cart = Cart.query.filter_by(id=id).first()
    delivers = User.query.filter_by(role_id=5, store_id=current_user.store_id)
    if request.method == 'POST':
        deliver_id = request.form['deliver']
        cart.status = "In process"
        cart.deliver_id = deliver_id
        db.session.commit()
        flash("Successful assigned deliver to this order: " + str(cart.id))
        return redirect(url_for("order"))
    return render_template('managers/assign_order.html', delivers=delivers, cart=cart)


@app.route('/manager/DeliverWarning', methods=['GET', 'POST'])
@login_required(7)
def deliverwarning():
    delivery = User.query.filter_by(role_id=5, store_id=current_user.store_id)
    if request.method == "POST":
        target = int(request.form['erase'])
        delivery_target = User.query.filter_by(id=target).first()
        if delivery_target.number_of_warning > 0:
            delivery_target.number_of_warning = delivery_target.number_of_warning - 1
            db.session.commit()
            flash("Erase Successfully!")
    return render_template('managers/DeliverWarning.html', delivery=delivery)


@app.route('/manager/ManageCustomers', methods=['GET', 'POST'])
@login_required(7)
def managecustomers():
    customers = User.query.filter((User.role_id == 1) | (User.role_id == 3) | (User.role_id == 4))
    message = ""
    if request.method == "POST":
        name = str(request.form['customer_name'])
        name = name.split()
        if len(name) != 2:
            message = "Please follow the format (First_name Last_name)"
        else:
            customers = User.query.filter_by(first_name=name[0], last_name=name[1])
            message = ""
    return render_template('managers/ManageCustomers.html', customers=customers, message=message)


@app.route('/manager/PayWage', methods=['GET', 'POST'])
@login_required(7)
def paywage():
    delivery = User.query.filter_by(role_id=5, store_id=current_user.store_id)
    cook = User.query.filter_by(role_id=6, store_id=current_user.store_id)
    if request.method == 'POST':
        if request.form['action'] == "new_sheet":
            for i in delivery:
                if request.values.get('hours' + str(i.id)) == "":
                    i.salary = 0.0
                    db.session.commit()
            for j in cook:
                if request.values.get('hours' + str(j.id)) == "":
                    j.salary = 0.0
                    db.session.commit()
            flash("New salary sheet")

        if request.form['action'] == "submit_hours":
            for i in delivery:
                if request.values.get('hours' + str(i.id)) == "":
                    i.salary = i.salary
                else:
                    i.salary = float(request.values.get('hours' + str(i.id))) * 15
                    db.session.commit()
            for j in cook:
                if request.values.get('hours' + str(j.id)) == "":
                    j.salary = j.salary
                else:
                    j.salary = float(request.values.get('hours' + str(j.id))) * 20
                    db.session.commit()
            flash("Submit Successfully!")
    return render_template('managers/PayWage.html', delivery=delivery, cook=cook, delivery_salary_rate=15,
                           cook_salary_rate=20)


########################################################################################################################
# Map

@app.route('/')
@app.route('/mapforcustomers')
def mapforcust():
    return render_template('customers/MapForCustomer.html')


@app.route('/mapforcustomers/ajax', methods=['POST'])
def mapforcoord():
    x = request.form.get('x', 0, type=int)
    y = request.form.get('y', 0, type=int)
    c_x = request.form.get('c_x', 0, type=int)
    c_y = request.form.get('c_y', 0, type=int)
    u = Store.query.filter_by(width=x, height=y).first()
    session['store_address'] = u.storeid
    session['user_address'] = [c_x, c_y]
    print(session['user_address'])
    print(session['store_address'])
    session.modified = True
    flash("Updated session")
    return jsonify('success')


@app.route('/delivery/route/<id>', methods=['GET'])
@login_required(5)
def delivery_route(id):
    customer = Cart.query.filter_by(id=id).first()
    custaddr = customer.checkout_address.split(',')
    cust_x = int(custaddr[0])
    cust_y = int(custaddr[1])
    store_id = customer.checkout_store
    storeaddr = Store.query.filter_by(storeid=store_id).first()
    storex = storeaddr.width
    storey = storeaddr.height
    return render_template('deliveries/MapForDelivery.html', cust_x=cust_x, cust_y=cust_y, storex=storex, storey=storey,
                           store_id=store_id)
