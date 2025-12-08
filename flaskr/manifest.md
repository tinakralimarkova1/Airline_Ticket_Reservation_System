### File Manifest

- `flaskr/__init__.py`  
  Main Flask application. Defines routes for all three roles (Customer, Booking Agent, Airline Staff), database connection helper, and core business logic (search, purchase, analytics, staff views, etc.).

- `flaskr/__init__.py: get_db_connection()`  
  Helper function that opens a MySQL connection to the `Airline_Reservation_System` database. Used by all routes that query or modify data.

- `templates/index.html`  
  Public homepage that lists upcoming flights and provides navigation to login / register pages.

---

## Log In

- `templates/login.html`  
  “Select Role” page where users choose to log in as Customer, Booking Agent, or Airline Staff.

- `templates/loginCustomer.html`  
  Login form for customers (email + password), with error display if authentication fails.

- `templates/loginAgent.html`  
  Booking Agent login page containing a simple username/password form and error message block.

- `templates/loginStaff.html`  
  Airline Staff login page. Verifies staff credentials tied to a specific airline.

---

## Registration

- `templates/register.html`  
  “Select Role” page where users choose to register as Customer, Booking Agent, or Airline Staff.

- `templates/registerCustomer.html`  
  Form for creating a customer account (email, name, password, address, phone, passport data, date of birth). Displays validation errors and success messages.

- `templates/registerAgent.html`  
  Registration page for booking agents (username, password). Includes form validation and error feedback.

- `templates/registerStaff.html`  
  Allows creation of a new airline staff account (username, password, first/last name, date of birth, airline they work for). Includes validation.

---

## Customer

- `templates/indexCust.html`  
  Customer homepage. Displays available flights with filtering options and includes two buttons linking to the Spending page and Purchases page.

- `templates/spendingCust.html`  
  Spending dashboard for customers. Shows total spending in the last 12 months and includes bar graphs for the last 6 months. Date filtering allows viewing spending over custom ranges.

- `templates/purchasedCust.html`  
  Page displaying two tables: one for upcoming flights, and one for all previously purchased flights. Both tables support filtering.

- `templates/buyCust.html`  
  Purchase confirmation page. After the customer selects a flight, this page shows the flight details and provides the button to finalize the ticket purchase.

---

## Booking Agent

- `templates/indexAgent.html`  
  Displays all tickets sold by the agent. Usually sorted by purchase date and includes customer email, flight details, and price.

- `templates/agentSearch.html`  
  Booking Agent flight search interface. Lists all flights not yet fully booked, allows filtering by date/origin/destination, and enables agents to initiate purchases on behalf of customers.

- `templates/agentFlights.html`  
  Displays all tickets sold by the agent. Usually sorted by purchase date and includes customer email, flight details, and price.

- `templates/agentAnalytics.html`  
  Analytics dashboard showing total commission in the last 30 days, average commission per ticket, and bar charts for identifying top customers within defined windows.

---

## Airline Staff





