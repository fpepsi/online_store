import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, login_required, LoginManager, current_user, logout_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, DepartmentForm, ProductForm, EmployeeForm, TransactionForm, PaymentForm, ClientForm, AddressForm, InventoryForm
from datetime import datetime
from database import db, Product, Department, Inventory, BaseUser, Client, Address, Employee, Transaction, TransactionItem, Payment, UserCart, CartItem
import re
from sqlalchemy.event import listens_for
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import joinedload
from sqlalchemy import select
import stripe


# load virtual environment and initiate Flask
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'retail.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
YOUR_DOMAIN = "http://127.0.0.1:5000"

# payment website key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# initiate database
db.init_app(app)
with app.app_context():
    db.create_all()

# load migration option and bootstrap form functionalities
migrate = Migrate(app, db)
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

csrf = CSRFProtect(app)

# configure user loader for Flask Login
@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(BaseUser, int(user_id))  # ✅ SQLAlchemy 2.0 Compatible
    if user:
        return user
    return None


# configure employee access decorator
def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.employee:
            return redirect(url_for("login"))
        # New employees initially receive code "00" without any system access.
        if current_user.employee.clearance_code == "00":  
            return "Access Denied: Your account is not activated"
        return f(*args, **kwargs)
    return decorated_function


def get_primary_key(model):
    """Returns the primary key column name for a given SQLAlchemy model class."""
    return inspect(model).primary_key[0].name  # Get the first (and usually only) primary key


@app.context_processor
def inject_departments():
    departments = db.session.execute(db.select(Department)).scalars().all()
    return {'departments': departments}  # departments will feed base.html and be available to all templates


# Home Route
@app.route("/")
def home():
    return render_template("home.html", year=datetime.now().year)


# Departments Route
@app.route("/department/<department>")
def department_page(department):
    department_id = db.session.execute(db.select(Department).filter_by(name=department.title())).scalar_one_or_none().department_id
    # Query only products that have inventory with quantity > 0
    products = db.session.execute(
        db.select(Product)
        .join(Inventory)  # Join Product with Inventory
        .filter(Product.department_id == department_id, Inventory.quantity > 0)
        .options(joinedload(Product.inventory))
    ).scalars().all()

    # Extract inventory quantities (avoid extra queries)
    inventory = [product.inventory.quantity for product in products]

    return render_template("department.html", department=department, inventory=inventory, products=products)


