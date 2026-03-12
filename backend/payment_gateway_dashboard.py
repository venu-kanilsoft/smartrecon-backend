"""
Payment Gateway Charges custom dashboard – APIs for filter options and widget data.
Uses PostgreSQL table "PG_final". Set PG_DATABASE_URL in environment for live data.
"""
import os
import logging
import typing
import fastapi
import framework
from fastapi import Query

logger = logging.getLogger(__name__)

# Mount under /reporting via dashboard_actions.router.include_router(pg_router)
router = fastapi.APIRouter(tags=["Reporting"])

# Optional PostgreSQL connection. If not set, endpoints return empty data.
def _get_pg_connection():
    try:
        import psycopg2
        url = str(framework.settings.db_urls["postgres"][0])
        # url = os.environ.get("PG_DATABASE_URL") or os.environ.get("DATABASE_URL")
        if not url:
            return None
        return psycopg2.connect(url)
    except Exception as e:
        logger.warning("PG connection not available: %s", e)
        return None


def _build_filter_clause_and_params(
    card_type: typing.Optional[str],
    payment_gateway: typing.Optional[str],
    transaction_date: typing.Optional[str],
    settlement_month: typing.Optional[str],
) -> tuple:
    """Returns (sql_and_clause, params_sequence) for WHERE. Uses %s placeholders and a tuple so all drivers accept it."""
    conditions = ["NOT \"Card Type\" IS NULL"]
    params = []
    if card_type:
        conditions.append("\"Card Type\" = %s")
        params.append(card_type)
    if payment_gateway:
        conditions.append("\"Payment Gateway\" = %s")
        params.append(payment_gateway)
    if transaction_date:
        conditions.append("\"Transaction Date\"::date = %s")
        params.append(transaction_date)
    if settlement_month:
        conditions.append("TO_DATE(\"Settlement Month Year\", 'Mon-YYYY') = TO_DATE(%s, 'Mon-YYYY')")
        params.append(settlement_month)
    return " AND ".join(conditions), tuple(params)


def _inject_filter_into_query(base_query: str, filter_where: str) -> str:
    """Inject filter into query by adding WHERE after FROM \"PG_final\" in the innermost subquery."""
    # Insert after the first occurrence of FROM "PG_final" (the base table)
    marker = "FROM \"PG_final\""
    if marker not in base_query:
        return base_query
    return base_query.replace(marker, f"FROM \"PG_final\" WHERE {filter_where}", 1)


# ---- Filter options ----

@router.get("/pg_charges/filters")
async def get_pg_charges_filters():
    """Return distinct values for Card Type, Payment Gateway, Transaction Date, Settlement Month."""
    conn = _get_pg_connection()
    if not conn:
        return {
            "card_types": [],
            "payment_gateways": [],
            "transaction_dates": [],
            "settlement_months": [],
        }
    out = {
        "card_types": [],
        "payment_gateways": [],
        "transaction_dates": [],
        "settlement_months": [],
    }
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT DISTINCT "Card Type" FROM "PG_final" WHERE "Card Type" IS NOT NULL ORDER BY 1')
            out["card_types"] = [r[0] for r in cur.fetchall()]
            cur.execute('SELECT DISTINCT "Payment Gateway" FROM "PG_final" WHERE "Payment Gateway" IS NOT NULL ORDER BY 1')
            out["payment_gateways"] = [r[0] for r in cur.fetchall()]
            cur.execute('SELECT DISTINCT "Transaction Date"::date FROM "PG_final" ORDER BY 1 DESC')
            out["transaction_dates"] = [r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]) for r in cur.fetchall()]
            cur.execute('SELECT DISTINCT "Settlement Month Year" FROM "PG_final" ORDER BY 1 DESC')
            out["settlement_months"] = [r[0] for r in cur.fetchall()]
    except Exception as e:
        logger.exception("Error fetching PG filter options")
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return out


# ---- Widget 1: Card Type-wise Transaction Summary ----

