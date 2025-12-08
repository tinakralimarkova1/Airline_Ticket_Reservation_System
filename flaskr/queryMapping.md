# **Query Mapping**

---

## **1. Public Homepage (`index.html`)**

### **Feature: Display upcoming flights**

**Query executed:**

```sql
SELECT operated_by, flight_num, departure_time, arrival_time, status_, arrives, departs
FROM flight
WHERE status_ = 'upcoming';
```

**Purpose:**
Shows all flights that have not yet departed.

---

### **Feature: Search by origin, destination, date, or time**

Depending on which fields the user fills in, one or more filters are added.

**Base query:**

```sql
SELECT operated_by, flight_num, departure_date, departure_time, arrival_date, arrival_time, 
       status_, arrives, departs
FROM flight
WHERE status_ = 'upcoming'
```

**Filters:**

* **Origin filter**

```sql
AND (departs = %s OR departs LIKE %s)
```

* **Destination filter**

```sql
AND (arrives = %s OR arrives LIKE %s)
```

* **Departure date filter**

```sql
AND departure_date = %s
```

* **Departure time filter**

```sql
AND departure_time = %s
```

The final executed query depends on which inputs the user provides.

---

### **Feature: Display in-progress flights**

**Query executed:**

```sql
SELECT operated_by, flight_num, departure_date, departure_time, arrival_date, arrival_time, 
       status_, arrives, departs
FROM flight
WHERE status_ = 'in progress';
```

**Purpose:**
Displays all flights that are currently in progress.

---

### **Feature: Search for specific in-progress flights**

**Base query:**

```sql
SELECT operated_by, flight_num, departure_date, departure_time, arrival_date, arrival_time, 
       status_, arrives, departs
FROM flight
WHERE status_ = 'in progress'
```

**Optional filters:**

* **Airline name:**

```sql
AND operated_by = %s
```

* **Flight number:**

```sql
AND flight_num = %s
```

**Purpose:**
Allows users to narrow down in-progress flights by airline and/or flight number.

---

## **2. Login Pages**

Each login submits a username/email and password, then queries the corresponding table.

---

### **Feature: Customer Login (`loginCustomer.html`)**

**Query executed:**

```sql
SELECT *
FROM customer
WHERE email = %s AND password = SHA2(%s, 256);
```

**Purpose:**
Verifies credentials and retrieves customer info for session storage.

---

### **Feature: Booking Agent Login (`loginAgent.html`)**

**Query executed:**

```sql
SELECT *
FROM booking_agent
WHERE email = %s AND password = SHA2(%s, 256);
```

**Purpose:**
Authenticates booking agents using a hashed password.

---

### **Feature: Airline Staff Login (`loginStaff.html`)**

**Query executed:**

```sql
SELECT *
FROM airline_staff
WHERE username = %s AND password = SHA2(%s, 256);
```

**Purpose:**
Authenticates airline staff using a hashed password.

---

## **3. Registration Pages**

---

### **Feature: Customer Registration (`register_customer`)**

**Check whether the email already exists:**

```sql
SELECT email
FROM customer
WHERE email = %s;
```

**Insert new customer:**

