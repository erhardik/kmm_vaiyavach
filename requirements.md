# Kalyan Mitra Mandal Chaturmas ERP

## Master Development Specification for Codex

### Objective

Build a production-ready, scalable, multi-user web application for Kalyan Mitra Mandal to manage the complete Chaturmas Vaiyavach operation from requirement collection to procurement, sponsorship, inventory, distribution, fund management, reporting, and volunteer coordination.

The application must eliminate dependency on WhatsApp groups, Excel files, phone calls, and manual tracking.

The system must support multiple simultaneous users with role-based permissions and real-time visibility of event progress.

---

# Technology Stack

Backend:

* Django 5+
* Python 3.12

Frontend:

* Bootstrap 5
* HTMX (optional)
* Responsive Mobile First Design

Database:

* SQLite (Development)
* MySQL/MariaDB (Production)

Hosting:

* PythonAnywhere

Authentication:

* Django Authentication

File Storage:

* Local Media Storage
* Future AWS S3 Compatible

Architecture:

* Modular Django Apps
* Service Layer Architecture
* Repository Pattern where possible

---

# Core Business Concepts

Everything revolves around:

1. Upashray
2. Item
3. Requirement
4. Vendor
5. Sponsorship
6. Inventory
7. Distribution
8. Volunteer
9. Fund
10. Reports

---

# User Roles

## Super Admin

Full Access

Can:

* Manage users
* Configure system
* View all reports
* Approve expenses
* Manage masters

---

## Procurement Team

Can:

* Manage vendors
* Add quotations
* Create purchase orders
* Receive inventory

Cannot:

* Delete transactions

---

## Sponsorship Team

Can:

* Add sponsors
* Track commitments
* Update received material

---

## Distribution Team

Can:

* View assigned deliveries
* Mark delivery status
* Add additional requirements

---

## Accounts Team

Can:

* Manage funds
* Manage donations
* Record expenses

---

## Viewer

Read-only access

---

# Module 1: Master Data

## Item Master

Fields

id
item_code
item_name
category
unit
default_size
description
estimated_rate
active

Categories

General
Stationery
Medical
Ayurvedic
Color Material

Import all standard items from Vaiyavach PDF. 

---

## Upashray Master

Fields

id
name
area
address
city
contact_person
mobile
maharaj_name
entry_date
status

Status

Planning
Requirement Pending
Requirement Received
Procurement In Progress
Distribution Pending
Completed

---

## Volunteer Master

Fields

id
name
mobile
email
area
vehicle_available
remarks

---

# Module 2: Requirement Collection

One Upashray can have multiple requirements.

## Requirement Header

id
upashray_id
created_by
requirement_date
remarks

---

## Requirement Items

id
requirement_id
item_id
required_qty

---

## Special Requirement

id
upashray_id
description
priority
status

Priority

Low
Medium
High
Urgent

---

# Module 3: Vendor Management

## Vendor Master

id
vendor_name
contact_person
mobile
address
gst_no
remarks

---

## Vendor Quotes

id
vendor_id
item_id

rate

home_delivery

pickup_available

return_unused

credit_days

gst_included

quote_date

remarks

System should automatically highlight:

* Lowest rate
* Best return policy
* Preferred vendor

---

# Module 4: Sponsorship Management

Most important module.

---

## Sponsor Master

id
sponsor_name
mobile
address
organization
reference_volunteer_id

---

## Sponsorship Commitment

id
sponsor_id
item_id

committed_qty

received_qty

expected_date

status

remarks

Status

Discussion
Committed
Partially Received
Completed
Cancelled

---

## Sponsorship Dashboard

For each item display:

Required Qty

Sponsored Qty

Received Qty

Purchase Qty

Pending Qty

Color indicators

Green = Covered

Yellow = Partially Covered

Red = Pending

---

# Module 5: Procurement Planning Engine

Automatic calculations.

Formula

Purchase Required =
Total Requirement
Minus
Sponsored Received
Minus
Current Stock

System auto calculates.

No manual entry.

---

# Module 6: Purchase Management

## Purchase Order

id
vendor_id
po_number
date
status

---

## Purchase Order Items

item
qty
rate

---

## Goods Receipt

id
purchase_order
date

received_by

remarks

Inventory automatically updated.

---

# Module 7: Inventory Management

Single source of truth.

Never directly edit stock.

Everything must be transaction based.

---

## Inventory Transactions

id

item_id

transaction_type

qty

source

reference_id

remarks

created_at

Transaction Types

Purchase

Donation

Distribution

Return

Adjustment

Damage

---

## Inventory Dashboard

Current Stock

Reserved Stock

Available Stock

Pending Requirement

Shortage

---

# Module 8: Distribution Planning

## Distribution Batch

id
batch_name
date
assigned_volunteer

---

## Distribution Details

upashray

item

required

dispatched

delivered

balance

status

Status

Pending
Dispatched
Delivered
Partial

---

# Module 9: Additional Requirement System

Volunteer can create new requirement from mobile.

Fields

upashray

item

qty

urgency

remarks

photo

Immediately visible on dashboard.

---

# Module 10: Donation Management

## Monetary Donations

id

donor_name

mobile

amount

mode

reference_person

remarks

---

## Material Donations

Handled through Sponsorship Module

Not through inventory directly.

Material received must create inventory transaction.

---

# Module 11: Fund Management

## Fund Transactions

id

transaction_type

category

amount

date

remarks

Transaction Types

Income

Expense

Transfer

Adjustment

---

Dashboard

Total Collection

Total Expense

Available Balance

Committed Expense

Projected Balance

---

# Module 12: Alerts Engine

Automatic Alerts

Low Stock

Pending Sponsorship

Pending Distribution

Pending Procurement

Pending Requirement Collection

Overdue Commitment