# Register new clients and emplyees into the Client/Employee database
@app.route('/register_user', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    title = "Register User"
    greeting = "Welcome to Rock Tools!"
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        document_id = form.document_id.data

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(BaseUser).where(BaseUser.email == email))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already registered with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        base_user = BaseUser(
            email=email,
            password=hash_and_salted_password,
        )
        db.session.add(base_user)
        db.session.commit()
        
        # Determine user type automatically based on email. New emplyees will be assigned code "00".
        # employees will have email address in the format initiallast_name@rocktools.com
        if re.match(r"^[a-zA-Z]+[a-zA-Z0-9]*@rocktools\.com$", email):

            clearance_code = "99" if db.session.execute(db.select(Employee)).scalar() is None else "00"
            employee = Employee(
                first_name=first_name,
                last_name=last_name,
                clearance_code=clearance_code,
                document_id=document_id,
                user=base_user,
            )
            db.session.add(employee)
            db.session.commit()
            login_user(base_user)
            return redirect(url_for("home"))
        
        else:
            client = Client(
                first_name=first_name,
                last_name=last_name,
                document_id=document_id,
                user=base_user,
            )
            db.session.add(client)
            db.session.commit()

            # Create a UserCart for the new client
            user_cart = UserCart(client_id=client.client_id)
            db.session.add(user_cart)
            db.session.commit()
            
            login_user(base_user)
            return redirect(url_for("home"))

    return render_template("forms.html", 
                           form=form, 
                           current_user=current_user, 
                           title=title, 
                           greeting=greeting)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.session.execute(db.select(BaseUser).filter_by(email=email)).scalar()
        # Email doesn't exist
        if not user:
            flash("This email does not exist, please try again or register.")
            return redirect(url_for('register'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
                login_user(user)
                return redirect(url_for("home"))
    return render_template("login.html", form=form, current_user=current_user)


# logout 
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# this route allows users adding their addresses
@app.route("/address", methods=["GET","POST"])
@login_required
def address():
    address = None

    # Check if user is a Client
    if current_user.client:
        address = db.session.execute(db.select(Address).filter_by(client_id=current_user.client.client_id)).scalar_one_or_none()

    # Check if user is an Employee
    elif current_user.employee:
        address = db.session.execute(db.select(Address).filter_by(employee_id=current_user.employee.employee_id)).scalar_one_or_none()

    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        if address:
            # Update existing address
            form.populate_obj(address)
            flash("Address updated successfully!", "success")
        else:
            # Create a new address entry
            new_address = Address(
                street=form.street.data,
                number=form.number.data,
                complement=form.complement.data,
                city=form.city.data,
                zip_code=form.zip_code.data,
                client_id=current_user.client.client_id if current_user.client else None,
                employee_id=current_user.employee.employee_id if current_user.employee else None,
            )
            db.session.add(new_address)
            flash("Address added successfully!", "success")

        # Commit the changes
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("forms.html", 
                        form=form, 
                        current_user=current_user, 
                        record_id=None,
                        table=None,
                        title="Register or Change your Address", 
                        greeting='Fill Data and Press "Add"')


# this route allows employees access to all system records, subject to their clearance codes
@app.route("/employees", methods=["GET", "POST"])
@login_required
@employee_required
def employees():
    # Define SQLAlchemy model mappings for dynamic querying
    model_mapping = {
        "employees": Employee,
        "departments": Department,
        "products": Product,
        "transactions": Transaction,
        "clients": Client,
        "inventory": Inventory,
    }

    # Default table to display when employee route selected
    table_name = request.args.get("table", "transactions")
    model = model_mapping.get(table_name)
    query_data = db.session.execute(db.select(model)).scalars().all()
    if query_data is None:
            return f"Error: Table not found in employees", 400

    # Handle dynamic table selection from POST requests providing access to other database information
    if request.method == "POST":
        table_name = request.form.get("table") 
        model = model_mapping.get(table_name)
        query_data = db.session.execute(db.select(model)).scalars().all()
   
    # Filter rows dynamically by ensuring only columns from the applicable table list are displayed
    filtered_rows = []
    for row in query_data:
        row_dict = row.__dict__.copy()
        row_dict.pop("_sa_instance_state", None)  # Remove SQLAlchemy metadata
        filtered_row = {key: value for key, value in row_dict.items() if key != 'password'}
        filtered_rows.append(filtered_row) # selects table's rows information
    # select column headers
    columns = list(filtered_rows[0].keys()) if filtered_rows else []
    # find primary key
    primary_key = get_primary_key(model)

    return render_template(
        "employees.html",
        table_title=table_name.capitalize(),
        table_name=table_name,
        columns=columns,
        rows=filtered_rows,
        primary_key=primary_key,
    )


# this route allows adding records
@app.route("/add_record/<table_name>", methods=["GET","POST"])
@login_required
@employee_required
def add_record(table_name):
    # Define SQLAlchemy model mappings for dynamic querying
    model_mapping = {
        "employees": Employee,
        "departments": Department,
        "products": Product,
        "transactions": Transaction,
        "clients": Client,
        "inventory": Inventory,
    }

    # Fetch the appropriate table dynamically
    model = model_mapping.get(table_name)
    if not model:
        return f"Error: Table not found in update_record", 400  # Handle invalid table requests
    
    # Determine form type based on the table
    form_mapping = {
        Employee: EmployeeForm,
        Client: ClientForm,
        Department: DepartmentForm,
        Product: ProductForm,
        Transaction: TransactionForm,
        Payment: PaymentForm,
    }

    form_class = form_mapping.get(model, None)
    if not form_class:
        return "Error: No matching form found", 400  # Handle missing forms
    
    form = form_class(request.form) if request.method == "POST" else form_class()

    if form.validate_on_submit():
        if table_name == "transactions":  
            new_transaction = Transaction(
                client_id=form.client_id.data,
                transaction_type=form.transaction_type.data,
                total_amount=0,  # Will update after adding items
                transaction_date=datetime.utcnow(),
            )
            db.session.add(new_transaction)
            db.session.flush()

            # Step 2: Create TransactionItem(s)
            product = db.session.get(Product, form.product_id.data)
            if not product:
                flash("Error: Selected product not found!", "danger")
                return redirect(url_for("add_record", table_name=table_name))

            new_transaction_item = TransactionItem(
                transaction_id=new_transaction.transaction_id,
                product_id=product.product_id,
                quantity=form.quantity.data,
                price=form.price.data,
            )
            db.session.add(new_transaction_item)

            # Step 3: Update total_amount in Transaction
            new_transaction.total_amount = new_transaction_item.quantity * new_transaction_item.price
            
            # Commit new transaction and transaction item
            db.session.commit()
            flash("Transaction added successfully!", "success")
            update_inventory(db.session, new_transaction)
            return redirect(url_for("employees", table=table_name))
        
        else:
            # Default behavior for other models
            new_record = model()
            form.populate_obj(new_record)
            db.session.add(new_record)
            db.session.commit()
            flash("Record added successfully!", "success")
            return redirect(url_for("employees", table=table_name))

    return render_template("forms.html", 
                           form=form, 
                           current_user=current_user, 
                           record_id=None,
                           table=table_name,
                           title="Create Record", 
                           greeting="Add and Submit!")


# this route allows record updates
@app.route("/update_record/<table>/<int:record_id>", methods=["GET", "POST"])
@login_required
@employee_required
def update_record(table, record_id):
    # Define SQLAlchemy model mappings
    model_mapping = {
        "employees": Employee,
        "departments": Department,
        "products": Product,
        "transactions": Transaction,
        "clients": Client,
        "inventory": Inventory,
    }

    # Fetch the appropriate table dynamically
    model = model_mapping.get(table)
    if not model:
        return f"Error: Table not found in update_record", 400  # Handle invalid table requests

    # find primary key
    primary_key = get_primary_key(model)
    record = db.session.execute(db.select(model).filter(getattr(model, primary_key) == record_id)).scalar()

    if current_user.employee.clearance_code != "99" and model == Employee:
        return "Access Denied: Only Admins can update clearance levels"
    
    # Determine form type based on the table
    form_mapping = {
        Employee: EmployeeForm,
        Client: ClientForm,
        Department: DepartmentForm,
        Product: ProductForm,
        Transaction: TransactionForm,
        Payment: PaymentForm,
        Inventory: InventoryForm,
    }

    form_class = form_mapping.get(model, None)
    if not form_class:
        return "Error: No matching form found", 400  # Handle missing forms
    
    if request.method == "POST":
        action = request.form.get("action")  # Determine which button was clicked

        if action == "update":
            form = form_class(request.form, obj=record)
            if form.validate_on_submit():
                form.populate_obj(record)
                db.session.commit()
                flash("Record updated successfully!", "success")
                return redirect(url_for("employees", table=table))

        elif action == "delete":
            db.session.execute(db.delete(TransactionItem).where(TransactionItem.transaction_id == record_id))
            db.session.delete(record)
            db.session.commit()
            flash("Record deleted successfully!", "danger")
            return redirect(url_for("employees", table=table))
        
        elif action == "cancel":
            flash("Record Unchanged!", "message")
            return redirect(url_for("employees", table=table))

    else:
        form = form_class(obj=record)  # Pre-populate form for GET requests
        if model == Transaction:
            complementary_data = db.session.execute(
            db.select(TransactionItem).where(getattr(TransactionItem, primary_key) == record_id)).scalar_one_or_none()
            if complementary_data:
                form.quantity.data = complementary_data.quantity
                form.price.data = complementary_data.price

    return render_template("forms.html", 
                           form=form, 
                           current_user=current_user, 
                           record_id=record_id,
                           table=table,
                           title="Update Record", 
                           greeting="Delete Record or Edit and Submit!")


@app.route("/cart", methods=["GET", "POST"])
@login_required
def view_cart():
    cart_id = db.session.execute(select(UserCart).filter_by(client_id=current_user.id)).scalar().cart_id
    cart_items = db.session.execute(select(CartItem).filter_by(cart_id=cart_id)).scalars().all()
    total = sum(item.quantity * item.price for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/remove_from_cart/<int:product_id>", methods=["GET", "POST"])
@login_required
def remove_from_cart(product_id):
    cart_id = db.session.execute(select(UserCart).filter_by(client_id=current_user.id)).scalar().cart_id
    item = db.session.execute(select(CartItem).where(CartItem.cart_id == cart_id).where(CartItem.product_id == product_id)).scalar_one_or_none()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('view_cart'))


@app.route("/add_to_cart/<department>/<int:product_id>", methods=["GET", "POST"])
@login_required
def add_to_cart(department, product_id):
    cart_id = db.session.execute(select(UserCart).filter_by(client_id=current_user.id)).scalar().cart_id
    quantity = request.form.get("quantity", type=int)
    if quantity == 0:
        flash("Invalid quantity selected.", "danger")
        return redirect(url_for("department_page", department=department))
    # Ensure the requested quantity does not exceed inventory
    inventory = db.session.execute(select(Inventory).filter_by(product_id=product_id)).scalar()
    if not inventory or inventory.quantity < quantity:
        flash("Insufficient stock available.", "danger")
        return render_template(url_for("department_page", department=department))
    
    product = db.session.execute(select(Product).filter_by(product_id=product_id)).scalar()
    price = product.price  
    description = product.description
    print(description, f'product_id = {product.product_id}')
    product_in_cart = db.session.execute(select(CartItem).where(CartItem.cart_id == cart_id).where(CartItem.product_id == product.product_id)).scalar()
    
    # add quantity if item already in cart
    if product_in_cart:
        print(product_in_cart.product_id)
        product_in_cart.quantity += quantity

    if not product_in_cart:
        new_cart_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity, price=price)
        db.session.add(new_cart_item)

    db.session.commit()
    flash(f"Item {description} added to cart!", "message")
    return redirect(url_for("department_page", department=department))


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    cart_id = db.session.execute(select(UserCart).filter_by(client_id=current_user.id)).scalar().cart_id
    cart_items = db.session.execute(select(CartItem).filter_by(cart_id=cart_id)).scalars().all()

    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for("view_cart"))
    
    # create cart item list
    line_items = []
    for item in cart_items:
        product = db.session.execute(select(Product).filter_by(product_id=item.product_id)).scalar()
        stripe_price_code = product.stripe_price_code
        checkout_product = {
            'price': stripe_price_code,
            'quantity': item.quantity,
        }
        line_items.append(checkout_product)

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url = f"{YOUR_DOMAIN}/",
            cancel_url = f"{YOUR_DOMAIN}/",
        )
        update_database(cart_id, cart_items)
    except Exception as e:
        return str(e)

    flash("Checkout successful!", "success")
    return redirect(checkout_session.url, code=303)