```sql
INSERT INTO customer
(email, name, password, building_number, street, city, state, phone_number,
 passport_number, passport_expiration_date, passport_country, date_of_birth)
VALUES
(%s, %s, SHA2(%s, 256), %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

**Purpose:**
Creates a full customer profile and stores a hashed password.

---

### **Feature: Booking Agent Registration (`register_agent`)**

**Check whether the email already exists:**

```sql
SELECT email
FROM booking_agent
WHERE email = %s;
```

**Insert new booking agent:**

```sql
INSERT INTO booking_agent (email, password)
VALUES (%s, SHA2(%s, 256));
```

**Purpose:**
Registers a new agent account with a hashed password.

---

### **Feature: Airline Staff Registration (`register_staff`)**

**Validate that the airline exists:**

```sql
SELECT name
FROM airline
WHERE name = %s;
```

**Check whether the username already exists:**

```sql
SELECT username
FROM airline_staff
WHERE username = %s;
```

**Insert new staff member:**

```sql
INSERT INTO airline_staff
(username, password, first_name, last_name, date_of_birth, permissions, works_for)
VALUES
(%s, SHA2(%s, 256), %s, %s, %s, %s, %s);
```

**Purpose:**
Creates a staff account tied to a valid airline, with assigned permissions.

---

## **4. Customer Pages**

---

### **4.1 Customer Homepage (`/customer_home`, `indexCust.html`)**

### **Feature: Show all upcoming flights with available tickets and filters**

**Base query (all upcoming flights with available tickets):**

```sql
SELECT
    f.operated_by,          
    f.flight_num,           
    f.departure_date,       
    f.departure_time,       
    f.arrival_date,        
    f.arrival_time,         
    f.status_,              
    f.arrives,              
    f.departs,              
    avail.available_tickets 
FROM flight AS f
-- join with airports for city search
LEFT JOIN airport AS dep_airport
    ON f.departs = dep_airport.name
LEFT JOIN airport AS arr_airport
    ON f.arrives = arr_airport.name
-- subquery: count available tickets per flight
JOIN (
    SELECT
        t.for_ AS flight_num,
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
```

**Filters appended depending on user input:**

**Origin filter (origin airport code or origin city):**

```sql
AND (f.departs LIKE %s OR dep_airport.host LIKE %s)
```

**Destination filter (destination airport code or destination city):**

```sql
AND (f.arrives LIKE %s OR arr_airport.host LIKE %s)
```

**Departure date filter:**

```sql
AND f.departure_date = %s
```

**Departure time filter (departing at or after):**

```sql
AND f.departure_time >= %s
```

**Purpose:**
Lets customers search upcoming flights that still have available tickets, using airport or city plus optional date/time filters.

---

### **4.2 Customer Spending Page (`/spending_cust`, `spendingCust.html`)**

#### **Feature: Total spending in the last 12 months**

```sql
SELECT COALESCE(SUM(f.price), 0) AS total_spent
FROM purchases p
JOIN ticket t ON p.ticket_id = t.ticket_id
JOIN flight f ON t.for_ = f.flight_num
WHERE p.customer_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH);
```

**Purpose:**
Shows the customer’s total spending on tickets over the last year.

---

#### **Feature: Default bar chart – spending per month over last 6 months**

```sql
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
ORDER BY y, m;
```

Parameters:

* `%s` (1st): customer email
* `%s` (2nd): `start_date` (first day of the oldest month in the 6-month window)
* `%s` (3rd): `end_date` (today’s date)

**Purpose:**
Builds a monthly spending breakdown over the last 6 months for visualization.

---

#### **Feature: Custom date range – total spending**

```sql
SELECT COALESCE(SUM(f.price), 0) AS total_spent
FROM purchases p
JOIN ticket t ON p.ticket_id = t.ticket_id
JOIN flight f ON t.for_ = f.flight_num
WHERE p.customer_email = %s
  AND p.date BETWEEN %s AND %s;
```

**Purpose:**
Shows total spending within a user-selected start/end date window.

---

#### **Feature: Custom date range – monthly breakdown**

```sql
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
ORDER BY y, m;
```

**Purpose:**
Provides monthly spending totals within the chosen custom range for the bar chart.

---

### **4.3 Customer Purchases Page (upcoming + history)**

#### **Feature: Show upcoming purchased flights (top table)**

```sql
SELECT purchases.ticket_id,
       operated_by,
       flight_num,
       departure_date,
       departure_time,
       arrival_date,
       arrival_time,
       status_,
       arrives,
       departs
FROM purchases
JOIN ticket ON purchases.ticket_id = ticket.ticket_id
JOIN flight ON ticket.for_ = flight.flight_num
WHERE customer_email = %s
  AND status_ = 'upcoming';
