from models.to_sql import ToSQL
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("company_name", help="The name of the company (nse) or (bse)")

args = parser.parse_args()
name = args.company_name
app = ToSQL(name)
app.build()

