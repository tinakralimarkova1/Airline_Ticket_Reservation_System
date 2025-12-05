from flask import Flask, render_template, request, url_for, redirect, session
import mysql.connector
from datetime import date

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
def get_db_connection():
	return mysql.connector.connect(
		host='localhost',
        user='root',
        password='',
        database='Airline_Reservation_System')

## helper functions for agent
def require_agent(): 
    if session.get('user_type') != 'agent': 
        # redirect if not an agent to 
        return redirect(url_for('login_agent'))
    return None 

def normalize_date(value):
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return value

#Define a route to hello function
@app.route('/')
def hello():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT operated_by, flight_num, departure_time, arrival_time, status_, arrives, departs
        FROM flight
        WHERE status_ = 'upcoming'
    """
    cursor.execute(query)
    data1 = cursor.fetchall()

    cursor.close()
    conn.close()

   
    return render_template('index.html', data=data1)


@app.route('/logUser', methods=['GET', 'POST'])
def select_role():
#When user selects a button, it is registered here and redirects to the appropriate route
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'customer':
            return redirect(url_for('login_cust'))
        elif role == 'booking_agent':
            return redirect(url_for('login_agent'))
        elif role == 'airline_staff':
            return redirect(url_for('login_staff'))
        else:
            return "Invalid role selected", 400
	
    #if request is GET
    return render_template('logUser.html')


#Define routes for login
@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/login_cust', methods=['GET', 'POST'])
def login_cust():
    if request.method == 'POST':

        #user input 
        username = request.form['username']
        password = request.form['password']

        #connect to dp
        conn = get_db_connection()
        cursor = conn.cursor()

        #query and fetching data
        query = "SELECT email, password FROM Customer WHERE email = %s and password = %s"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()


        #if data is found, username exists 
        if data:
            session['username'] = username
            session['user_type'] = 'customer'
            return redirect(url_for('customer_home'))
        else:
            error = 'Invalid login or username'
            return render_template('login_cust.html', error=error)

    return render_template('loginCust.html')
@app.route('/login_agent', methods=['GET', 'POST'])
def login_agent():
    if request.method == 'POST':

        #user input 
        username = request.form['username']
        password = request.form['password']

        #connect to dp
        conn = get_db_connection()
        cursor = conn.cursor()

        #query and fetching data
        query = "SELECT email, password FROM booking_agent WHERE email = %s and password = %s"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()

        #if data is found, username exists 
        if data:
            session['username'] = username
            session['user_type'] = 'agent'
            session['agent_email'] = username # for agent pages 
            return redirect(url_for('agent_home'))
        else:
            error = 'Invalid login or username'
            return render_template('login_agent.html', error=error)
    
    return render_template('loginAgent.html')

@app.route('/login_staff', methods=['GET', 'POST'])
def login_staff():
    if request.method == 'POST':

        #user input 
        username = request.form['username']
        password = request.form['password']

        #connect to dp
        conn = get_db_connection()
        cursor = conn.cursor()

        #query and fetching data
        query = "SELECT username, password FROM airline_staff WHERE username = %s and password = %s"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()


        #if data is found, username exists 
        if data:
            session['username'] = username
            session['user_type'] = 'staff'
            return redirect(url_for('staff_home'))
        else:
            error = 'Invalid login or username'
            return render_template('loginStaff.html', error=error)
    return render_template('loginStaff.html')

#Register routes 

@app.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

@app.route('/regUser', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
          role = request.form.get('role')
          if role == 'customer':
              return redirect(url_for('register_customer'))
          elif role == 'booking_agent':
              return redirect(url_for('register_agent'))
          elif role == 'airline_staff':
              return redirect(url_for('register_staff'))
          else:
              return "Invalid role selected", 400

    return render_template('register.html')


@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        building_number = request.form.get('building_number')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        phone_number = request.form.get('phone_number')
        passport_number = request.form.get('passport_number')
        passport_expiration_date = request.form.get('passport_expiration_date')
        passport_country = request.form.get('passport_country')
        date_of_birth = request.form.get('date_of_birth')

        if not all([email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration_date, passport_country, date_of_birth]):
            error = "All fields are required"
            return render_template('registerCust.html', error=error)
    


        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT email FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        data = cursor.fetchone()

        if data:
            error = "This email is already in use"
            return render_template('registerCust.html', error=error)
        else:
            # Insert the new customer record
            query = """INSERT INTO customer (email,name,password, building_number, street, city, state, phone_number, passport_number, passport_expiration_date, passport_country, date_of_birth) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration_date, passport_country, date_of_birth))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('login_cust'))  




    return render_template('registerCust.html')

