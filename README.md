# Airline Reservation System

**Databases – CSCI-SHU 213 (NYU Shanghai)**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Framework-lightgrey.svg)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange.svg)
![Status](https://img.shields.io/badge/Project-Class%20Assignment-success.svg)

A full-stack web application built with **Flask (Python)** and **MySQL** for managing airline ticket reservations.
Created as a course project for **Databases (CSCI-SHU 213)** at **NYU Shanghai**, the system demonstrates relational database design, backend data handling, SQL joins and aggregates, and role-based access control.

The platform supports three roles — **Customer**, **Booking Agent**, and **Airline Staff** — each with their own authentication flow and features including searching flights, purchasing tickets, analytics dashboards, and staff-side operations.

---

## Table of Contents

* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Running-the-Application](#running-the-application)
* [Database-Setup](#database-setup)
* [Project-Structure](#project-structure)
* [Features](#features)
* [Notes](#notes)

---

## Prerequisites

* Python 3.9 or newer
* MySQL Server and phpMyAdmin or MySQL Workbench
* pip package manager
* Optional: Python virtual environment

---

## Installation

Install dependencies from the project root:

```sh
pip install -r requirements.txt
```

---

## Running the Application

Start the Flask development server:

```sh
python -u flaskr/__init__.py
```

Open the application in your browser:

```
http://127.0.0.1:5000
```

---

## Database Setup

1. Create a MySQL database named:

```
Airline_Reservation_System
```

2. Import your SQL schema into the database, or manually create the tables.
3. Update your MySQL credentials inside:

```
flaskr/__init__.py
```

Example:

```python
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='YOUR_PASSWORD',
        database='Airline_Reservation_System'
    )
```

---

## Project Structure

```
flaskr/
    __init__.py          # Flask app, routes, DB queries, authentication
    templates/           # HTML templates (Jinja2)
    static/              # CSS and images

requirements.txt
README.md
```

---

## Features

### Customer

* Search flights by departure/arrival airports and date
* Purchase tickets (with server-side capacity checks)
* View upcoming and past flights
* Spending dashboard with total spending and monthly bar chart

### Booking Agent

* Purchase tickets on behalf of customers
* View all tickets sold
* Commission analytics for the past 30 days
* Top customers by number of tickets purchased

### Airline Staff

* View all flights for their airline
* Create new flights
* Update flight status (on-time, delayed, etc.)
* Add airports and airplanes
* Staff analytics:

  * Top booking agents
  * Most frequent customers
  * Monthly ticket sales
  * Delay vs. on-time statistics
  * Top destinations

---

## Notes

* All SQL queries use parameterized inputs for safety.
* Plotly is used to generate analytics visualizations.
* This project was built for educational purposes and is not production-ready.