```

**Purpose:**
Shows all flights that the customer has purchased that are still upcoming.

---

#### **Feature: Show all purchased flights (bottom table, base query)**

```sql
SELECT purchases.ticket_id,
       operated_by,
       flight_num,
       departure_date,
       departure_time,
       arrival_date,
       arrival_time,
       status_,
       arrives,
       departs
FROM purchases
JOIN ticket ON purchases.ticket_id = ticket.ticket_id
JOIN flight ON ticket.for_ = flight.flight_num
WHERE customer_email = %s;
```

**Purpose:**
Displays the full purchase history for the logged-in customer.

---

#### **Filters for “All Purchased Flights” table**

These are appended dynamically when the user submits filtering options:

**Filter: Start date**

```sql
AND departure_date >= %s
```

**Filter: End date**

```sql
AND departure_date < %s
```

**Filter: Origin airport**

```sql
AND departs LIKE %s
```

**Filter: Destination airport**

```sql
AND arrives = %s
```

**Purpose:**
Allows customers to filter their purchase history by date range and route.

---

### **4.4 Customer Buying Page (`buyCust.html`)**

#### **Feature: Show selected flight details before purchase (GET /buy_cust)**

```sql
SELECT *
FROM flight
WHERE flight_num = %s;
```

**Purpose:**
Displays full details of the selected flight so the customer can review before purchasing.

---

#### **Feature: Find an available ticket for this flight (POST /buy_cust)**

```sql
SELECT t.ticket_id
FROM ticket AS t
LEFT JOIN purchases AS p
    ON t.ticket_id = p.ticket_id
WHERE
    t.for_ = %s
    AND p.ticket_id IS NULL
LIMIT 1;
```

**Purpose:**
Ensures only unpurchased tickets are sold; returns one available ticket or none if sold out.

---

#### **Feature: Insert a new purchase record (POST /buy_cust)**

```sql
INSERT INTO purchases (customer_email, booking_agent_email, ticket_id, date)
VALUES (%s, %s, %s, CURDATE());
```

**Purpose:**
Creates a purchase entry for the logged-in customer. `booking_agent_email` is `NULL` for direct customer purchases.

---

## **5. Booking Agent Pages**

---

### **5.1 Agent Flights (`/agent_flights`, `agentFlights.html`)**

### **Feature: Display flights purchased by the agent**

**Query executed:**

```sql
SELECT f.flight_num,
       f.operated_by AS airline_name,
       f.departs,
       f.departure_date,
       f.departure_time,
       f.arrives,
       f.arrival_date,
       f.arrival_time,
       f.price,
       f.status_,
       f.use_ AS airplane_id,
       p.customer_email,
       p.date
FROM flight AS f,
     ticket AS t,
     purchases AS p
WHERE p.booking_agent_email = %s
  AND p.ticket_id = t.ticket_id
  AND t.for_ = f.flight_num
  -- Optional filters:
  -- AND f.departs = %s
  -- AND f.arrives = %s
  -- AND f.departure_date >= %s
  -- AND f.departure_date <= %s
ORDER BY p.date DESC;
```

**Purpose:**
Shows all flights purchased by the logged-in agent for customers, with optional filters by departure/arrival airport and departure date range.

---

### **5.3 Agent Search & Purchase (`/agent_search`, `agentSearch.html`)**

#### **Feature: Verify agent is authorized to book for airline**

**Query executed:**

```sql
SELECT 1
FROM flight AS f
JOIN authorized_by AS auth
  ON f.operated_by = auth.airline_name
WHERE auth.booking_agent_email = %s
  AND f.flight_num = %s;
```

**Purpose:**
Checks whether the booking agent is authorized to sell tickets for the selected flight’s airline.

---

#### **Feature: Find an available ticket for a flight**

**Query executed:**

```sql
SELECT t.ticket_id
FROM ticket AS t
WHERE t.for_ = %s
  AND t.ticket_id NOT IN (
      SELECT p.ticket_id
      FROM purchases AS p
  );
