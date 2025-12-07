from flask import Flask, render_template, request, url_for, redirect, session
import mysql.connector
from datetime import date, datetime

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

@app.after_request
def add_no_cache_headers(response):
    """
    Prevent caching so that back/forward buttons do not show
    logged-in pages after logout.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def require_agent(): 
    if session.get('user_type') != 'agent': 
        # redirect if not an agent to 
        return redirect(url_for('login_agent'))
    return None 



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
        query = "SELECT name, email, password FROM Customer WHERE email = %s and password = SHA2(%s, 256)"
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
            session['user_type'] = 'agent'
            session['agent_email'] = username # for agent pages 
            return redirect(url_for('agent_home'))
        else:
            error = 'Invalid login or username'
            return render_template('loginAgent.html', error=error)
    
    return render_template('loginAgent.html')

@app.route('/login_staff', methods=['GET', 'POST'])
def login_staff():
    if request.method == 'POST':

        #user input 
        username = request.form['username']
        password = request.form['password']

        #connect to db
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #query and fetching data
        query = "SELECT username, password, works_for, permissions FROM airline_staff WHERE username = %s and password = SHA2(%s, 256)"
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        cursor.close()
        conn.close()

        #if data is found, username exists 
        if data:
            session['username'] = data['username']
            session['airline'] = data['works_for']
            session['permissions'] = data['permissions']
            
            # redirect staff depending on role 
            if data['permissions'] == 'admin': 
                return redirect(url_for('admin_home'))
            else:
                return redirect(url_for('operator_home'))
        return render_template('loginStaff.html', error = "Invalid credentials")
    
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
        if type(building_number) != int:
            error = "Building number must be an integer"
            return render_template('registerCust.html', error=error)
        
        if type(phone_number) != int:
            error = "Phone number must be an integer"
            return render_template('registerCust.html', error=error)
        
        if type(passport_number) != int:
            error = "Passport number must be an integer"
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
        works_for = request.form.get('works_for')
        permissions = request.form.get('permissions')

        # validate input
        if not all([username, password, first_name, last_name, date_of_birth, works_for, permissions]):
            error = "All fields are required"
            return render_template('registerStaff.html', error=error)
        
        if permissions not in ['admin', 'operator']:
            error = "Invalid permissions selected"
            return render_template('registerStaff.html', error=error)
        
        if date_of_birth:
            try:
                datetime.strptime(date_of_birth, '%Y-%m-%d')
            except ValueError:
                error = "Invalid date of birth format"
                return render_template('registerStaff.html', error=error)
            
        
    


        conn = get_db_connection()
        cursor = conn.cursor()

        # check if airline exists
        check_airline_query = "SELECT name FROM airline WHERE name = %s"
        cursor.execute(check_airline_query, (works_for,))
        airline_data = cursor.fetchone()

        if not airline_data:
            error = "Invalid airline name"
            return render_template('registerStaff.html', error=error)
        
        # check if username already exists

        query = "SELECT username FROM airline_staff WHERE username = %s"
        cursor.execute(query, (username,))
        data = cursor.fetchone()

        if data:
            error = "This username is already in use"
            return render_template('registerStaff.html', error=error)
        else:
            # Insert the new customer record
            query = """INSERT INTO airline_staff (username,password, first_name, last_name, date_of_birth, permissions, works_for) 
                       VALUES (%s, SHA2(%s, 256), %s, %s, %s, %s, %s)"""
            cursor.execute(query, (username, password, first_name, last_name, date_of_birth, permissions, works_for))
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
        f.operated_by,          -- 0: Airline Name
        f.flight_num,           -- 1: Flight Number
        f.departure_date,       -- 2: Departure Date
        f.departure_time,       -- 3: Departure Time
        f.arrival_date,         -- 4: Arrival Date
        f.arrival_time,         -- 5: Arrival Time
        f.status_,              -- 6: Status
        f.arrives,              -- 7: Arrival Airport Code
        f.departs,              -- 8: Departure Airport Code
        avail.available_tickets -- 9: # of tickets left
    FROM flight AS f
    -- join with airports for city search
    LEFT JOIN airport AS dep_airport
        ON f.departs = dep_airport.name
    LEFT JOIN airport AS arr_airport
        ON f.arrives = arr_airport.name
    -- subquery: count available tickets per flight
    JOIN (
        SELECT
            t.for_ AS flight_num,        -- ✅ this links tickets to flights
            COUNT(*) AS available_tickets
        FROM ticket AS t
        LEFT JOIN purchases AS p
            ON t.ticket_id = p.ticket_id
        WHERE p.ticket_id IS NULL        -- only tickets not purchased
        GROUP BY t.for_
    ) AS avail
        ON avail.flight_num = f.flight_num
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

        query = """
            SELECT *
            FROM flight
            WHERE flight_num = %s
        """
        cursor.execute(query, (flight_num,))
        flight = cursor.fetchone()

        cursor.close()
        conn.close()

        if not flight:
            return "Flight not found", 404

        return render_template(
            "buyCust.html",
            flight=flight,
            customer_email=session['username']
        )

    # ---------------------------------
    # POST → Actually buy the ticket
    # ---------------------------------
    if request.method == 'POST':
        customer_email = session['username']
        # If you later support agents, you can pass this in the form; for now None
        agent_email = request.form.get('agent_email') or None
        flight_num = request.form.get('flight_num')

        # 1) Find an available ticket for this flight
        cursor = conn.cursor()  # simple fetch, no need for dict here
        cursor.execute("""
            SELECT t.ticket_id
            FROM ticket AS t
            LEFT JOIN purchases AS p
                ON t.ticket_id = p.ticket_id
            WHERE
                t.for_ = %s
                AND p.ticket_id IS NULL
            LIMIT 1
        """, (flight_num,))
        row = cursor.fetchone()

        if not row:
            # No more tickets left for this flight
            cursor.close()
            conn.close()
            return "Sorry, this flight has no tickets available.", 400

        ticket_id = row[0]

        # 2) Insert into purchases (date = today using CURDATE())
        #    You can also use NOW() if you want date+time
        cursor.execute("""
            INSERT INTO purchases (customer_email, booking_agent_email, ticket_id, date)
            VALUES (%s, %s, %s, CURDATE())
        """, (customer_email, agent_email, ticket_id))

        conn.commit()
        cursor.close()
        conn.close()

        # You can redirect to a "my flights" page, or back to customer_home
        return redirect(url_for('customer_home'))
    
from datetime import date

@app.route('/spendingCust', methods=['GET', 'POST'])
def customer_spending():
    if 'username' not in session:
        return redirect(url_for('login_cust'))
    
    customer_email = session['username']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # ----- 1) Total spending in the last 12 months (always shown) -----
    total_spending_sql = """
        SELECT COALESCE(SUM(f.price), 0) AS total_spent
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.for_ = f.flight_num
        WHERE p.customer_email = %s
          AND p.date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
    """
    
    cursor.execute(total_spending_sql, (customer_email,))
    row = cursor.fetchone()
    total_spending_year = float(row[0] or 0)

    # ----- 2) Default chart: last 6 months (what you already have) -----
    today = date.today()
    months = []
    y = today.year
    m = today.month
    for _ in range(6):
        months.append((y, m))        # (year, month)
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()                 # oldest first

    # Query DB for spending grouped by year+month in that 6-month window
    start_year, start_month = months[0]
    start_date = date(start_year, start_month, 1)
    end_date = today

    monthly_sql = """
        SELECT 
            YEAR(p.date) AS y,
            MONTH(p.date) AS m,
            COALESCE(SUM(f.price), 0) AS total_spent
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.for_ = f.flight_num
        WHERE p.customer_email = %s
          AND p.date BETWEEN %s AND %s
        GROUP BY y, m
        ORDER BY y, m
    """
    cursor.execute(monthly_sql, (customer_email, start_date, end_date))
    rows = cursor.fetchall()   # e.g. [(2025, 7, 120.0), (2025, 9, 300.0), ...]

    spending_by_ym = {
        (int(r[0]), int(r[1])): float(r[2] or 0)
        for r in rows
    }

    default_month_numbers = []
    default_month_spending = []
    for (yy, mm) in months:
        default_month_numbers.append(mm)
        default_month_spending.append(spending_by_ym.get((yy, mm), 0.0))

    # ----- 3) Custom range (if user submits dates) -----
    is_custom = False
    custom_total_spending = None
    chart_title = "Spending per Month over the last 6 months"
    chart_month_numbers = default_month_numbers
    chart_month_spending = default_month_spending
    start_date_value = ""
    end_date_value = ""

    if request.method == 'POST':
        start_date_value = (request.form.get('start_date') or "").strip()
        end_date_value = (request.form.get('end_date') or "").strip()

        if start_date_value and end_date_value:
            try:
                start_d = datetime.strptime(start_date_value, "%Y-%m-%d").date()
                end_d = datetime.strptime(end_date_value, "%Y-%m-%d").date()

                # If reversed, swap
                if end_d < start_d:
                    start_d, end_d = end_d, start_d
                    start_date_value, end_date_value = end_date_value, start_date_value

                is_custom = True

                # 3a) Total spending in custom range
                custom_total_sql = """
                    SELECT COALESCE(SUM(f.price), 0) AS total_spent
                    FROM purchases p
                    JOIN ticket t ON p.ticket_id = t.ticket_id
                    JOIN flight f ON t.for_ = f.flight_num
                    WHERE p.customer_email = %s
                      AND p.date BETWEEN %s AND %s
                """
                cursor.execute(custom_total_sql, (customer_email, start_d, end_d))
                row = cursor.fetchone()
                custom_total_spending = float(row[0] or 0)

                # 3b) Monthly breakdown for custom range
                monthly_custom_sql = """
                    SELECT 
                        YEAR(p.date) AS y,
                        MONTH(p.date) AS m,
                        COALESCE(SUM(f.price), 0) AS total_spent
                    FROM purchases p
                    JOIN ticket t ON p.ticket_id = t.ticket_id
                    JOIN flight f ON t.for_ = f.flight_num
                    WHERE p.customer_email = %s
                      AND p.date BETWEEN %s AND %s
                    GROUP BY y, m
                    ORDER BY y, m
                """
                cursor.execute(monthly_custom_sql, (customer_email, start_d, end_d))
                rows = cursor.fetchall()

                spending_by_ym_custom = {
                    (int(r[0]), int(r[1])): float(r[2] or 0)
                    for r in rows
                }

                # helper to generate all months between start_d and end_d (inclusive)
                def iter_months(sd, ed):
                    yy = sd.year
                    mm = sd.month
                    res = []
                    while (yy < ed.year) or (yy == ed.year and mm <= ed.month):
                        res.append((yy, mm))
                        mm += 1
                        if mm == 13:
                            mm = 1
                            yy += 1
                    return res

                all_months = iter_months(start_d, end_d)

                chart_month_numbers = []
                chart_month_spending = []
                for (yy, mm) in all_months:
                    chart_month_numbers.append(mm)
                    chart_month_spending.append(
                        spending_by_ym_custom.get((yy, mm), 0.0)
                    )

                chart_title = f"Spending per Month from {start_date_value} to {end_date_value}"

            except ValueError:
                # bad date format → just keep default chart
                pass

    cursor.close()
    conn.close()

    return render_template(
        'spendingCust.html',
        total_spending_year=total_spending_year,
        # chart data (default or custom)
        month_numbers=chart_month_numbers,
        month_spending=chart_month_spending,
        chart_title=chart_title,
        # custom info
        is_custom=is_custom,
        custom_total_spending=custom_total_spending,
        start_date_value=start_date_value,
        end_date_value=end_date_value
    )


@app.route('/purchasesCust', methods=['GET', 'POST'])
def customer_purchases():
    if 'username' not in session:
        return redirect(url_for('login_cust'))
    
    customer_email = session['username']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # ---------- data1: upcoming purchased flights ----------
    query = """
        SELECT purchases.ticket_id, operated_by, flight_num, departure_date,
               departure_time, arrival_date, arrival_time, status_, arrives, departs
        FROM purchases
        JOIN ticket ON purchases.ticket_id = ticket.ticket_id
        JOIN flight ON ticket.for_ = flight.flight_num
        WHERE customer_email = %s AND status_ = 'upcoming'
    """
    cursor.execute(query, (customer_email,))
    data1 = cursor.fetchall()

    # ---------- data2: all purchased flights (optionally filtered) ----------
    query2 = """
        SELECT purchases.ticket_id, operated_by, flight_num, departure_date,
               departure_time, arrival_date, arrival_time, status_, arrives, departs
        FROM purchases
        JOIN ticket ON purchases.ticket_id = ticket.ticket_id
        JOIN flight ON ticket.for_ = flight.flight_num
        WHERE customer_email = %s
    """

    params = [customer_email]

    if request.method == 'POST':
        # 🔹 get values from the form body, not from args
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()

        if start_date:
            query2 += " AND departure_date >= %s"
            params.append(start_date)

        if end_date:
            query2 += " AND departure_date < %s"
            params.append(end_date)

        if origin:
            query2 += " AND departs LIKE %s"
            params.append(f"%{origin}%")

        if destination:
            query2 += " AND arrives = %s"
            params.append(destination)

    # For GET, we just use the base query2 with only customer_email
    cursor.execute(query2, tuple(params))
    data2 = cursor.fetchall()

    
    cursor.close()
    conn.close()

    return render_template('purchasedCust.html', data1=data1, data2=data2)

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

    return render_template('agentFlights.html', flights=flights, from_airport=from_airport,to_airport=to_airport,start_date=start_date,end_date=end_date)

# 3. search for flights and purchase tickets for customers 
@app.route('/agent_search', methods=['GET', 'POST'])
def agent_search():
    
    redirect_or_none = require_agent()
    if redirect_or_none:
        return redirect_or_none
    
    agent_email = session.get('agent_email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

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
                    f"Ticket #{ticket_id}, Flight NO.{flight_num} has been purchased for "
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
        WHERE f.status_ = "upcoming" AND t.ticket_id NOT IN (SELECT p.ticket_id FROM purchases as p) 
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

    return render_template('agentSearch.html', flights=flights, departure_airport=departure_airport, arrival_airport=arrival_airport, departure_date=departure_date, message=message, error=error)

# 4. access analytics 
@app.route('/agent_analytics')
def agent_analytics(): 
    
    redirect_or_none = require_agent()
    if redirect_or_none:
        return redirect_or_none
    
    agent_email = session.get('agent_email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 4.1 get commission totals for the last 30 days 
    # this assumes booking agent gets a commission of 10%
    monthly_commission_query = """ 
        SELECT COALESCE(SUM(f.price * 0.1),0) as total_commission
        FROM purchases as p  
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE p.booking_agent_email = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY )
    """
    cursor.execute(monthly_commission_query, (agent_email,))
    monthly_commission = cursor.fetchone()

    # 4.2 average commission per ticket 
    avg_commission_query = """ 
        SELECT COALESCE(AVG(f.price * 0.1),0) as avg_commission
        FROM purchases as p  
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE p.booking_agent_email = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY )
    """
    cursor.execute(avg_commission_query, (agent_email,))
    avg_commission = cursor.fetchone()

    # 4.3 number of tickets sold 
    tixsold_query = """ 
        SELECT COUNT(*) as tickets_sold
        FROM purchases as p  
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE p.booking_agent_email = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY )
    """
    cursor.execute(tixsold_query, (agent_email,))
    tixsold = cursor.fetchone()
    
    # 4.4 top 5 customers by number of tickets (last 6 months)
    top5_tickets_query = """
        SELECT p.customer_email, COUNT(t.ticket_id) as ticket_count
        FROM purchases as p 
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE p.booking_agent_email = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY p.customer_email 
        ORDER BY ticket_count DESC
        LIMIT 5 
    """
    cursor.execute(top5_tickets_query, (agent_email,))
    top5_customer_tickets = cursor.fetchall()

    # 4.5 top 5 customers by commission (last year)
    top5_commission_query = """
        SELECT p.customer_email, SUM(f.price * 0.1) as total_commission
        FROM purchases as p 
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num
        WHERE p.booking_agent_email = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY p.customer_email
        ORDER BY total_commission DESC 
        LIMIT 5 
    """
    cursor.execute(top5_commission_query, (agent_email,))
    top5_customers_commission = cursor.fetchall()

    # convert decimals -> float/int for JSON
    for row in top5_customer_tickets:
        if row['ticket_count'] is not None:
            row['ticket_count'] = int(row['ticket_count'])
    for row in top5_customers_commission:
        if row['total_commission'] is not None:
            row['total_commission'] = float(row['total_commission'])

    cursor.close()
    conn.close()
    
    return render_template('agentAnalytics.html', monthly_commission=monthly_commission, avg_commission=avg_commission, tixsold=tixsold, top5_customer_tickets=top5_customer_tickets,top5_customers_commission=top5_customers_commission )  

##### airline staff ####

@app.route('/default_view')

# 1. default view: all flights operated by that airline in the next 30 days
def default_view(): 
    if 'username' not in session:
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    upcoming_flights_query = """
        SELECT *
        FROM flight as f 
        WHERE f.operated_by = %s AND f.status_ = 'upcoming' AND f.departure_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    """
    cursor.execute(upcoming_flights_query, (airline,))
    upcoming_flights = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('defaultViewStaff.html', upcoming_flights=upcoming_flights, airline=airline)

# 2. passenger lists for flights 
@app.route('/passenger_list')
def passenger_list(): 
    if 'username' not in session:
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    passengers_list_query = """
        SELECT f.flight_num, f.departs, f.arrives, f.departure_date, c.name as customer_name, c.email as customer_email
        FROM customer as c
        JOIN purchases as p ON c.email = p.customer_email 
        JOIN ticket as t ON p.ticket_id = t.ticket_id 
        JOIN flight as f ON t.for_ = f.flight_num
        WHERE f.operated_by = %s 
        ORDER BY f.flight_num, c.name ASC
    """
    cursor.execute(passengers_list_query, (airline,))
    passengers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('passengerList.html', passengers=passengers, airline=airline)

# 3. check all flights taken by a specific customer on their airline 
@app.route('/customer_flights', methods=['GET', 'POST'])
def customer_flights(): 
    if 'username' not in session:
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    cust_flights = []
    customer_email = None 

    if request.method == 'GET':
        customer_email = request.args.get('customer_email')
    else:  # POST
        customer_email = request.form.get('customer_email')

    if customer_email:
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        customer_flights_query = """
            SELECT p.customer_email, f.flight_num, f.operated_by as airline_name, f.departs, f.departure_date, 
                f.departure_time, f.arrives, f.arrival_date, f.arrival_time,
                f.price, f.status_, f.use_ as airplane_id
            FROM purchases as p 
            JOIN ticket as t ON p.ticket_id = t.ticket_id 
            JOIN flight as f ON t.for_ = f.flight_num
            WHERE p.customer_email = %s AND f.operated_by = %s 
            ORDER BY f.departure_date DESC
        """
        cursor.execute(customer_flights_query, (customer_email, airline))
        cust_flights = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template('customerFlights.html', cust_flights=cust_flights, airline=airline, customer_email=customer_email)

# 4. staff analytics
@app.route('/staff_analytics')
def staff_analytics(): 
    if 'username' not in session:
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 4.1 top booking agents by month (by tickets)
    top_agents_month_tickets_query  = """
        SELECT p.booking_agent_email, COUNT(*) as tickets_sold
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY p.booking_agent_email 
        ORDER BY tickets_sold DESC
    """
    cursor.execute(top_agents_month_tickets_query, (airline,))
    top_agents_month_tickets = cursor.fetchall()

    # 4.2 top booking agents by year (by tickets)
    top_agents_year_tickets_query  = """
        SELECT p.booking_agent_email, COUNT(*) as tickets_sold
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY p.booking_agent_email 
        ORDER BY tickets_sold DESC 
    """
    cursor.execute(top_agents_year_tickets_query, (airline,))
    top_agents_year_tickets = cursor.fetchall()

    # 4.3 top booking agents by month (by commission)
    top_agents_month_commission_query = """
        SELECT p.booking_agent_email, SUM(f.price * 0.1) as commission
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY p.booking_agent_email 
        ORDER BY commission DESC 
    """
    cursor.execute(top_agents_month_commission_query, (airline,))
    top_agents_month_commission = cursor.fetchall()

    # 4.4 top booking agents by year (by commission)
    top_agents_year_commission_query = """
        SELECT p.booking_agent_email, SUM(f.price * 0.1) as commission
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY p.booking_agent_email 
        ORDER BY commission DESC 
    """
    cursor.execute(top_agents_year_commission_query, (airline,))
    top_agents_year_commission = cursor.fetchall()

    # 4.5 most frequent customer in the last year 
    most_freq_cust_query = """
        SELECT p.customer_email, COUNT(*) as flights_taken
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY p.customer_email
        ORDER BY flights_taken DESC 
        LIMIT 1
    """
    cursor.execute(most_freq_cust_query, (airline,))
    most_freq_cust = cursor.fetchone()

    # 4.6 tickets sold per month 
    tix_per_month_query = """
        SELECT MONTH(p.date) as month, COUNT(p.ticket_id) as tickets_sold
        FROM purchases as p
        JOIN ticket as t ON p.ticket_id = t.ticket_id
        JOIN flight as f ON t.for_ = f.flight_num 
        WHERE f.operated_by = %s AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY month
    """
    cursor.execute(tix_per_month_query, (airline,))
    tix_per_month = cursor.fetchall()

    # 4.7 delay vs on time statistics 
    delay_vs_ontime_query = """
        SELECT f.status_, COUNT(*) as count
        FROM flight as f
        WHERE f.operated_by = %s AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY f.status_
    """
    cursor.execute(delay_vs_ontime_query, (airline,))
    delay_vs_ontime = cursor.fetchall()

    # 4.8 top 10 destinations for the last 3 months
    top10_destinations_month_query = """
        SELECT f.arrives as destination, COUNT(*) as tickets_sold 
        FROM purchases AS p
        JOIN ticket AS t ON p.ticket_id = t.ticket_id
        JOIN flight AS f ON t.for_ = f.flight_num
        WHERE f.operated_by = %s AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
        GROUP BY f.arrives
        ORDER BY tickets_sold DESC 
        LIMIT 10
    """
    cursor.execute(top10_destinations_month_query, (airline,))
    top10_destinations_month = cursor.fetchall()

    # 4.9 top 10 destinations for the last year 
    top10_destinations_year_query = """
        SELECT f.arrives as destination, COUNT(*) as tickets_sold 
        FROM purchases AS p
        JOIN ticket AS t ON p.ticket_id = t.ticket_id
        JOIN flight AS f ON t.for_ = f.flight_num
        WHERE f.operated_by = %s AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY f.arrives
        ORDER BY tickets_sold DESC 
        LIMIT 10
    """
    cursor.execute(top10_destinations_year_query, (airline,))
    top10_destinations_year = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'staffAnalytics.html', 
        airline=airline,
        top_agents_month_tickets=top_agents_month_tickets,
        top_agents_year_tickets=top_agents_year_tickets,
        top_agents_month_commission=top_agents_month_commission,
        top_agents_year_commission=top_agents_year_commission,
        most_freq_cust=most_freq_cust,
        tix_per_month=tix_per_month,
        delay_vs_ontime=delay_vs_ontime,
        top10_destinations_month=top10_destinations_month,
        top10_destinations_year=top10_destinations_year
    )

# 5. admin only operations 
# 5.1 add new airports and airplanes 
@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    if 'username' not in session or session.get('permissions') != "admin":
        return redirect(url_for('login_staff'))

    message = None 
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        city = request.form.get('city')
        country = request.form.get('country')

        insert_airport_query = """
            INSERT INTO airport (name, city, country)
            VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(insert_airport_query, (name, city, country))
            conn.commit()
            message = "Airport added successfully!"

        except Exception as e:
            conn.rollback()
            message = f"Error adding airport: {e}"
    
    cursor.close()
    conn.close() 

    return render_template('addAirport.html', message=message)