def update_database(cart_id, cart_items):
    total_amount = sum(item.quantity * item.price for item in cart_items)

    # Create a new transaction
    new_transaction = Transaction(
        client_id=current_user.id,
        transaction_type="sell",  # from the store point of view
        total_amount=total_amount,
        transaction_date=datetime.utcnow()
    )
    db.session.add(new_transaction)
    db.session.flush()

    # Move cart items to TransactionItem
    for item in cart_items:
        transaction_item = TransactionItem(
            transaction_id=new_transaction.transaction_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.session.add(transaction_item)
        db.session.flush()

        # Reduce inventory stock
        inventory = db.session.get(Inventory, item.product_id)
        inventory.quantity -= item.quantity

    # Commit all changes
    db.session.commit()

    # Clear the cart after successful checkout
    db.session.execute(db.delete(CartItem).where(CartItem.cart_id == cart_id))
    db.session.commit()


# adds product purchase to inventory
def update_inventory(session, transaction):
    """ Updates inventory after a purchase (buy transaction). """
    # Fetch TransactionItems related to this Transaction
    transaction_items = session.execute(select(TransactionItem).filter_by(transaction_id=transaction.transaction_id)).scalars().all()
    print(f't_items={transaction_items}')

    for item in transaction_items:
        # Fetch Inventory entry for this product
        inventory = db.session.execute(select(Inventory).filter_by(product_id=item.product_id)).scalar()

    if transaction.transaction_type == "buy":
        print(f'Processing inventory update for transaction {transaction.transaction_id}')
        if inventory:
            # Update inventory quantity
            inventory.quantity += item.quantity 
            inventory.last_updated = datetime.utcnow()
            print("inventory updated")
        else:
            # Insert new inventory entry
            new_inventory = Inventory(
                product_id=item.product_id,
                quantity=item.quantity,
                acquired_date=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            session.add(new_inventory)
            print("new inventory item added")
        session.commit()

    elif transaction.transaction_type == "sell":
        print(f'Processing inventory update for transaction {transaction.transaction_id}')
        if inventory:
            # Update inventory quantity
            if inventory.quantity >= item.quantity:
                inventory.quantity -= item.quantity 
                inventory.last_updated = datetime.utcnow()
                session.commit()
                print("inventory updated")
        else:
            product_id = transaction.transaction_items.product_id
            product_description = session.execute(select(Product).filter_by(product_id=product_id)).scalar().description
            flash(f"Not enough stock for {product_description}.", "danger")
            return redirect(url_for("view_cart"))
        

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
    csrf.init_app(app)