```

**Purpose:**
Selects an unused ticket for the chosen flight so the agent can complete a purchase on behalf of a customer.

---

#### **Feature: Insert a new purchase**

**Query executed:**

```sql
INSERT INTO purchases (ticket_id, customer_email, booking_agent_email, date)
VALUES (%s, %s, %s, CURDATE());
```

**Purpose:**
Records the ticket purchase made by the booking agent for a specific customer on the current date.

---

#### **Feature: Search upcoming flights with available tickets**

**Query executed:**

```sql
SELECT f.flight_num,
       f.operated_by AS airline_name,
       f.departs,
       f.departure_date,
       f.departure_time,
       f.arrives,
       f.arrival_date,
       f.arrival_time,
       f.price,
       f.status_,
       f.use_ AS airplane_id
FROM flight AS f
JOIN ticket AS t
  ON t.for_ = f.flight_num
WHERE f.status_ = 'upcoming'
  AND t.ticket_id NOT IN (
      SELECT p.ticket_id
      FROM purchases AS p
  )
  -- Optional filters:
  -- AND f.departs = %s
  -- AND f.arrives = %s
  -- AND f.departure_date = %s
ORDER BY f.departure_date, f.departure_time;
```

**Purpose:**
Lists all upcoming flights that still have unsold tickets, with optional filters for departure airport, arrival airport, and departure date.

---

### **5.4 Agent Analytics (`/agent_analytics`, `agentAnalytics.html`)**

#### **Feature: Total commission in last 30 days**

**Query executed:**

```sql
SELECT COALESCE(SUM(f.price * 0.1), 0) AS total_commission
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.booking_agent_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

**Purpose:**
Calculates the total commission (10% of ticket price) earned by the agent over the last 30 days.

---

#### **Feature: Average commission per ticket in last 30 days**

**Query executed:**

```sql
SELECT COALESCE(AVG(f.price * 0.1), 0) AS avg_commission
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.booking_agent_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

**Purpose:**
Computes the average commission per ticket for the agent over the last 30 days.

---

#### **Feature: Number of tickets sold in last 30 days**

**Query executed:**

```sql
SELECT COUNT(*) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.booking_agent_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

**Purpose:**
Counts how many tickets the agent sold in the last 30 days.

---

#### **Feature: Top 5 customers by tickets (last 6 months)**

**Query executed:**

```sql
SELECT p.customer_email,
       COUNT(t.ticket_id) AS ticket_count
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.booking_agent_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY p.customer_email
ORDER BY ticket_count DESC
LIMIT 5;
```

**Purpose:**
Identifies the top 5 customers by number of tickets purchased through this agent over the last 6 months.

---

#### **Feature: Top 5 customers by commission (last year)**

**Query executed:**

```sql
SELECT p.customer_email,
       SUM(f.price * 0.1) AS total_commission
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.booking_agent_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY p.customer_email
ORDER BY total_commission DESC
LIMIT 5;
```

**Purpose:**
Finds the top 5 customers who generated the highest total commission for the agent over the last year.

---

## **6. Airline Staff Pages (Admin & Operator)**

---

### **6.1 Default View (`/default_view`, `defaultViewStaff.html`)**

### **Feature: Display upcoming flights for airline (next 30 days)**

**Query executed:**

```sql
SELECT *
FROM flight AS f
WHERE f.operated_by = %s
  AND f.status_ = 'upcoming'
  AND f.departure_date BETWEEN CURDATE()
                           AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
  -- Optional filters:
  -- AND f.departs = %s
  -- AND f.arrives = %s
  -- AND f.departure_date >= %s
  -- AND f.departure_date <= %s;
```

**Purpose:**
Shows all upcoming flights operated by the logged-in airline for the next 30 days, with optional filters for route and date range.

---

### **6.2 Passenger List (`/passenger_list`, `passengerList.html`)**

### **Feature: Display all passengers per flight**

**Query executed:**

