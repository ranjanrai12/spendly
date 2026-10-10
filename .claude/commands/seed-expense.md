---
description: Seed realistic dummy expenses for a specific user
argument-hint: <user_id> <count> <months>
allowed-tools: Read, Bash(python3:*)
---

Read `database/db.py` to understand the expenses table schema, database connection pattern, transaction handling, and database filename. Inspect any related user or expense model files if needed.

User input: $ARGUMENTS

## Step 1 — Parse and validate arguments

Extract the following arguments from `$ARGUMENTS`:

- `user_id`: positive integer identifying an existing user.
- `count`: positive integer representing the number of expenses to create.
- `months`: positive integer representing the historical period over which expenses should be distributed.

If any argument is missing, invalid, or contains unexpected extra values, stop and display:

Usage: `/seed-expenses <user_id> <count> <months>`

Example: `/seed-expenses 1 50 6`

Reject zero or negative values. Apply reasonable limits of 1000 expenses per run and 60 months of history. If a limit is exceeded, ask the user to provide valid arguments.

## Step 2 — Inspect and verify the database

1. Read `database/db.py` and identify the actual database filename, connection helper, schema, and transaction conventions.
2. Identify all required expense fields, including the user foreign key, amount, category, description, and expense date.
3. Verify that the specified `user_id` exists in the users table.
4. If the user does not exist, stop and print:

   `No user found with id <user_id>.`

5. Do not create a user, change the schema, or modify existing records.
6. If the schema or transaction mechanism is unclear, ask for clarification rather than guessing.

## Step 3 — Generate realistic expenses

Write and execute a Python script using the existing database connection pattern.

Generate exactly `count` expenses for the specified user, distributing their dates across the past `months` calendar months, including the current month.

Use realistic Indian spending descriptions and amounts in Indian rupees (₹).

Categories and amount ranges:

- Food: ₹50–₹800
- Transport: ₹20–₹500
- Bills: ₹200–₹3,000
- Health: ₹100–₹2,000
- Entertainment: ₹100–₹1,500
- Shopping: ₹200–₹5,000
- Other: ₹50–₹1,000

Use plausible descriptions such as:

- Food: Breakfast at a local restaurant, groceries, dosa and coffee, lunch at a canteen.
- Transport: BMTC bus fare, metro recharge, auto-rickshaw, cab ride.
- Bills: Electricity bill, mobile recharge, broadband bill, water bill.
- Health: Pharmacy purchase, doctor consultation, diagnostic test.
- Entertainment: Movie tickets, streaming subscription, weekend outing.
- Shopping: Clothing, household essentials, footwear, kitchen supplies.
- Other: Stationery, small household repairs, miscellaneous personal expenses.

Choose categories with realistic proportions: Food should be most common, followed by Transport and Bills; Health and Entertainment should be less common.

Ensure each amount falls within its category's specified range. Use valid dates and realistic descriptions. Distribute expenses across the requested historical period rather than placing them all on the same date.

## Step 4 — Insert safely

1. Generate the complete dataset before inserting records.
2. Use the existing database connection helper and database filename. Never hardcode a separate database path.
3. Use parameterized SQL queries for all values.
4. Insert all records within a single transaction.
5. If any insertion fails, roll back the entire transaction so that no partial batch is committed.
6. Commit only after all `count` records have been inserted successfully.
7. Follow the existing project's database connection and cleanup conventions.
8. Do not delete, update, or overwrite existing expenses.
9. Do not claim success if the transaction fails.
10. If the database is production or its environment cannot be determined, ask for confirmation before writing data.

## Step 5 — Verify and report

After the transaction commits successfully, report:

- User ID
- Number of expenses inserted
- Total amount of expenses inserted
- Earliest and latest expense dates
- A sample of up to 5 inserted records, showing ID, date, category, amount, and description

Verify that the inserted records belong to the specified user and that the expected number of records was created.

If any operation fails, report the failure and whether the transaction was rolled back. Never report uncommitted records as successfully inserted.