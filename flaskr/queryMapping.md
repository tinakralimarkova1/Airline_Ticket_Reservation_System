
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
