
# **Query Mapping**

## **1. Homepage (`index.html`)**

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

Depending on which fields the user fills in, one or more filters are added:

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

---

### **Feature: Search for specific in-progress flights**

**Dynamic query with optional filters:**

**Base:**

```sql
SELECT operated_by, flight_num, departure_date, departure_time, arrival_date, arrival_time, 
       status_, arrives, departs
FROM flight
WHERE status_ = 'in progress'
```

**Optional filters:**

* Airline name:

```sql
AND operated_by = %s
```

* Flight number:

```sql
AND flight_num = %s
```

---

# **2. Login Pages**

## **Login (all roles)**

Each login submits a username and password, then queries the corresponding table.

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

---

### **Feature: Airline Staff Login (`loginStaff.html`)**

**Query executed:**

```sql
SELECT *
FROM airline_staff
WHERE username = %s AND password = SHA2(%s, 256);
```

---

# **3. Registration Pages**



**Customer Registration (`register_customer`)**

• Check whether the email already exists:
```sql
SELECT email
FROM customer
WHERE email = %s;
```


• Insert new customer:

```sql
INSERT INTO customer
(email, name, password, building_number, street, city, state, phone_number,
passport_number, passport_expiration_date, passport_country, date_of_birth)
VALUES
(%s, %s, SHA2(%s, 256), %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

Purpose: Creates a full customer profile and stores a hashed password.

---

**Booking Agent Registration (`register_agent`)**

• Check whether the email already exists:
```sql
SELECT email
FROM booking_agent
WHERE email = %s;
```

• Insert new booking agent:
```sql
INSERT INTO booking_agent (email, password)
VALUES (%s, SHA2(%s, 256));
```
Purpose: Registers a new agent account with a hashed password.

---

**Airline Staff Registration (`register_staff`)**

• Validate that the airline exists:
```sql
SELECT name
FROM airline
WHERE name = %s;
```

• Check whether the username already exists:
```sql
SELECT username
FROM airline_staff
WHERE username = %s;
```

• Insert new staff member:
```sql
INSERT INTO airline_staff
(username, password, first_name, last_name, date_of_birth, permissions, works_for)
VALUES
(%s, SHA2(%s, 256), %s, %s, %s, %s, %s);
```
Purpose: Creates a staff account tied to a valid airline, with assigned permissions.

---
# **2. Customer Pages**

**Customer homepage (`/customer_home`)**

Feature: Show all upcoming flights with available tickets, plus origin/destination/date/time filters.

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

Then the following filters are appended depending on what the user filled in on the search form:

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

**Departure time filter (departing at or after the given time):**

```sql
AND f.departure_time >= %s
```

---
**Customer spending page**

Feature: Show total spending in the last 12 months (always visible at the top)

```sql
SELECT COALESCE(SUM(f.price), 0) AS total_spent
FROM purchases p
JOIN ticket t ON p.ticket_id = t.ticket_id
JOIN flight f ON t.for_ = f.flight_num
WHERE p.customer_email = %s
  AND p.date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH);
```

Parameters:

* `%s`: the logged-in customer’s email (`customer_email` from `session['username']`)

Feature: Default bar chart of spending per month over the last 6 months

(The Python code computes a 6-month window and passes `start_date` and `end_date`.)

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
* `%s` (2nd):`start_date` (first day of the oldest month in the 6-month window)
* `%s` (3rd): `end_date` (today’s date)

Feature: Custom date range – total spending over user-selected period

(Used when the user submits start_date and end_date in the form.)

```sql
SELECT COALESCE(SUM(f.price), 0) AS total_spent
FROM purchases p
JOIN ticket t ON p.ticket_id = t.ticket_id
JOIN flight f ON t.for_ = f.flight_num
WHERE p.customer_email = %s
  AND p.date BETWEEN %s AND %s;
```

Parameters:

* `%s` (1st) → customer email
* `%s` (2nd) → `start_d` = parsed start date from the form
* `%s` (3rd) → `end_d` = parsed end date from the form (swapped if user reversed them)


Feature: Custom date range – monthly breakdown for that period (for the bar chart)

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
* `%s` (2nd): `start_d` (custom range start)
* `%s` (3rd): `end_d` (custom range end)

The Python side then fills in “missing” months between `start_d` and `end_d` with `0` in the chart data.

---

# **4. Customer Purchases Pages**


**Feature: Show upcoming purchased flights (top table)**

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

Description:
Shows all flights the customer has purchased that are still upcoming.

---

**Feature: Show all purchased flights (bottom table)**

Base query used on first page load:

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

Description:
Displays the full history of purchases for the logged-in customer.

---

### Filters for the "All Purchased Flights" table (applied only when the user submits the form)

**Filter: start date**

```sql
AND departure_date >= %s
```

**Filter: end date**

```sql
AND departure_date < %s
```

**Filter: origin airport**

```sql
AND departs LIKE %s
```

**Filter: destination airport**

```sql
AND arrives = %s
```

Description:
These conditions are appended dynamically based on the customer’s filter input.
The query always starts with the base query shown above, and then each filter is added if the user fills in that field.

---
# **5. Customer Buying Page**


**Feature: Show selected flight details before purchase (GET /buy_cust)**

When the customer clicks on a flight from `indexCust.html`, the app loads the full flight record:

```sql
SELECT *
FROM flight
WHERE flight_num = %s;
```

Description:
Used to display all details of the chosen flight on `buyCust.html` so the customer can confirm before buying.

---

**Feature: Find an available ticket for this flight (POST /buy_cust)**

Before inserting a purchase, the system must find a ticket for that flight that has not yet been purchased:

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

Description:
Ensures that only tickets not already associated with a row in `purchases` are sold.
If no row is returned, the flight is effectively sold out.

---

**Feature: Insert a new purchase record (POST /buy_cust)**

Once an available ticket is found, the system records the purchase:

```sql
INSERT INTO purchases (customer_email, booking_agent_email, ticket_id, date)
VALUES (%s, %s, %s, CURDATE());
```

Description:
Creates a purchase entry for the logged-in customer (`customer_email`), with `booking_agent_email` set to `NULL` for direct customer purchases, and uses `CURDATE()` as the purchase date.