```sql
SELECT f.flight_num,
       f.departs,
       f.arrives,
       f.departure_date,
       c.name AS customer_name,
       c.email AS customer_email
FROM customer AS c
JOIN purchases AS p
  ON c.email = p.customer_email
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
ORDER BY f.flight_num, c.name ASC;
```

**Purpose:**
Lists all passengers on flights operated by the airline, grouped and sorted by flight and passenger name.

---

### **6.3 Customer Flights (`/customer_flights`, `customerFlights.html`)**

### **Feature: Display all flights for a specific customer with this airline**

**Query executed:**

```sql
SELECT p.customer_email,
       f.flight_num,
       f.operated_by AS airline_name,
       f.departs,
       f.departure_date,
       f.departure_time,
       f.arrives,
       f.arrival_date,
       f.arrival_time,
       f.price,
       f.status_,
       f.use_ AS airplane_id
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE p.customer_email = %s
  AND f.operated_by = %s
ORDER BY f.departure_date DESC;
```

**Purpose:**
Shows the flight history of a specific customer with the current airline.

---

### **6.4 Staff Analytics (`/staff_analytics`, `staffAnalytics.html`)**

#### **Feature: Top booking agents by tickets (last 30 days)**

**Query executed:**

```sql
SELECT p.booking_agent_email,
       COUNT(*) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.booking_agent_email
ORDER BY tickets_sold DESC;
```

**Purpose:**
Finds the most productive booking agents by ticket volume in the last month.

---

#### **Feature: Top booking agents by tickets (last year)**

**Query executed:**

```sql
SELECT p.booking_agent_email,
       COUNT(*) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY p.booking_agent_email
ORDER BY tickets_sold DESC;
```

**Purpose:**
Ranks booking agents by total tickets sold for this airline over the past year.

---

#### **Feature: Top booking agents by commission (last 30 days)**

**Query executed:**

```sql
SELECT p.booking_agent_email,
       SUM(f.price * 0.1) AS commission
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.booking_agent_email
ORDER BY commission DESC;
```

**Purpose:**
Shows which booking agents generated the most commission for the airline in the last 30 days.

---

#### **Feature: Top booking agents by commission (last year)**

**Query executed:**

```sql
SELECT p.booking_agent_email,
       SUM(f.price * 0.1) AS commission
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY p.booking_agent_email
ORDER BY commission DESC;
```

**Purpose:**
Identifies which booking agents earned the highest commission for the airline over the last year.

---

#### **Feature: Most frequent customer (last year)**

**Query executed:**

```sql
SELECT p.customer_email,
       COUNT(*) AS flights_taken
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY p.customer_email
ORDER BY flights_taken DESC
LIMIT 1;
```

**Purpose:**
Finds the single most frequent customer for the airline in the past year.

---

#### **Feature: Tickets sold per month (last year)**

**Query executed:**

```sql
SELECT MONTH(p.date) AS month,
       COUNT(p.ticket_id) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY month;
```

**Purpose:**
Aggregates tickets sold per month for the airline over the last year.

---

#### **Feature: Delay vs on-time statistics (last year)**

**Query executed:**

```sql
SELECT f.status_,
       COUNT(*) AS count
FROM flight AS f
WHERE f.operated_by = %s
  AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY f.status_;
```

**Purpose:**
Shows how many flights were on time, delayed, or in other statuses over the past year.

---

#### **Feature: Top 10 destinations (last 3 months)**

**Query executed:**

```sql
SELECT f.arrives AS destination,
       COUNT(*) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
GROUP BY f.arrives
ORDER BY tickets_sold DESC
LIMIT 10;
```

**Purpose:**
Finds the most popular destinations for the airline in the last 3 months.

---

#### **Feature: Top 10 destinations (last year)**

**Query executed:**

```sql
SELECT f.arrives AS destination,
       COUNT(*) AS tickets_sold
FROM purchases AS p
JOIN ticket AS t
  ON p.ticket_id = t.ticket_id
JOIN flight AS f
  ON t.for_ = f.flight_num
WHERE f.operated_by = %s
  AND f.departure_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
GROUP BY f.arrives
ORDER BY tickets_sold DESC
LIMIT 10;
```

