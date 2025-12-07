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
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database-Setup](#database-setup)
- [Running-the-Application](#running-the-application)
- [Project-Structure](#project-structure)
- [Features](#features)
- [Notes](#notes)

---

## Prerequisites
- Python 3.9 or newer  
- MySQL Server and phpMyAdmin or MySQL Workbench  
- pip package manager  
- Optional: Python virtual environment  

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
http://127.0.0.1:5000