Displayed on dashboard.

---

# Module 13: Analytics

Item Wise Requirement

Item Wise Sponsorship

Vendor Rate Comparison

Volunteer Contribution

Fund Utilization

Area Wise Distribution

Upashray Completion %

---

# Module 14: Dashboard

Home Screen

Cards

Total Upashray

Total Requirement Value

Total Sponsorship Value

Fund Available

Pending Procurement

Pending Distribution

Pending Alerts

---

Charts

Requirement vs Delivered

Sponsored vs Purchased

Fund Collection Trend

Distribution Progress

---

# Module 15: Reports

PDF

Excel

Print Friendly

Reports

Upashray Summary

Item Summary

Vendor Comparison

Purchase Report

Donation Report

Sponsorship Report

Distribution Report

Fund Report

Volunteer Report

Inventory Report

---

# Automation Rules

When Requirement Saved

Recalculate Item Demand

---

When Sponsorship Received

Update Inventory

Recalculate Purchase Need

---

When Purchase Received

Update Inventory

Recalculate Stock

---

When Distribution Done

Reduce Inventory

Update Upashray Progress

---

When Additional Requirement Added

Increase Demand

Trigger Alert

---

# Non Functional Requirements

Mobile Responsive

Works on Low Internet

Bootstrap UI

Fast Loading

Audit Trail

Soft Delete

Role Based Security

CSV Import Export

Backup Database Option

Activity Logs

Pagination

Search Everywhere

Filters Everywhere

---

# Future Expansion

QR Based Distribution

WhatsApp Integration

Barcode Inventory

Multiple Events

Multi City Support

Multi Organization Support

Android App

API Layer

Public Donor Portal

Public Sponsorship Portal

Payment Gateway

Geo Tracking

---

Expected Scale

1000+ Sponsors

500+ Volunteers

500+ Upashray

10000+ Inventory Transactions

100 Concurrent Users

Must be designed to support scaling without major schema redesign.

Create an **Item Funding Matrix**.

Example:

| Item | Required | Sponsored | Received | Purchased | Stock | Delivered | Balance |
| ---- | -------- | --------- | -------- | --------- | ----- | --------- | ------- |

This single screen will become the command center for the entire event. Most committee members will probably spend 80% of their time on this page because it instantly answers:

* What is still needed?
* Who promised it?
* Has it arrived?
* Do we need to buy it?
* Has it been distributed?

slightly modify the architecture so Codex generates a production-ready GitHub-first Django project instead of a PythonAnywhere-first project.

Add these requirements to the Codex specification:

Deployment Architecture

Repository Structure

kmm-chaturmas-erp/

├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── deployment/
│   └── pythonanywhere.md
├── media/
├── static/
├── config/
│   ├── settings.py
│   ├── settings_dev.py
│   ├── settings_prod.py
│   └── urls.py
├── apps/
│   ├── accounts/
│   ├── masters/
│   ├── requirements/
│   ├── sponsorship/
│   ├── vendors/
│   ├── procurement/
│   ├── inventory/
│   ├── distribution/
│   ├── funds/
│   ├── reports/
│   └── dashboard/
Git Workflow
Main Branch

Production

main
Development Branch
develop
Feature Branches
feature/vendor-module

feature/sponsorship-module

feature/inventory-module
Environment Variables

Never hardcode anything.

SECRET_KEY=

DEBUG=

ALLOWED_HOSTS=

DATABASE_URL=

EMAIL_HOST=

EMAIL_USER=

EMAIL_PASSWORD=
PythonAnywhere Deployment

PythonAnywhere should only:

Pull Latest Code
git pull origin main
Install Dependencies
pip install -r requirements.txt
Run Migrations
python manage.py migrate
Collect Static
python manage.py collectstatic --noinput
Reload Web App

Done.

Database Strategy
Phase 1

SQLite

Before Event Goes Live

Switch to MySQL.

Reason:

SQLite becomes risky when:

Procurement team enters data
Distribution team updates delivery
Accounts updates funds

at the same time.

MySQL handles concurrent writes much better.

Daily Backup System

Create admin button:

Backup Database

Exports:

backup_2026_06_18.sql

Store under:

/backup/

Allow download from admin.

Import System

Very important.

Create Excel importers for:

Items
Upashray
Volunteers
Sponsors
Vendor Rates

Committee members will never enter 500 records manually.

Audit Trail

Every change must be logged.

Table:

activity_log

Fields:

user

action

module

record_id

old_value

new_value

timestamp

Example:

Hardik Shah

Updated Sponsorship

Item #45

Qty 100 → 150

18-Jun-2026 11:32 AM
Smart Dashboard Widgets
Requirement Completion
78%
Sponsorship Coverage
62%
Procurement Coverage
55%
Distribution Coverage
20%
Fund Position
Collected

Spent

Available
Critical Screen

Tell Codex:

Build this screen first after login.

Item Control Center
Item	Required	Sponsored	Received	Purchase Needed	Stock	Distributed

Filters:

Category
Pending Only
Fully Covered
Shortage

This becomes the war room screen.

Future Multi-Year Support

Don't hardcode 2025.

Create:

event

table.

Example:

Chaturmas 2025

Chaturmas 2026

Paryushan 2026

Vaiyavach 2027

Every record must belong to an event.

This single decision will save you from rebuilding the software next year.

Final Instruction for Codex

Ask Codex to generate:

Complete Django project
Models
Admin
Migrations
Bootstrap UI
Authentication
CRUD screens
Dashboard
Reports
Excel import/export
Role permissions
Activity logs
Production deployment files
README with setup instructions

Generate the application as a maintainable enterprise ERP, not as a collection of forms. All calculations must be automatic and derived from transactions. No inventory quantity should ever be manually edited. Every stock movement must create a transaction record.
