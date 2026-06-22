# KMM Chaturmas ERP Module Flow

## 1. Login and Landing

After authentication, the user lands on the Item Control Center.

Why:

- It answers the operational questions committee members ask most often.
- It is the best single screen for shortage, coverage, stock, and purchase decisions.
- It reduces the need to jump between modules during daily operations.

## 2. Item Control Center Flow

Display columns:

- Item
- Required
- Sponsored
- Received
- Purchase Needed
- Stock
- Distributed
- Balance

Filters:

- Event
- Category
- Pending only
- Fully covered
- Shortage

This screen should be driven by service-layer summary queries over requirements, sponsorships, inventory, and distribution records.

## 3. Requirement Flow

1. Select event.
2. Create requirement header for an upashray.
3. Add one or more item lines.
4. Save the requirement.
5. Recalculate demand summaries.
6. Raise alerts for shortages or urgent items.

Special requirements may be added separately and should appear on the dashboard immediately.

## 4. Sponsorship Flow

1. Create sponsor master record.
2. Enter commitment by item and quantity.
3. Track status as discussion, committed, partially received, completed, or cancelled.
4. When material is received, create a material receipt record.
5. Convert the receipt into an inventory transaction.
6. Recompute sponsored, received, and purchase-needed figures.

Business rule:

- Sponsorship coverage influences procurement need.
- Receipt creates inventory movement only when material is actually received.

## 5. Vendor and Procurement Flow

1. Add or update vendor data.
2. Store vendor quotes for items.
3. Compare rates and policies.
4. Highlight the preferred vendor automatically using business rules.
5. Generate purchase orders for unmet demand.
6. Receive goods against a purchase order.
7. Create inventory transactions on receipt.

Purchase need formula:

`Purchase Required = Total Requirement - Sponsored Received - Current Stock`

The formula must be computed automatically and never manually entered.

## 6. Inventory Flow

1. A source event creates a stock movement.
2. The system writes an `InventoryTransaction` row.
3. Current stock is recalculated from the ledger.
4. Dashboard totals and item control summaries refresh from projections.

Supported movements:

- Purchase receipt
- Donation receipt
- Sponsorship receipt
- Distribution
- Return
- Damage
- Adjustment

No user screen should directly edit on-hand quantity.

## 7. Distribution Flow

1. Create a distribution batch.
2. Assign a volunteer.
3. Add distribution lines by upashray and item.
4. Mark dispatch.
5. Mark delivery.
6. Create the inventory outflow transaction.
7. Update upashray completion progress.

Distribution statuses:

- Pending
- Dispatched
- Delivered
- Partial

## 8. Additional Requirement Flow

1. Volunteer opens mobile screen.
2. Selects event and upashray.
3. Adds required item, quantity, urgency, and remarks.
4. Optionally uploads a photo.
5. Saves the request.
6. The request appears immediately in the dashboard queue.

This flow must be lightweight for field use on mobile browsers.

## 9. Donation and Fund Flow

### Monetary donations

1. Record donor details.
2. Record amount, mode, and reference person.
3. Save donation.
4. Summarize into fund dashboards.

### Fund transactions

1. Record income, expense, transfer, or adjustment.
2. Recalculate available balance.
3. Show committed expense and projected balance in dashboard widgets.

## 10. Reporting Flow

Reports should be available by:

- PDF
- Excel
- Print-friendly HTML

Operational reports:

- Upashray summary
- Item summary
- Vendor comparison
- Purchase report
- Donation report
- Sponsorship report
- Distribution report
- Fund report
- Volunteer report
- Inventory report

## 11. Alerts Flow

Alerts are derived from business state, not manually created.

Trigger conditions:

- Low stock
- Pending sponsorship
- Pending distribution
- Pending procurement
- Pending requirement collection
- Overdue commitment

Alerts should surface on the dashboard and on relevant module screens.

## 12. Import Flow

Importers should be staged and reversible before commit.

Recommended sequence:

1. Upload file
2. Map columns if necessary
3. Validate rows
4. Display preview and errors
5. Commit valid rows
6. Log import activity

Required import targets:

- Items
- Upashrays
- Volunteers
- Sponsors
- Vendor rates

## 13. Audit Flow

Every important action should:

1. Save the main business record.
2. Create any derived transaction or status record.
3. Write an activity log entry.
4. Preserve old and new values where practical.

Audit logs must support compliance review and operational traceability.