CARD_TYPE_SUMMARY_QUERY = """
SELECT
  "Card Type" AS "Card Type",
  "Payment Gateway" AS "Payment Gateway",
  TO_CHAR(COUNT("Payment Processing Fee"), 'FM9,99,99,99,999') AS "Txn Count",
  TO_CHAR(SUM("Gross Amount"), 'FM₹999,99,99,99,99,999.00') AS "Txn Amount (Cr)",
  CONCAT('₹', TO_CHAR(SUM("Payment Processing Fee"), 'FM999,99,99,99,99,999.00')) AS "Fee (Cr)",
  TO_CHAR(
    COALESCE(
      SUM("Gross Amount") / NULLIF(SUM(SUM("Gross Amount")) OVER (PARTITION BY "Card Type"), 0),
      0
    ) * 100,
    'FM999,999,990.00'
  ) || '%%' AS "Mix%",
  COALESCE(
    TO_CHAR(
      (
        SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0)
      ) * 100,
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Rate%",
  COALESCE(
    TO_CHAR(
      MIN(
        CASE
          WHEN SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0) > 0.0001
          THEN (
            SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0)
          ) * 100
        END
      ) OVER (PARTITION BY "Card Type"),
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Lowest-Rate%",
  TO_CHAR(
    GREATEST(
      0,
      (
        COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0) - MIN(COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0)) OVER (PARTITION BY "Card Type")
      ) * 100
    ),
    'FM999,999,990.00'
  ) || '%%' AS "Delta-Rate%",
  TO_CHAR(
    (
      SUM(mix) * GREATEST(
        0,
        COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0) - MIN(COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0)) OVER (PARTITION BY "Card Type")
      )
    ) * 100,
    'FM999,999,990.00'
  ) || '%%' AS "Impact%",
  TO_CHAR(
    CAST((
      (
        CAST(COUNT("Payment Reference Number") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ) AS DECIMAL),
    'FM9,99,99,99,999'
  ) AS "Prov Txn Count",
  TO_CHAR(
    (
      (
        CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹999,99,99,99,99,999.00'
  ) AS "Prov.Amount",
  TO_CHAR(
    (
      (
        CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹999,99,99,99,99,999.00'
  ) AS "Prov.Fee",
  TO_CHAR(
    ROUND(
      (
        (
          (
            CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        ) / (
          (
            CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        )
      ) * 100,
      2
    ),
    'FM999,999,990.00'
  ) || '%%' AS "Prov.Rate(%)",
  COALESCE(
    ROUND(
      CAST(COUNT("Payment Reference Number") AS DECIMAL) * (
        CAST(EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') AS DECIMAL) / NULLIF(EXTRACT(DAY FROM MAX("Transaction Date")), 0)
      ),
      0
    ),
    0
  ) AS "Total.Txn-Count",
  TO_CHAR(
    CAST(SUM("Gross Amount") AS DECIMAL) + (
      (
        CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM (
          DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
        )) - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹99,99,99,99,99,999.00'
  ) AS "Total Txn-Amt",
  TO_CHAR(
    CAST(SUM("Payment Processing Fee") AS DECIMAL) + (
      (
        CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM (
          DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
        )) - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹99,99,99,99,99,999.00'
  ) AS "Total Fee",
  COALESCE(
    TO_CHAR(
      (
        (
          CAST(SUM("Payment Processing Fee") AS DECIMAL) + (
            (
              CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
            ) * (
              EXTRACT(DAY FROM (
                DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
              )) - EXTRACT(DAY FROM MAX("Transaction Date"))
            )
          )
        ) / NULLIF(
          CAST(SUM("Gross Amount") AS DECIMAL) + (
            (
              CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
            ) * (
              EXTRACT(DAY FROM (
                DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
              )) - EXTRACT(DAY FROM MAX("Transaction Date"))
            )
          ),
          0
        )
      ) * 100,
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Total Rate (%)",
  TO_CHAR(
    (
      CAST(SUM("Gross Amount") AS DECIMAL) + (
        (
          CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
        ) * (
          EXTRACT(DAY FROM (
            DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
          )) - EXTRACT(DAY FROM MAX("Transaction Date"))
        )
      )
    ) / NULLIF(
      SUM(
        CAST(SUM("Gross Amount") AS DECIMAL) + (
          (
            CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        )
      ) OVER (PARTITION BY "Card Type"),
      0
    ) * 100,
    'FM999,999,990.00'
  ) || '%%' AS "Total Mix(%)"
FROM (
  SELECT
    *,
    COALESCE("Gross Amount" / NULLIF(SUM("Gross Amount") OVER (PARTITION BY "Card Type"), 0), 0) AS mix
  FROM "PG_final"
) AS virtual_table
WHERE
  NOT "Card Type" IS NULL
GROUP BY
  "Card Type",
  "Payment Gateway"
ORDER BY
  "Txn Count" DESC
LIMIT 1000
"""


