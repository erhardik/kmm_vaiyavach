# KMM Chaturmas ERP Database Schema

## 1. Schema Design Goals

The database must support:

- Event scoping everywhere
- Transaction-ledger inventory
- Auditability
- Production concurrency
- Multi-year event history

The schema is designed to avoid direct stock mutation and to keep all operational calculations reproducible.

## 2. Shared Base Fields

Most business tables should inherit common fields:

- `id`
- `event`
- `created_at`
- `updated_at`
- `created_by`
- `updated_by`
- `is_active`
- `is_deleted`

High-value transactional tables should also support:

- `status`
- `status_changed_at`
- `status_changed_by`
- `remarks`

## 3. Core Tables

### Event

Represents a Chaturmas or related operational cycle.

Fields:

- `id`
- `name`
- `slug`
- `start_date`
- `end_date`
- `location`
- `status`
- `is_current`

Constraints:

- `slug` unique
- one active event can be marked current at a time through application logic

### User Profile / Role Mapping

Use Django auth plus a profile or role mapping table for operational metadata.

Fields:

- `user`
- `event` if event-specific access is required
- `role`
- `mobile`
- `designation`

### ActivityLog

Append-only activity log.

Fields:

- `user`
- `event`
- `action`
- `module`
- `record_id`
- `old_value`
- `new_value`
- `timestamp`
- `ip_address`
- `user_agent`

## 4. Master Data

### Item

Fields:

- `event`
- `item_code`
- `item_name`
- `category`
- `unit`
- `default_size`
- `description`
- `estimated_rate`
- `is_active`

Recommended constraints:

- unique `(event, item_code)`
- indexed `(event, category, is_active)`

### Upashray

Fields:

- `event`
- `name`
- `area`
- `address`
- `city`
- `contact_person`
- `mobile`
- `maharaj_name`
- `entry_date`
- `status`
- `is_active`

### Volunteer

Fields:

- `event`
- `name`
- `mobile`
- `email`
- `area`
- `vehicle_available`
- `remarks`
- `is_active`

### Sponsor

Fields:

- `event`
- `sponsor_name`
- `mobile`
- `address`
- `organization`
- `reference_volunteer`
- `is_active`

### Vendor

Fields:

- `event`
- `vendor_name`
- `contact_person`
- `mobile`
- `address`
- `gst_no`
- `remarks`
- `is_active`

## 5. Requirement Collection

### RequirementHeader

Fields:

- `event`
- `upashray`
- `created_by`
- `requirement_date`
- `remarks`
- `status`

### RequirementLine

Fields:

- `event`
- `requirement`
- `item`
- `required_qty`
- `remarks`

Constraints:

- unique `(requirement, item)`

### SpecialRequirement

Fields:

- `event`
- `upashray`
- `description`
- `priority`
- `status`
- `photo`
- `created_by`

## 6. Sponsorship

### SponsorshipCommitment

Fields:

- `event`
- `sponsor`
- `item`
- `committed_qty`
- `received_qty`
- `expected_date`
- `status`
- `remarks`

Constraints:

- unique `(event, sponsor, item)` unless multiple commitment rows are explicitly desired

### SponsorMaterialReceipt

Tracks actual receipt against a commitment or sponsor donation.

Fields:

- `event`
- `commitment`
- `item`
- `received_qty`
- `received_date`
- `received_by`
- `inventory_transaction`
- `remarks`

## 7. Vendor and Procurement

### VendorQuote

Fields:

- `event`
- `vendor`
- `item`
- `rate`
- `home_delivery`
- `pickup_available`
- `return_unused`
- `credit_days`
- `gst_included`
- `quote_date`
- `remarks`

### PurchaseOrder

Fields:

- `event`
- `vendor`
- `po_number`
- `date`
- `status`
- `created_by`
- `remarks`

### PurchaseOrderLine

Fields:

- `event`
- `purchase_order`
- `item`
- `qty`
- `rate`
- `tax_amount`
- `line_total`

### GoodsReceipt

Fields:

- `event`
- `purchase_order`
- `date`
- `received_by`
- `remarks`
- `inventory_transaction_reference`

## 8. Inventory

### InventoryTransaction

This is the source of truth for stock movement.

Fields:

- `event`
- `item`
- `transaction_type`
- `qty_in`
- `qty_out`
- `source_module`
- `reference_id`
- `reference_label`
- `unit_rate`
- `remarks`
- `created_by`
- `created_at`
- `reversal_of`

Recommended transaction types:

- `PURCHASE`
- `DONATION`
- `SPONSORSHIP_RECEIPT`
- `DISTRIBUTION`
- `RETURN`
- `ADJUSTMENT`
- `DAMAGE`
- `RESERVATION`
- `RELEASE`

### InventoryProjection

Optional fast-read model, if the project needs it later.

Fields:

- `event`
- `item`
- `current_stock`
- `reserved_stock`
- `available_stock`
- `distributed_stock`
- `updated_at`

This table must be fully derivable from `InventoryTransaction`.

## 9. Distribution

### DistributionBatch

Fields:

- `event`
- `batch_name`
- `date`
- `assigned_volunteer`
- `status`

### DistributionLine

Fields:

- `event`
- `distribution_batch`
- `upashray`
- `item`
- `required_qty`
- `dispatched_qty`
- `delivered_qty`
- `balance_qty`
- `status`

Constraints:

- unique `(distribution_batch, upashray, item)`

## 10. Funds

### Donation

For monetary donations.

Fields:

- `event`
- `donor_name`
- `mobile`
- `amount`
- `mode`
- `reference_person`
- `received_date`
- `remarks`
- `created_by`

### FundTransaction

Fields:

- `event`
- `transaction_type`
- `category`
- `amount`
- `date`
- `remarks`
- `reference_module`
- `reference_id`
- `created_by`

Transaction types:

- `INCOME`
- `EXPENSE`
- `TRANSFER`
- `ADJUSTMENT`

## 11. Audit and Attachments

### Attachment

Use a generic attachment table for PDFs, images, and scans.

Fields:

- `event`
- `content_type`
- `object_id`
- `file`
- `file_name`
- `uploaded_by`
- `uploaded_at`

### StatusHistory

Recommended for workflow-heavy records.

Fields:

- `event`
- `content_type`
- `object_id`
- `from_status`
- `to_status`
- `changed_by`
- `changed_at`
- `remarks`

## 12. Derived Views and Query Patterns

Useful summary queries include:

- Item demand by event
- Sponsorship coverage by item
- Current stock by item
- Purchase need by item
- Distribution progress by upashray
- Fund balances by category

Prefer database annotations and grouped queries for these reads instead of Python-side aggregation loops.

## 13. Indexing Strategy

Add indexes on:

- `event`
- foreign keys
- `item_code`
- `mobile`
- `status`
- `created_at`
- `transaction_type`

Add composite indexes for common dashboard queries such as:

- `(event, item)`
- `(event, status)`
- `(event, upashray)`
- `(event, created_at)`

## 14. Concurrency and Integrity

- Use atomic transactions for all workflow mutations.
- Use row-level locking only where necessary for counters and approvals.
- Prevent concurrent stock edits by making inventory writes append-only.
- Recalculate projections after committed writes.
- Never trust UI totals as the source of truth.