@app.route('/register_agent', methods=['GET', 'POST'])
def register_agent():
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            error = "All fields are required"
            return render_template('registerAgent.html', error=error)
    
        conn = get_db_connection()
        cursor = conn.cursor()

        # check if email already exists 
        query = "SELECT email FROM booking_agent WHERE email = %s"
        cursor.execute(query, (email,))
        data = cursor.fetchone()

        if data:
            error = "This email is already in use"
            cursor.close()
            conn.close() 
            return render_template('registerAgent.html', error=error)
        else:
            # insert new agent record 
            query = """INSERT INTO booking_agent (email,password) 
                       VALUES (%s, %s)"""
            cursor.execute(query, (email, password))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('login_agent'))
    return render_template('registerAgent.html')


@app.route('/register_staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')


        if not all([username, password, first_name, last_name, date_of_birth]):
            error = "All fields are required"
            return render_template('registerStaff.html', error=error)
    


        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT username FROM airline_staff WHERE username = %s"
        cursor.execute(query, (username,))
        data = cursor.fetchone()

        if data:
            error = "This username is already in use"
            return render_template('registerStaff.html', error=error)
        else:
            # Insert the new customer record
            query = """INSERT INTO airline_staff (username,password, first_name, last_name, date_of_birth) 
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (username, password, first_name, last_name, date_of_birth))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('login_staff'))

    return render_template('registerStaff.html')

#customer 

@app.route('/customer_home')
def customer_home():
    return render_template('indexCust.html')


######## booking agent pages ##########

## 1. agent home page 
@app.route('/agent_home')
def agent_home():
    # only accessable if logged in as an agent already 
    redirect_or_none = require_agent()
    if redirect_or_none:
        return redirect_or_none
    
    return render_template('indexAgent.html')

# 2. show flights that booking agent has prchased for a customer
@app.route('/agent_flights')
def agent_flights():
    redirect_or_none = require_agent()
    if redirect_or_none: 
        return redirect_or_none 
    
    agent_email = session.get('agent_email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # read filters (date ranges and routes)
    from_airport = request.args.get('from_airport') or None
    to_airport   = request.args.get('to_airport') or None
    start_date   = request.args.get('start_date') or None
    end_date     = request.args.get('end_date') or None

    viewpur_query = """
        SELECT f.flight_num, f.operated_by AS airline_name, f.departs, f.departure_date, 
               f.departure_time, f.arrives, f.arrival_date, f.arrival_time, f.price, f.status_, 
               f.use_ AS airplane_id, p.customer_email, p.date
        FROM flight as f, ticket as t, purchases as p 
        WHERE p.booking_agent_email = %s AND p.ticket_id = t.ticket_id AND t.for_= f.flight_num 
    """

    params = [agent_email]

    if from_airport:
        viewpur_query += " AND f.departs = %s"
        params.append(from_airport)

    if to_airport:
        viewpur_query += " AND f.arrives = %s"
        params.append(to_airport)

    if start_date:
        viewpur_query += " AND f.departure_date >= %s"
        params.append(start_date)

    if end_date:
        viewpur_query += " AND f.departure_date <= %s"
        params.append(end_date)

    viewpur_query += " ORDER BY p.date DESC"

    cursor.execute(viewpur_query, tuple(params))
    flights = cursor.fetchall()

    cursor.close()
    conn.close() 

    return render_template('agentFlights.html', flights=flights, from_airport=from_airport,to_airport=to_airport,start_date=normalize_date(start_date),end_date=normalize_date(end_date))

# 3. search for flights and purchase tickets for customers 
@app.route('/agent_search', methods=['GET', 'POST'])
def agent_search():
    
    redirect_or_none = require_agent()
    if redirect_or_none:
        return redirect_or_none
    
    agent_email = session.get('agent_email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    message = None
    error = None

    # 3.1 ticket purchasing 
    if request.method == 'POST' and request.form.get('purchase_flight_num'):
        flight_num = request.form.get('purchase_flight_num')
        customer_email = request.form.get('customer_email')

        # check if agent is allowed to represent airline 
        authorization_query = """
            SELECT 1 
            FROM flight as f JOIN authorized_by as auth ON f.operated_by = auth.airline_name
            WHERE auth.booking_agent_email = %s AND f.flight_num = %s        
        """
        cursor.execute(authorization_query, (agent_email, flight_num))
        authorized = cursor.fetchone()

        if authorized:
            # find existing ticket for this flight that has NOT been purchased yet 
            availtix_query = """
                SELECT t.ticket_id
                FROM ticket as t
                WHERE t.for_ = %s AND t.ticket_id NOT IN (SELECT p.ticket_id FROM purchases AS p)
            """
            cursor.execute(availtix_query, (flight_num,))
            row = cursor.fetchone()

            if not row:
                error = "Sorry, there are no available tickets left for this flight"
            else:
                ticket_id = row['ticket_id']
                
                # insert into purchases
                insert_purchase = """
                    INSERT INTO purchases (ticket_id, customer_email, booking_agent_email, date)
                    VALUES (%s, %s, %s, CURDATE())
                """
                cursor.execute(insert_purchase, (ticket_id, customer_email, agent_email))
                conn.commit()
                message = (
                    f"Ticket #{ticket_id}, Flight {flight_num} has been purchased for "
                    f"{customer_email}."
                )
        else:
            error = "You are not allowed to book flights for this airline"

    # 3.2 flight search 

    # read filters 
    departure_airport = request.args.get('departure_airport') or None
    arrival_airport = request.args.get('arrival_airport') or None
    departure_date = request.args.get('departure_date') or None

    search_query = """
        SELECT f.flight_num, f.operated_by as airline_name, f.departs, f.departure_date, 
               f.departure_time, f.arrives, f.arrival_date, f.arrival_time,
               f.price, f.status_, f.use_ as airplane_id
        FROM flight as f JOIN ticket as t ON t.for_ = f.flight_num
        WHERE t.ticket_id NOT IN (SELECT p.ticket_id FROM purchases as p)
    """
    
    params = []
    
    if departure_airport:
        search_query += " AND f.departs = %s"
        params.append(departure_airport)

    if arrival_airport:
        search_query += " AND f.arrives = %s"
        params.append(arrival_airport)

    if departure_date:
        search_query += " AND f.departure_date = %s"
        params.append(departure_date)

    search_query += "ORDER BY f.departure_date, f.departure_time"

    cursor.execute(search_query, tuple(params))
    flights = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('agentSearch.html', flights=flights, departure_airport=departure_airport, arrival_airport=arrival_airport, departure_date=normalize_date(departure_date), message=message, error=error)

# 4. access analytics 
@app.route('/agent_analytics')
def agent_analytics(): 
    
    redirect_or_none = require_agent()
    if redirect_or_none:
        return redirect_or_none
    

    return render_template('agentAnalytics.html')  

#airline staff

@app.route('/staff_home')
def staff_home():
    return render_template('indexStaff.html')


#logout

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

	
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
