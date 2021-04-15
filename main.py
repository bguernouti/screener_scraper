from models.to_sql import ToSQL

comps = [
    "ASIANPAINT",
    "AXISBANK",
    "DMART",
    "ADANIGREEN",
    "ADANIPORTS",
    "ADANIENT",
    "ATGL",
    "ADANITRANS",
    "BHARTIARTL",
    "BAJAJFINSV",
    "BAJAJ-AUTO",
    "BRITANNIA",
    "BPCL",
    "BANDHANBNK"
]

for comp in comps:
    app = ToSQL(comp)
    app.build()
    print(comp, " Done.")