@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    if 'username' not in session or session.get('permissions') != "admin":
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    message = None 
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        ID = request.form.get('airplane_id')
        seat_capacity = request.form.get('seat_capacity')

        insert_airplane_query = """
            INSERT INTO airplane (ID, airline_name, seat_capacity)
            VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(insert_airplane_query, (ID, airline, seat_capacity))
            conn.commit()
            message = "Airplane added successfully!"
        except Exception as e:
            conn.rollback()
            message = f"Error adding airplane: {e}"

    cursor.close()
    conn.close()
    return render_template('addAirplane.html', message=message)


# 5.2 associate booking agents with the airline  
@app.route('/authorize_agent', methods=['GET', 'POST'])
def authorize_agent():
    if 'username' not in session or session.get('permissions') != "admin":
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    message = None

    # get all booking agents
    all_agents_query = "SELECT email FROM booking_agent"
    cursor.execute(all_agents_query)
    all_agents = cursor.fetchall()

    if request.method == 'POST':
        agent_email = request.form.get('booking_agent_email')

        insert_agent_query = """
            INSERT INTO authorized_by (airline_name, booking_agent_email)
            VALUES (%s, %s)
        """

        try:
            cursor.execute(insert_agent_query, (airline, agent_email))
            conn.commit()
            message = "Booking agent associated with airline successfully!"
        
        except Exception as e:
            conn.rollback()
            message = f"Error authorizing agent: {e}"

    cursor.close()
    conn.close()

    return render_template('authorizeAgent.html', airline=airline, all_agents=all_agents, message=message)

# 6. operator only operations 
# 6.1 update the status of the flights 
@app.route('/update_status', methods=['GET', 'POST'])
def update_status(): 
    if 'username' not in session or session.get('permissions') != "operator":
        return redirect(url_for('login_staff'))
    
    airline = session.get('airline')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    message = None 

    if request.method == 'POST':
        flight_num = request.form.get('flight_num')
        new_status = request.form.get('status_')

        update_status_query = """
            UPDATE flight
            SET status_ = %s
            WHERE flight_num = %s AND operated_by = %s
        """
        try:
            cursor.execute(update_status_query, (new_status, flight_num, airline))
            conn.commit()
            message = "Flight status updated successfully!"
        
        except Exception as e:
                conn.rollback()
                message = f"Error updating flight status: {e}"
    
    cursor.close()
    conn.close()

    return render_template('updateStatus.html', airline=airline, message=message)

# 7. airline staff admin home page
@app.route('/admin_home')
def admin_home():
    if 'username' not in session or session['permissions'] != "admin":
        return redirect("/login_staff")
    
    airline = session.get('airline')
    return render_template('indexAdminStaff.html')

# 8. airline staff operator home page 
@app.route('/operator_home')
def operator_home():
    if 'username' not in session or session['permissions'] != "operator":
        return redirect("/login_staff")
    
    return render_template('indexOperatorStaff.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

	
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
