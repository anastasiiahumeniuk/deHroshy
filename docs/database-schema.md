# deHroshy — Initial Database Schema

## 1. User

Represents an application user.

### Fields

| Field | Type | Constraints |
|---|---|---|
| id | Integer | Primary Key |
| email | String | NOT NULL, UNIQUE |
| password_hash | String | NOT NULL |
| created_at | DateTime | NOT NULL |

### Relationships

- One User can have many Accounts.
- One User can have many Categories.
- One User can have many MonthlyRecords.

---

## 2. Account

Represents a financial account owned by a user.

Examples:
- Monobank
- PrivatBank
- Cash

### Fields

| Field | Type | Constraints |
|---|---|---|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → users.id, NOT NULL |
| name | String | NOT NULL |
| type | String | NOT NULL |
| is_active | Boolean | NOT NULL |
| created_at | DateTime | NOT NULL |

### Constraints

- Account names must be unique within one user.
- A user may have multiple accounts.
- A user may access only their own accounts.

---

## 3. Category

Represents an income or expense category.

Categories are created for each user. A starter set may be created when the user registers, but all categories remain editable by the user.

Example starter categories:

### Expenses
- Food
- Transport
- Shopping
- Health
- Entertainment
- Home
- Subscriptions

### Income
- Salary
- Freelance
- Other income

Users may:
- create their own categories;
- rename categories;
- deactivate categories;
- remove unused categories according to business rules.

### Fields

| Field | Type | Constraints |
|---|---|---|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → users.id, NOT NULL |
| name | String | NOT NULL |
| type | Enum / String | INCOME or EXPENSE, NOT NULL |
| is_active | Boolean | NOT NULL |
| created_at | DateTime | NOT NULL |

### Constraints

- Category belongs to one user.
- Category type must be either INCOME or EXPENSE.
- Category name and type should be unique within one user.

---

## 4. MonthlyRecord

Represents an aggregated financial amount for a particular month, account, and category.

Example:

- Month: October 2026
- Account: Monobank
- Category: Food
- Amount: 8200 UAH

### Fields

| Field | Type | Constraints |
|---|---|---|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → users.id, NOT NULL |
| account_id | Integer | Foreign Key → accounts.id, NOT NULL |
| category_id | Integer | Foreign Key → categories.id, NOT NULL |
| year | Integer | NOT NULL |
| month | Integer | NOT NULL |
| amount | Numeric(12,2) | NOT NULL |
| comment | Text | Nullable |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

### Constraints

- Amount must be greater than zero.
- Month must be between 1 and 12.
- Year must be greater than zero.
- Account must belong to the same user as the MonthlyRecord.
- Category must belong to the same user as the MonthlyRecord.
- Record type is determined through Category.type and is not duplicated in MonthlyRecord.

---

## Relationships

```text
User
 ├── 1:N Account
 ├── 1:N Category
 └── 1:N MonthlyRecord

Account
 └── 1:N MonthlyRecord

Category
 └── 1:N MonthlyRecord
```

## Primary Keys

All entities use an integer `id` as the primary key.

## Foreign Keys

```text
accounts.user_id
    → users.id

categories.user_id
    → users.id

monthly_records.user_id
    → users.id

monthly_records.account_id
    → accounts.id

monthly_records.category_id
    → categories.id
```

## Money Representation

Financial values must not use floating-point numbers.

Database:

```text
NUMERIC(12, 2)
```

Python:

```text
Decimal
```

This avoids floating-point precision errors in financial calculations.