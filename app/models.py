from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# Set up user_loader
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.VARCHAR(255), unique=True, index=True)
    first_name = db.Column(db.VARCHAR(255))
    last_name = db.Column(db.VARCHAR(255))
    id_photo = db.Column(db.VARCHAR(255))
    billing_address = db.Column(db.VARCHAR(6))
    address = db.Column(db.VARCHAR(255))
    password_hash = db.Column(db.VARCHAR(255))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), index=True)
    blacklist = db.Column(db.Boolean)
    number_of_warning = db.Column(db.Integer)
    rating = db.Column(db.DECIMAL(4, 2))
    payment = db.Column(db.VARCHAR(255))
    store_id = db.Column(db.Integer, db.ForeignKey('store.storeid'))
    salary = db.Column(db.DECIMAL(9, 2))
    order_made = db.Column(db.Integer)
    number_of_drop = db.Column(db.Integer)
    vip_store_id = db.Column(db.Integer)

    role = db.relationship("Role", foreign_keys=[role_id], back_populates="user")
    store = db.relationship("Store", foreign_keys=[store_id], backref="user")

    def set_role_id(self, rid):
        self.role_id = rid

    def get_role_id(self):
        return self.role_id

    def set_password(self, passwords):
        self.password_hash = generate_password_hash(passwords)

    def check_password(self, passwords):
        return check_password_hash(self.password_hash, passwords)

    def __repr__(self):
        return '<User: {}, {}>'.format(self.password_hash, self.email)


class Store(db.Model):
    __tablename__ = 'store'

    storeid = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    role_type = db.Column(db.VARCHAR(60), unique=True)
    user = db.relationship("User", back_populates="role")  # user must equal to back_populates "user" on other table

    def __repr__(self):
        return '<Role: {}, {}>'.format(self.id, self.role_type)


class Cake(db.Model):
    __tablename__ = 'cakes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cake_name = db.Column(db.VARCHAR(255), nullable=False)
    visitor_price = db.Column(db.DECIMAL(5, 2))
    customer_price = db.Column(db.DECIMAL(5, 2))
    vip_price = db.Column(db.DECIMAL(5, 2))
    photo = db.Column(db.VARCHAR(255))
    description = db.Column(db.VARCHAR(255))
    rating = db.Column(db.DECIMAL(4, 2))
    order_made = db.Column(db.Integer)
    drop_amount = db.Column(db.Integer)
    store1 = db.Column(db.Integer)
    store2 = db.Column(db.Integer)
    store3 = db.Column(db.Integer)
    store4 = db.Column(db.Integer)
    store5 = db.Column(db.Integer)
    store6 = db.Column(db.Integer)
    store7 = db.Column(db.Integer)
    cart = db.relationship("Cart", back_populates="cake")
    store1 = db.Column(db.Integer)

    def __repr__(self):
        return '<Cake: {}, {}, {}, {}>'.format(self.id, self.cake_name, self.photo, self.description)


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cake_id = db.Column(db.Integer, db.ForeignKey('cakes.id'))
    cook_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deliver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    checkout_store = db.Column(db.Integer, db.ForeignKey('store.storeid'))
    amount = db.Column(db.Integer)
    price = db.Column(db.DECIMAL(6, 2))
    status = db.Column(db.VARCHAR(30))  # Not submitted, Submitted, In process, Closed
    cake_rating = db.Column(db.Integer)
    deliver_rating = db.Column(db.Integer)
    store_rating = db.Column(db.Integer)
    cake_comments = db.Column(db.VARCHAR(255))
    deliver_comments = db.Column(db.VARCHAR(255))
    store_comments = db.Column(db.VARCHAR(255))
    user_rating = db.Column(db.Integer)
    user_comments = db.Column(db.VARCHAR(255))
    time_submit = db.Column(db.DateTime)
    is_cake_drop = db.Column(db.Boolean)
    is_cook_warning = db.Column(db.Boolean)
    is_delivery_warning = db.Column(db.Boolean)
    checkout_address = db.Column(db.VARCHAR(255))
    current_store_id = db.Column(db.Integer)

    cake = db.relationship("Cake", back_populates="cart")
    user = db.relationship("User", foreign_keys=[user_id], backref="user_cart")
    cook = db.relationship("User", foreign_keys=[cook_id], backref="cook_cart")
    deliver = db.relationship("User", foreign_keys=[deliver_id], backref="deliver_cart")
    store = db.relationship("Store", foreign_keys=[checkout_store], backref="store_cart")

    def __repr__(self):
        return '<Cart: {}, {}>'.format(self.id, self.amount, self.price)

    def set_time(self, time):
        self.time_submit = time
