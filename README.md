# online_store
prototype of a small online business

Store functionality description:

This is an online store that sells musical instruments. Clients and employees have to register and login before they can buy products or manage store inventories.

The BaseUser class instance holds the users email and password, and the client or employee details are stored respectively in the Client and Employee class instances. I also created an Address class instance to hold all users' addresses.

The employees must create and setup each product by filling out the Product class instance. The employee must then create transactions of transaction_type “buy” in order to acquire new products for the store. A transaction may have one or more transaction items, each of which must be itemized in the TransactionItem class instance. A payment_type (credit card, check, cash…) must be selected and details of such payment must be stored in the Payment class instance. 

Once the transaction is added to the database, the transaction items must be moved to inventory, a department must be added to the product in order to track its location, and the cash or credit total amount should be populated and stored accordingly.

Finally, the client should select items to purchase, the cart_items stored in CartItem class instance, and those must be added together  under the UserCart class instance. After the client selects the checkout option, the cart items must be used to populate the TransactionItem, and payment methods should be filled.

When the transaction is paid by the client, the products should automatically be updated in the inventory and transaction, and the cart be emptied from the CartImes.

@app.route(“/“) - home() 
    —> displays a list of links to the various departments registered under Department class instance, hyperlink to @app.route(“/login”) - login(), and hyperlink to @app.route(“/register_user”) - register() 
    —> if an employee is logged in, he sees additional hyperlinks to “Orders” and “Employees”
    —> if a client is logged in, he sees additional hyperlinks to “Orders” and “User Profile”

@app.route(“/department/<department>”) - department_page()
    —> queries Product and Inventory databases for all products of a certain Department

@app.route(“/register_user”) - register() 
    —> allows clients and employees to register. This should be the only route to allow user registration. Upon successful registration, redirect to login() route.

@app.route(“/login”) - login() 
    —> if credentials are correct, logs use in and redirects back to home() page.

@app.route(“/logout”) - logout()
    —> lets user checkout from session

@app.route(“/address”) - address()
    —> this route is available to any registered user and allows the user to add or edit his/her address from the database

@app.route(“/employees”) - employees()
    —> access to a page wcontaining hyperlinks on the left side, and a table view on the right side. The hyperlinks load the tables stored in the app sqlalchemy database on the right side of the page
    —> the hyperlinks provide access to tables “employees”, “departments”, “products”, “transactions”, “clients”, “inventory”
    —> Once the hyperlink is clicked upon by user, the app queries the data and displays it on the right side. For tables which are not “clients” or employees”, a button “Add New Record” will also be displayed, allowing user to load a new form object and add a new record. Remember, “clients” and “employees” must be added via the “register” route.
    —> When a table is loaded, user can double click on any record and it will be loaded up on a form. The user can then delete or modify the record.

@app.route("/add_record/<table_name>”) - add_record()
    —> Allows employees, subject to certain clearance codes, to add new departments, products, or transactions. Employees, clients and respective addresses must be added via register or login routes.  

@app.route("/update_record/<table>/<int:record_id>”) - update_record()
    —> available only to employees. The page display a list of all database tables for consultation, and if user double clicks on a record, the respective form shows up and user can modify the record (except for employees, clients, and inventory tables, which are restricted for any employee without a 99 clearance code)		

@app.route("/cart") - view_cart()
    —> shows cart with selected items

@app.route("/remove_from_cart/<int:product_id>”) - remove_from_cart(product_id)
    —>  removes item from cart when button is pressed 

@app.route("/add_to_cart/<department>/<int:product_id>”) - add_to_cart(department, product_id)
    —> add items to cart upon selecting a quantity and pressing the button

@app.route('/create-checkout-session') - create_checkout_session()
    —> strip API route https://docs.stripe.com/testing