**Purpose:**
Lists the top 10 destinations by tickets sold over the past year.

---

### **6.5 Add Airport (`/add_airport`, `addAirport.html`)**

#### **Feature: Insert city if it does not exist**

**Query executed:**

```sql
INSERT IGNORE INTO city (name)
VALUES (%s);
```

**Purpose:**
Ensures the city exists in the `city` table before inserting a new airport.

---

#### **Feature: Insert new airport**

**Query executed:**

```sql
INSERT INTO airport (name, host)
VALUES (%s, %s);
```

**Purpose:**
Adds a new airport associated with a given city.

---

### **6.6 Add Airplane (`/add_airplane`, `addAirplane.html`)**

#### **Feature: Insert new airplane for airline**

**Query executed:**

```sql
INSERT INTO airplane (ID, seat_capacity, owned_by)
VALUES (%s, %s, %s);
```

**Purpose:**
Registers a new airplane with its seat capacity under the current airline.

---

### **6.7 Add Flight (`/add_flight`, `addFlight.html`)**

#### **Feature: Load airports for the form**

**Query executed:**

```sql
SELECT name
FROM airport
ORDER BY name;
```

**Purpose:**
Retrieves all airport names to populate the departure/arrival dropdowns.

---

#### **Feature: Load airplanes owned by airline**

**Query executed:**

```sql
SELECT ID, seat_capacity
FROM airplane
WHERE owned_by = %s
ORDER BY ID;
```

**Purpose:**
Lists airplanes belonging to the current airline so staff can choose which plane operates the new flight.

---

#### **Feature: Validate airplane ownership and get seat capacity**

**Query executed:**

```sql
SELECT seat_capacity
FROM airplane
WHERE ID = %s
  AND owned_by = %s;
```

**Purpose:**
Ensures the selected airplane belongs to the airline and retrieves its seat capacity.

---

#### **Feature: Insert new flight**

**Query executed:**

```sql
INSERT INTO flight (
    flight_num,
    price,
    status_,
    departure_date,
    departure_time,
    arrival_date,
    arrival_time,
    operated_by,
    use_,
    departs,
    arrives
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

**Purpose:**
Creates a new flight record operated by the current airline.

---

#### **Feature: Get next ticket ID**

**Query executed:**

```sql
SELECT COALESCE(MAX(ticket_id), 0) AS max_id
FROM ticket;
```

**Purpose:**
Finds the current maximum ticket ID to determine the starting ID for the new batch of tickets.

---

#### **Feature: Insert tickets for the new flight**

**Query executed:**

```sql
INSERT INTO ticket (ticket_id, for_)
VALUES (%s, %s);
```

*(Executed in a loop for `seat_capacity` times with incrementing `ticket_id`.)*

**Purpose:**
Generates one ticket per seat for the newly created flight.

---

### **6.8 Authorize Agent (`/authorize_agent`, `authorizeAgent.html`)**

#### **Feature: Load all booking agents**

**Query executed:**

```sql
SELECT email
FROM booking_agent;
```

**Purpose:**
Retrieves all booking agents so the admin can choose which ones to authorize.

---

#### **Feature: Associate booking agent with airline**

**Query executed:**

```sql
INSERT INTO authorized_by (airline_name, booking_agent_email)
VALUES (%s, %s);
```

**Purpose:**
Grants the selected booking agent permission to sell tickets for this airline.

---

### **6.9 Update Flight Status (`/update_status`, `updateStatus.html`)**

#### **Feature: Update status for a flight**

**Query executed:**

```sql
UPDATE flight
SET status_ = %s
WHERE flight_num = %s
  AND operated_by = %s;
```

**Purpose:**
Allows operator-level staff to change the status of a flight (e.g., upcoming, in-progress, delayed, completed).

---


