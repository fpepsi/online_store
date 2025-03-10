from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, URLField, IntegerField, DecimalField, SelectField
from wtforms.validators import DataRequired, URL, Regexp, Length, Email, NumberRange
from database import db, Product, Client, Department, Inventory
from sqlalchemy import select
from flask_login import current_user    

# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired(message='Password too long'), Length(max=100)])
    first_name = StringField("First Name", validators=[DataRequired(message='Name too long'), Length(max=20)])
    last_name = StringField("Last Name", validators=[DataRequired(message='Name too long'), Length(max=50)])
    document_id = StringField("Driver's License", validators=[Length(max=50)])
    submit = SubmitField("Register")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(message='Password too long')])
    submit = SubmitField("Log In")


# Create a form to update employee data
class EmployeeForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(message='Name too long'), Length(max=20)])
    last_name = StringField("Last Name", validators=[DataRequired(message='Name too long'), Length(max=50)])
    document_id = StringField("Document ID", validators=[Length(max=50, message='id too long')])
    job_title = StringField("Job Title", validators=[Length(max=100, message='id too long')])
    clearance_code = StringField("Clearance Code", validators=[DataRequired(), Length(max=2, message='id too long')])


# Create a form to update client data
class ClientForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(message='Name too long'), Length(max=20)])
    last_name = StringField("Last Name", validators=[DataRequired(message='Name too long'), Length(max=50)])
    document_id = StringField("Document ID")    


# create a form to update addresses
class AddressForm(FlaskForm):
    street = StringField("Street", validators=[Length(max=255)])
    number = StringField("Number", validators=[Length(max=20)])
    complement = StringField("Complement", validators=[Length(max=100)])
    city = StringField("City", validators=[Length(max=100)])
    zip_code = StringField('Zip Code', validators=[DataRequired(message='Invalid zip code format'), Regexp(r'^\d{5}(-\d{4})?$')])


# create a form to update products
class ProductForm(FlaskForm):
    description = StringField("Description", validators=[DataRequired()])
    brand = StringField("Brand", validators=[DataRequired()])
    website_url = URLField("Website Address", validators=[DataRequired(), URL()])
    image_url = StringField("Image", validators=[DataRequired()])
    price = DecimalField("Price (USD)", validators=[DataRequired()])
    cost = DecimalField("Cost (USD)", validators=[DataRequired()])
    department_id = SelectField(
        "Department",
        validators=[DataRequired()],
    )
    product_family = StringField("Family")
    stripe_product_code = StringField("Stripe Prod ID")
    stripe_price_code = StringField("Stripe Price ID")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(c.department_id, f"{c.name}") for c in db.session.scalars(select(Department)).all()]


# create a form to update departments
class DepartmentForm(FlaskForm):
    name = StringField("Description", validators=[DataRequired()])


# create a form to update transactions
class TransactionForm(FlaskForm):
    """Form for creating or updating transactions."""
    client_id = SelectField("Client", validators=[DataRequired()], coerce=int)
    product_id = SelectField("Product", validators=[DataRequired()], coerce=int)
    transaction_type = SelectField("Buy or Sell", choices=[("buy", "Buy"), ("sell", "Sell")])
    department_id = SelectField("Department", coerce=int)
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=0)])
    price = DecimalField("Price", validators=[DataRequired(), NumberRange(min=0)])
    payment_method = SelectField(
        "Payment Method",
        choices=[("cash", "Cash"), ("credit_card", "Credit Card"), ("bank_transfer", "Bank Transfer")],
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id.choices = [(c.client_id, f"{c.first_name} {c.last_name}") for c in db.session.scalars(select(Client)).all()]
        self.product_id.choices = [(p.product_id, p.description) for p in db.session.scalars(select(Product)).all()]
        if current_user.is_authenticated and current_user.employee:self.department_id.choices = [(d.department_id, d.name) 
                                          for d in db.session.scalars(select(Department)).all()]
        else:
            self.department_id.choices = []  # Hide department selection for non-employees


# create a form to update payments
class PaymentForm(FlaskForm):
    payment_type = StringField("Credit Card, Cash, or Bank Transfer", validators=[Length(max=20)])
    amount = DecimalField("Cost (USD)", validators=[DataRequired()])
    card_brand = StringField("Visa, Amex or Mastercard", validators=[Length(max=50)])
    expiration_date = StringField("mm/yy", validators=[Length(max=5)])
    card_holder = StringField("First Name", validators=[DataRequired(message='Name too long'), Length(max=100)])


# create a form to update inventory
class InventoryForm(FlaskForm):
    product_id = SelectField(
        "Product",
        validators=[DataRequired()],
    )
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=0)])
    department = StringField("Department", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_id.choices = [(c.product_id, f"{c.product.description}") for c in db.session.scalars(select(Inventory)).all()]

        