def _run_query_with_filters(base_sql: str, card_type: str = None, payment_gateway: str = None,
                            transaction_date: str = None, settlement_month: str = None):
    filter_where, params = _build_filter_clause_and_params(
        card_type, payment_gateway, transaction_date, settlement_month
    )
    # Inject filter into the innermost FROM "PG_final" (subquery in FROM ( SELECT ... FROM "PG_final" ) )
    sql = _inject_filter_into_query(base_sql, filter_where)
    conn = _get_pg_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


@router.get("/pg_charges/widget/card-type-summary")
async def get_pg_widget_card_type_summary(
    card_type: typing.Optional[str] = Query(None),
    payment_gateway: typing.Optional[str] = Query(None),
    transaction_date: typing.Optional[str] = Query(None),
    settlement_month: typing.Optional[str] = Query(None),
):
    """Card Type-wise Transaction Summary & Gateway Cost Efficiency Overview."""
    return _run_query_with_filters(
        CARD_TYPE_SUMMARY_QUERY,
        card_type=card_type, payment_gateway=payment_gateway,
        transaction_date=transaction_date, settlement_month=settlement_month,
    )


# ---- Widget 2: Monthly CardType Transaction Summary ----

MONTHLY_SUMMARY_QUERY = """
SELECT
  TO_DATE("Settlement Month Year", 'Mon-YYYY') AS "Month",
  "Card Type" AS "Card Type",
  "Payment Gateway" AS "Payment Gateway",
  TO_CHAR(COUNT("Payment Processing Fee"), 'FM9,99,99,99,999') AS "Txn Count",
  TO_CHAR(SUM("Gross Amount"), 'FM999,99,99,99,99,999.00') AS "Txn Amount",
  TO_CHAR(SUM("Payment Processing Fee"), 'FM999,99,99,99,99,999.00') AS "Fee",
  TO_CHAR(
    COALESCE(
      SUM("Gross Amount") / NULLIF(SUM(SUM("Gross Amount")) OVER (PARTITION BY "Card Type"), 0),
      0
    ) * 100,
    'FM999990.00'
  ) || '%%' AS "Mix(%)",
  COALESCE(
    TO_CHAR(
      (
        SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0)
      ) * 100,
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Rate(%)",
  COALESCE(
    TO_CHAR(
      MIN(
        CASE
          WHEN SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0) > 0.0001
          THEN (
            SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0)
          ) * 100
        END
      ) OVER (PARTITION BY "Card Type"),
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Lowest-Rate(%)",
  TO_CHAR(
    GREATEST(
      0,
      (
        COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0) - MIN(COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0)) OVER (PARTITION BY "Card Type")
      ) * 100
    ),
    'FM999,999,990.00'
  ) || '%%' AS "Delta-Rate(%)",
  TO_CHAR(
    (
      SUM(mix) * GREATEST(
        0,
        COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0) - MIN(COALESCE(SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0), 0)) OVER (PARTITION BY "Card Type")
      )
    ) * 100,
    'FM999,999,990.00'
  ) || '%%' AS "Impact(%)",
  TO_CHAR(
    CAST((
      (
        CAST(COUNT("Payment Reference Number") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ) AS DECIMAL),
    'FM9,99,99,99,999'
  ) AS "Prov.Txn.Count",
  TO_CHAR(
    (
      (
        CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹999,99,99,99,99,999.00'
  ) AS "Prov.Amount",
  TO_CHAR(
    (
      (
        CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹999,99,99,99,99,999.00'
  ) AS "Prov.Fee",
  TO_CHAR(
    ROUND(
      (
        (
          (
            CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        ) / (
          (
            CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        )
      ) * 100,
      2
    ),
    'FM999,999,990.00'
  ) || '%%' AS "Prov Rate(%)",
  CAST(COUNT("Payment Reference Number") AS DECIMAL) * (
    EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') / EXTRACT(DAY FROM MAX("Transaction Date"))
  ) AS "Total.Txn-Count",
  TO_CHAR(
    CAST(SUM("Gross Amount") AS DECIMAL) + (
      (
        CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM (
          DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
        )) - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹99,99,99,99,99,999.00'
  ) AS "Total.Txn.Amt",
  TO_CHAR(
    CAST(SUM("Payment Processing Fee") AS DECIMAL) + (
      (
        CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
      ) * (
        EXTRACT(DAY FROM (
          DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
        )) - EXTRACT(DAY FROM MAX("Transaction Date"))
      )
    ),
    'FM₹99,99,99,99,99,999.00'
  ) AS "Total  Fee"
FROM (
  SELECT
    *,
    COALESCE("Gross Amount" / NULLIF(SUM("Gross Amount") OVER (PARTITION BY "Card Type"), 0), 0) AS mix
  FROM "PG_final"
) AS virtual_table
WHERE
  NOT "Card Type" IS NULL
GROUP BY
  TO_DATE("Settlement Month Year", 'Mon-YYYY'),
  "Card Type",
  "Payment Gateway"
ORDER BY
  "Txn Count" DESC
LIMIT 1000
"""


