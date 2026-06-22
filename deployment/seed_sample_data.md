# Sample Seed Data

Use the following sequence to populate a demonstration event:

```bash
python manage.py import_standard_items --replace
python manage.py seed_sample_data --replace
```

This loads:

- a sample event
- upashrays
- volunteers
- vendors
- sponsors
- requirements and requirement lines
- sponsorship commitments and receipts
- purchase orders and goods receipts
- distribution batches and lines
- donations and fund transactions

The command is safe to re-run with `--replace` for the sample event.
