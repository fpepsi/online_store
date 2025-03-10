from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, Text, DateTime, Boolean, select
from datetime import datetime
import pytz

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Products Table
class Product(db.Model):
    __tablename__ = 'products'
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("departments.department_id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(100))
    website_url: Mapped[str] = mapped_column(String(255))
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    cost: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    product_family: Mapped[str] = mapped_column(String(100))
    stripe_product_code: Mapped[str] = mapped_column(String(255))
    stripe_price_code: Mapped[str] = mapped_column(String(255))
    
    department = relationship('Department', back_populates='products')
    inventory = relationship('Inventory', back_populates='product', uselist=False, cascade="all, delete-orphan")

# Departments Table
class Department(db.Model):
    __tablename__ = 'departments'
    department_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Many-to-Many Relationship with Inventory and products
    products = relationship("Product", back_populates="department")

# Inventory Table
class Inventory(db.Model):
    __tablename__ = 'inventory'
    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acquired_date = db.Column(db.DateTime, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(pytz.utc))

    product = db.relationship('Product', back_populates='inventory', uselist=False)

# Association Table for Many-to-Many Relationship (Inventory <-> Department)
inventory_department = db.Table(
    'inventory_department',
    db.Column('inventory_id', db.Integer, db.ForeignKey('inventory.inventory_id'), primary_key=True),
    db.Column('department_id', db.Integer, db.ForeignKey('departments.department_id'), primary_key=True)
)

# Base User class (for shared login behavior)
class BaseUser(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    
    client = relationship('Client', back_populates='user', uselist=False, cascade="all, delete-orphan")
    employee = relationship('Employee', back_populates='user', uselist=False, cascade="all, delete-orphan")

# Clients Table
class Client(db.Model):
    __tablename__ = 'clients'
    client_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(pytz.utc))

    user = relationship('BaseUser', back_populates='client', uselist=False)
    addresses = relationship('Address', back_populates='client', cascade="all, delete-orphan")
    cart = relationship('UserCart', back_populates='client', cascade="all, delete-orphan")

# Employees Table
class Employee(db.Model):
    __tablename__ = 'employees'
    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    job_title: Mapped[str] = mapped_column(String(100), nullable=True)
    clearance_code: Mapped[str] = mapped_column(String(2), nullable=True) # '99' (Admin), '00' (Blocked), or other
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship('BaseUser', back_populates='employee', uselist=False)
    addresses = relationship('Address', back_populates='employee', cascade="all, delete-orphan")

# Addresses Table (For Clients & Employees)
class Address(db.Model):
    __tablename__ = 'addresses'
    address_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    street: Mapped[str] = mapped_column(String(255))
    number: Mapped[str] = mapped_column(String(20))
    complement: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(20))
    
    client_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('clients.client_id'), nullable=True)
    employee_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('employees.employee_id'), nullable=True)

    client = relationship('Client', back_populates='addresses')
    employee = relationship('Employee', back_populates='addresses')


# Transactions Table
class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('clients.client_id'), nullable=True)
    store_account_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('store_accounts.st_acc_id'), nullable=True) 
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'Buy' or 'Sell'
    total_amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag to mark canceled transactions

    client = relationship('Client')
    store_account = relationship('StoreAccount', back_populates='transactions')
    transaction_items = relationship('TransactionItem', back_populates='transaction', cascade="all, delete-orphan")
    payments = relationship('Payment', back_populates='transaction')


# Transaction Items Table (For Multi-Product Transactions)
class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'
    t_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('transactions.transaction_id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    transaction = relationship('Transaction', back_populates='transaction_items')
    product = relationship('Product')

# Payments Table (Handles Both Cash & Credit Transactions)
class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('transactions.transaction_id'), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'Credit Card', 'Cash', 'Bank Transfer'
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transaction = relationship('Transaction', back_populates='payments')

class StoreAccount(db.Model):
    __tablename__ = 'store_accounts'
    st_acc_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'Cash' or 'Credit'
    balance: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False, default=0.00)

    transactions = relationship("Transaction", back_populates="store_account", cascade="all, delete-orphan")

# UserCart Table (One per User)
class UserCart(db.Model):
    __tablename__ = "user_carts"
    cart_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("clients.client_id"), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="cart")
    cart_items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

# CartItem Table (Stores Products Added to the Cart)
class CartItem(db.Model):
    __tablename__ = "cart_items"
    c_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user_carts.cart_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    cart = relationship("UserCart", back_populates="cart_items")
    product = relationship("Product")

# class UserCartManager:
#     def __init__(self, client_id):
#         self.client_id = client_id
#         self.cart = db.session.execute(select(UserCart).filter_by(client_id=client_id)).scalar()

    # def add_item(self, product_id: int, price: Numeric, quantity: int = 1):
    #     """Adds a product to the cart, or updates quantity if it exists."""
    #     cart_item = CartItem.query.filter_by(cart_id=self.cart.cart_id, product_id=product_id).first()
    #     if cart_item:
    #         cart_item.quantity += quantity
    #     else:
    #         cart_item = CartItem(cart_id=self.cart.cart_id, product_id=product_id, quantity=quantity, price=price)
    #         db.session.add(cart_item)
    #     db.session.commit()

    # def remove_item(self, product_id: int):
    #     """Removes a product from the cart."""
    #     cart_item = CartItem.query.filter_by(cart_id=self.cart.cart_id, product_id=product_id).first()
    #     if cart_item:
    #         db.session.delete(cart_item)
    #         db.session.commit()

    # def update_quantity(self, product_id: int, quantity: int):
    #     """Updates quantity of a product in the cart."""
    #     cart_item = CartItem.query.filter_by(cart_id=self.cart.cart_id, product_id=product_id).first()
    #     if cart_item:
    #         cart_item.quantity = quantity
    #         db.session.commit()

    # def clear_cart(self):
    #     """Clears all items from the cart."""
    #     CartItem.query.filter_by(cart_id=self.cart.cart_id).delete()
    #     db.session.commit()

    # def get_cart_items(self):
    #     """Returns all cart items for this user."""
    #     return CartItem.query.filter_by(cart_id=self.cart.cart_id).all()

    # def calculate_total(self):
    #     """Calculates total cart value."""
    #     return sum(item.quantity * item.price for item in self.cart.cart_items)