@router.get("/pg_charges/widget/monthly-summary")
async def get_pg_widget_monthly_summary(
    card_type: typing.Optional[str] = Query(None),
    payment_gateway: typing.Optional[str] = Query(None),
    transaction_date: typing.Optional[str] = Query(None),
    settlement_month: typing.Optional[str] = Query(None),
):
    """Monthly CardType Transaction Summary & Gateway Cost Efficiency Overview."""
    return _run_query_with_filters(
        MONTHLY_SUMMARY_QUERY,
        card_type=card_type, payment_gateway=payment_gateway,
        transaction_date=transaction_date, settlement_month=settlement_month,
    )


# ---- Widget 3: Summary Report ----

SUMMARY_REPORT_QUERY = """
SELECT
  TO_DATE("Settlement Month Year", 'Mon-YYYY') AS "Month",
  "Payment Type" AS "Payment Type",
  "Card Type" AS "Card Type",
  COUNT("Payment Processing Fee") AS "Txn Count",
  SUM("Gross Amount") AS "Txn Amount (₹)",
  SUM("Payment Processing Fee") AS "Fee (₹)",
  TO_CHAR(
    COALESCE(
      SUM("Gross Amount") / NULLIF(SUM(SUM("Gross Amount")) OVER (PARTITION BY "Card Type"), 0),
      0
    ) * 100,
    'FM999990.00'
  ) || '%%' AS "Mix(%)",
  COALESCE(
    TO_CHAR(
      (
        SUM("Payment Processing Fee") / NULLIF(SUM("Gross Amount"), 0)
      ) * 100,
      'FM999,999,990.00'
    ) || '%%',
    '0%%'
  ) AS "Rate(%)",
  CAST((
    (
      CAST(COUNT("Payment Reference Number") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
    ) * (
      EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
    )
  ) AS DECIMAL) AS "Prov.Txn.Count",
  (
    (
      CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
    ) * (
      EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
    )
  ) AS "Prov.Amount (₹)",
  (
    (
      CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
    ) * (
      EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') - EXTRACT(DAY FROM MAX("Transaction Date"))
    )
  ) AS "Prov.Fee (₹)",
  TO_CHAR(
    ROUND(
      (
        (
          (
            CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        ) / (
          (
            CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
          ) * (
            EXTRACT(DAY FROM (
              DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
            )) - EXTRACT(DAY FROM MAX("Transaction Date"))
          )
        )
      ) * 100,
      2
    ),
    'FM999,999,990.00'
  ) || '%%' AS "Prov Rate(%)",
  CAST(COUNT("Payment Reference Number") AS DECIMAL) * (
    EXTRACT(DAY FROM DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day') / EXTRACT(DAY FROM MAX("Transaction Date"))
  ) AS "Total.Txn-Count",
  CAST(SUM("Gross Amount") AS DECIMAL) + (
    (
      CAST(SUM("Gross Amount") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
    ) * (
      EXTRACT(DAY FROM (
        DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
      )) - EXTRACT(DAY FROM MAX("Transaction Date"))
    )
  ) AS "Total.Txn.Amt (₹)",
  CAST(SUM("Payment Processing Fee") AS DECIMAL) + (
    (
      CAST(SUM("Payment Processing Fee") AS DECIMAL) / EXTRACT(DAY FROM MAX("Transaction Date"))
    ) * (
      EXTRACT(DAY FROM (
        DATE_TRUNC('MONTH', MAX("Transaction Date")) + INTERVAL '1 month - 1 day'
      )) - EXTRACT(DAY FROM MAX("Transaction Date"))
    )
  ) AS "Total  Fee (₹)"
FROM (
  SELECT
    *,
    COALESCE("Gross Amount" / NULLIF(SUM("Gross Amount") OVER (PARTITION BY "Card Type"), 0), 0) AS mix
  FROM "PG_final"
) AS virtual_table
WHERE
  NOT "Card Type" IS NULL
GROUP BY
  TO_DATE("Settlement Month Year", 'Mon-YYYY'),
  "Payment Type",
  "Card Type"
ORDER BY
  "Txn Count" DESC
LIMIT 1000
"""


