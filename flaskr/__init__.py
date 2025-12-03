from flask import Flask, render_template, request, url_for, redirect, session
import mysql.connector

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
def get_db_connection():
	return mysql.connector.connect(
		host='localhost',
        user='root',
        password='',
        database='Airline_Reservation_System')


#Define a route to hello function
@app.route('/', methods=['GET'])
def index():
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '').strip()
    time = request.args.get('time', '').strip()

    # fields for status lookup
    status_airline = request.args.get('status_airline', '').strip()
    status_flight = request.args.get('status_flight', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query: all upcoming flights from the flight table only
    query = """
        SELECT
            operated_by,      -- 0: Airline Name
            flight_num,       -- 1: Flight Number
            departure_date,   -- 2: Departure Date
            departure_time,   -- 3: Departure Time
            arrival_date,     -- 4: Arrival Date
            arrival_time,     -- 5: Arrival Time
            status_,          -- 6: Status
            arrives,          -- 7: Arrival Airport Code
            departs           -- 8: Departure Airport Code
        FROM flight AS f
        LEFT JOIN airport AS dep_airport
            ON f.departs = dep_airport.name      -- dep airport code → airport row
        LEFT JOIN airport AS arr_airport
            ON f.arrives = arr_airport.name      -- arr airport code → airport row
        WHERE
            f.status_ = 'upcoming'
    """
    params = []

    # Origin filter: match origin airport code OR origin city
    if origin:
        query += " AND (f.departs LIKE %s OR dep_airport.host LIKE %s)"
        like_origin = f"%{origin}%"
        params.extend([like_origin, like_origin])

    # Destination filter: match destination airport code OR destination city
    if destination:
        query += " AND (f.arrives LIKE %s OR arr_airport.host LIKE %s)"
        like_dest = f"%{destination}%"
        params.extend([like_dest, like_dest])

    # Date filter: exact departure date
    if date:
        query += " AND f.departure_date = %s"
        params.append(date)  # 'YYYY-MM-DD'

    # Time filter: departure_time >= selected time
    if time:
        query += " AND f.departure_time >= %s"
        params.append(time)  # 'HH:MM'

    cursor.execute(query, tuple(params))
    data = cursor.fetchall()


    query2 = """
        SELECT
            operated_by,      -- 0: Airline Name
            flight_num,       -- 1: Flight Number
            departure_date,   -- 2: Departure Date
            departure_time,   -- 3: Departure Time
            arrival_date,     -- 4: Arrival Date
            arrival_time,     -- 5: Arrival Time
            status_,          -- 6: Status
            arrives,          -- 7: Arrival Airport Code
            departs           -- 8: Departure Airport Code
        FROM flight AS f
        WHERE
            f.status_ = 'in_progress'
        """
    
    status_params = []
    
    if status_airline:
        query2 += " AND f.operated_by = %s"
        status_params.append(status_airline)

    if status_flight:
        query2 += " AND f.flight_num = %s"
        status_params.append(status_flight)

    cursor.execute(query2, tuple(status_params))
    data1 = cursor.fetchall()

    

    cursor.close()
    conn.close()

    return render_template('index.html', data=data, data1=data1)



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
	
    #if request if GET
    return render_template('logUser.html')


#Define route for login
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
        query = "SELECT name, email, password FROM Customer WHERE email = %s and password = SHA2(%s, 256)"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()


        #if data is found, username exists 
        if data:
            session['username'] = username
            session['name'] = data[0]
            return redirect(url_for('customer_home'))
        else:
            error = 'Invalid login or username'
            return render_template('loginCust.html', error=error)

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
        query = "SELECT email, password FROM booking_agent WHERE email = %s and password = SHA2(%s, 256)"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()


        #if data is found, username exists 
        if data:
            session['username'] = username
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
        query = "SELECT username, password FROM airline_staff WHERE username = %s and password = SHA2(%s, 256)"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()


        #if data is found, username exists 
        if data:
            session['username'] = username
            return redirect(url_for('staff_home'))
        else:
            error = 'Invalid login or username'
            return render_template('loginStaff.html', error=error)
    return render_template('loginStaff.html')

#register

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
                       VALUES (%s, %s, SHA2(%s, 256), %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
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

        query = "SELECT email FROM booking_agent WHERE email = %s"
        cursor.execute(query, (email,))
        data = cursor.fetchone()

        if data:
            error = "This email is already in use"
            return render_template('registerAgent.html', error=error)
        else:
            # Insert the new customer record
            query = """INSERT INTO booking_agent (email,password) 
                       VALUES (%s, SHA2(%s, 256))"""
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
                       VALUES (%s, SHA2(%s, 256), %s, %s, %s)"""
            cursor.execute(query, (username, password, first_name, last_name, date_of_birth))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('login_staff'))

    return render_template('registerStaff.html')

#customer 

@app.route('/customer_home', methods=['GET'])
def customer_home():
    if 'username' not in session:
        return redirect(url_for('login_cust'))

    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '').strip()
    time = request.args.get('time', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            operated_by,      -- 0: Airline Name
            flight_num,       -- 1: Flight Number
            departure_date,   -- 2: Departure Date
            departure_time,   -- 3: Departure Time
            arrival_date,     -- 4: Arrival Date
            arrival_time,     -- 5: Arrival Time
            status_,          -- 6: Status
            arrives,          -- 7: Arrival Airport Code
            departs           -- 8: Departure Airport Code
        FROM flight AS f
        LEFT JOIN airport AS dep_airport
            ON f.departs = dep_airport.name
        LEFT JOIN airport AS arr_airport
            ON f.arrives = arr_airport.name
        WHERE
            f.status_ = 'upcoming'
    """
    params = []

    if origin:
        query += " AND (f.departs LIKE %s OR dep_airport.host LIKE %s)"
        like_origin = f"%{origin}%"
        params.extend([like_origin, like_origin])

    if destination:
        query += " AND (f.arrives LIKE %s OR arr_airport.host LIKE %s)"
        like_dest = f"%{destination}%"
        params.extend([like_dest, like_dest])

    if date:
        query += " AND f.departure_date = %s"
        params.append(date)

    if time:
        query += " AND f.departure_time >= %s"
        params.append(time)

    cursor.execute(query, tuple(params))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'indexCust.html',
        name=session.get('name'),
        data=data
    )

@app.route('/buy_cust', methods=['GET', 'POST'])
def buy_cust():
    # Must be logged in
    if 'username' not in session:
        return redirect(url_for('login_cust'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)   # dictionary=True gives column names

    # ---------------------------------
    # GET → Show the purchase page
    # ---------------------------------
    if request.method == 'GET':
        flight_num = request.args.get('flight_num')

        # Fetch flight details
        query = """
            SELECT *
            FROM flight
            WHERE flight_num = %s
        """
        cursor.execute(query, (flight_num,))
        flight = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template("buyCust.html", 
                               flight=flight,
                               customer_email=session['username'])

    # ---------------------------------
    # POST → Insert purchase into table
    # ---------------------------------
    if request.method == 'POST':
        customer_email = session['username']
        agent_email = request.form.get('agent_email') or None
        ticket_id = request.form.get('ticket_id')
        purchase_date = request.form.get('purchase_date')
        flight_num = request.form.get('flight_num')

        # Insert into purchases
        insert_query = """
            INSERT INTO purchases (customer_email, booking_agent_email, ticket_id, date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, 
                       (customer_email, agent_email, ticket_id, purchase_date))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('customer_home'))


@app.route('/spendingCust', methods=['GET'])
def customer_spending():
    # Later: query DB for this customer's spending
    return render_template('spendingCust.html')

@app.route('/purchasesCust', methods=['GET'])
def customer_purchases():
    # Later: query DB for this customer's purchased flights
    return render_template('purchasedCust.html')




#booking agent

@app.route('/agent_home')
def agent_home():
    
    
    return render_template('indexAgent.html')

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
