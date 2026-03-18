# International FIDE Data Management System

## 1. Introduction
The International FIDE Data Management System is a database-driven application designed to store, manage, and analyze chess player data based on FIDE (Fédération Internationale des Échecs) standards. The system focuses on handling large-scale datasets efficiently while demonstrating core Database Management System (DBMS) concepts.

This project was developed as part of a DBMS course to showcase database design, normalization, query optimization, and implementation of advanced database features.

---

## 2. Objectives
- Design a structured and normalized relational database  
- Efficiently manage large datasets (100,000+ records)  
- Enable fast retrieval and analysis of player data  
- Implement stored procedures and triggers  
- Provide a simple interface for interacting with the database  

---

## 3. Features
- Player login system  
- Player profile dashboard displaying ratings  
- Search functionality using player name or FIDE ID  
- Sorting and ranking of players  
- Efficient handling of large datasets  
- Use of stored procedures for complex operations  
- Triggers to maintain data integrity  
- Optimized SQL queries for performance  

---

## 4. Technology Stack
- Database: MySQL  
- Backend: Python (Flask)  
- Frontend: HTML, CSS  
- Version Control: Git and GitHub  

---

## 5. System Architecture
The system follows a three-tier architecture:

1. Presentation Layer (Frontend)  
   - HTML and CSS used for user interface  

2. Application Layer (Backend)  
   - Flask handles routing and business logic  

3. Data Layer (Database)  
   - MySQL stores and manages all data  

---

## 6. Database Design

### 6.1 Tables

**players**
- fide_id (Primary Key)  
- name  
- country  
- gender  
- birth_year  

**ratings**
- fide_id (Foreign Key)  
- standard_rating  
- rapid_rating  
- blitz_rating  

**tournaments**
- tournament_id (Primary Key)  
- tournament_name  
- location  
- date  

**results**
- result_id (Primary Key)  
- fide_id (Foreign Key)  
- tournament_id (Foreign Key)  
- score  

---

### 6.2 Relationships
- One player can have one rating record  
- One player can participate in multiple tournaments  
- Each tournament can have multiple players  
- Results table connects players and tournaments  

---

## 7. DBMS Concepts Used
- Normalization (up to 3NF)  
- Primary Key and Foreign Key constraints  
- Joins for data retrieval  
- Indexing for faster queries  
- Stored Procedures  
- Triggers  
- Aggregate functions  

---

## 8. Setup Instructions

### 8.1 Prerequisites
- MySQL installed  
- Python 3.x installed  
- Git installed  

---

### 8.2 Clone the Repository
```bash
git clone https://github.com/your-username/fide-dbms-project.git
cd fide-dbms-project