@router.get("/pg_charges/widget/summary-report")
async def get_pg_widget_summary_report(
    card_type: typing.Optional[str] = Query(None),
    payment_gateway: typing.Optional[str] = Query(None),
    transaction_date: typing.Optional[str] = Query(None),
    settlement_month: typing.Optional[str] = Query(None),
):
    """Summary Report."""
    return _run_query_with_filters(
        SUMMARY_REPORT_QUERY,
        card_type=card_type, payment_gateway=payment_gateway,
        transaction_date=transaction_date, settlement_month=settlement_month,
    )


# ---- Widget 4: Payment Gateway Transaction Overview (detail, with pagination) ----

TRANSACTION_OVERVIEW_QUERY = """
SELECT
  "UTR Date" AS "UTR Date",
  "Transaction Date" AS "Transaction Date",
  "Payment Reference Number" AS "Payment Reference Number",
  "Transaction Type" AS "Transaction Type",
  "Payment Gateway" AS "Payment Gateway",
  "Card Type" AS "Card Type",
  "Gross Amount" AS "Gross Amount",
  "Service Tax" AS "Service Tax",
  "Payment Processing Fee" AS "Payment Processing Fee",
  "Net Amount" AS "Net Amount",
  "Payment Type" AS "Payment Type"
FROM (
  SELECT
    *,
    COALESCE("Gross Amount" / NULLIF(SUM("Gross Amount") OVER (PARTITION BY "Card Type"), 0), 0) AS mix
  FROM "PG_final"
) AS virtual_table
"""


@router.get("/pg_charges/widget/transaction-overview")
async def get_pg_widget_transaction_overview(
    card_type: typing.Optional[str] = Query(None),
    payment_gateway: typing.Optional[str] = Query(None),
    transaction_date: typing.Optional[str] = Query(None),
    settlement_month: typing.Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Payment Gateway Transaction Overview (paginated)."""
    filter_where, params = _build_filter_clause_and_params(
        card_type, payment_gateway, transaction_date, settlement_month
    )
    sql = _inject_filter_into_query(TRANSACTION_OVERVIEW_QUERY, filter_where)
    # Add pagination: ORDER BY and LIMIT/OFFSET
    sql = sql.strip()
    if not sql.upper().endswith("LIMIT"):
        sql += " ORDER BY \"Transaction Date\" DESC NULLS LAST, \"Payment Reference Number\" NULLS LAST"
    sql += f" LIMIT {int(page_size)} OFFSET {(int(page) - 1) * int(page_size)}"
    conn = _get_pg_connection()
    if not conn:
        return {"rows": [], "total": 0, "page": page, "page_size": page_size}
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            # Total count (without LIMIT)
            count_sql = "SELECT COUNT(*) FROM (" + _inject_filter_into_query(
                "SELECT * FROM \"PG_final\"", filter_where
            ) + ") AS _cnt"
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]
        return {"rows": rows, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.exception("Error in transaction overview")
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

