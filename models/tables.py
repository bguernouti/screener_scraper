from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:admin@localhost:5432/screener_in')
Base = declarative_base()
session = sessionmaker(bind=engine)


class CompanyInfo(Base):
    __tablename__ = "company_info"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    website = Column(String)
    bse = Column(Integer)
    nse = Column(String)
    about = Column(Text)
    market_cap = Column(String)
    current_price = Column(String)
    high_low = Column(String)
    stock_p_e = Column(String)
    book_value = Column(String)
    dividend_yield = Column(String)
    roce = Column(String)
    roe = Column(String)
    face_value = Column(String)
    peer = relationship("PeerComparison", cascade="all, delete")
    quarterly_results = relationship("QuarterlyResults", cascade="all, delete")
    profit_loss = relationship("ProfitLoss", cascade="all, delete")
    balance_sheet = relationship("BalanceSheet", cascade="all, delete")
    cash_flow = relationship("CashFlow", cascade="all, delete")
    ratios = relationship("Ratios", cascade="all, delete")
    shareholding = relationship("Shareholding", cascade="all, delete")

    compounded_sales_growth = relationship(
        "CompoundedSalesGrowth",
        primaryjoin="and_(CompanyInfo.id == CompoundedSalesGrowth.company, CompoundedSalesGrowth.consolidated == False)",
        cascade="all, delete",
        backref="company_info",
        overlaps="compounded_sales_growth_c, company_info"
    )

    compounded_sales_growth_c = relationship(
        "CompoundedSalesGrowth",
        primaryjoin="and_(CompanyInfo.id == CompoundedSalesGrowth.company, CompoundedSalesGrowth.consolidated == True)",
        cascade="all, delete",
        overlaps="compounded_sales_growth, company_info"
    )

    compounded_profit_growth = relationship(
        "CompoundedProfitGrowth",
        primaryjoin="and_(CompanyInfo.id == CompoundedProfitGrowth.company,CompoundedProfitGrowth.consolidated == False)",
        cascade="all, delete",
        backref="company_info",
        overlaps="compounded_profit_growth_c, company_info"
    )

    compounded_profit_growth_c = relationship(
        "CompoundedProfitGrowth",
        primaryjoin="and_(CompanyInfo.id == CompoundedProfitGrowth.company,CompoundedProfitGrowth.consolidated == True)",
        cascade="all, delete",
        overlaps="compounded_profit_growth, company_info"
    )

    stock_price_cgar = relationship(
        "StockPriceCAGR",
        primaryjoin="and_(CompanyInfo.id == StockPriceCAGR.company, StockPriceCAGR.consolidated == False)",
        cascade="all, delete",
        backref="company_info",
        overlaps="stock_price_cgar_c, company_info"
    )

    stock_price_cgar_c = relationship(
        "StockPriceCAGR",
        primaryjoin="and_(CompanyInfo.id == StockPriceCAGR.company, StockPriceCAGR.consolidated == True)",
        cascade="all, delete",
        overlaps="stock_price_cgar, company_info"
    )

    return_on_quality = relationship(
        "ReturnOnQuality",
        primaryjoin="and_(CompanyInfo.id == ReturnOnQuality.company, ReturnOnQuality.consolidated == False)",
        cascade="all, delete",
        backref="company_info",
        overlaps="return_on_quality_c, company_info"
    )
    return_on_quality_c = relationship(
        "ReturnOnQuality",
        primaryjoin="and_(CompanyInfo.id == ReturnOnQuality.company, ReturnOnQuality.consolidated == True)",
        cascade="all, delete",
        overlaps="return_on_quality, company_info"
    )


class PeerComparison(Base):
    __tablename__ = "peer_comparison"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    s_no = Column(Integer)
    name = Column(String)
    current_price = Column(Float)
    price_to_earning = Column(Float)
    market_cap = Column(Float)
    dividend_yield = Column(Float)
    net_profit = Column(Float)
    yoy_profit_growth = Column(Float)
    sales = Column(Float)
    yoy_sales_growth = Column(Float)
    roce = Column(Float)


# Quarterly result
class QuarterlyCell(Base):
    __tablename__ = "quarterly_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("quarterly_indexes.id"))
    month_id = Column(Integer, ForeignKey("quarterly_months.id"))
    table_id = Column(Integer, ForeignKey("quarterly_results.id"))
    value = Column(String)
    idx = relationship("QuarterlyIndexes")
    month = relationship("QuarterlyMonths")


class QuarterlyIndexes(Base):
    __tablename__ = "quarterly_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class QuarterlyMonths(Base):
    __tablename__ = "quarterly_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class QuarterlyResults(Base):
    __tablename__ = "quarterly_results"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("QuarterlyCell", cascade="all, delete")


# Profit & Loss
class ProfitLossCell(Base):
    __tablename__ = "profit_loss_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("profit_loss_indexes.id"))
    month_id = Column(Integer, ForeignKey("profit_loss_months.id"))
    table_id = Column(Integer, ForeignKey("profit_loss.id"))
    value = Column(String)
    idx = relationship("ProfitLossIndexes")
    month = relationship("ProfitLossMonths")


class ProfitLossIndexes(Base):
    __tablename__ = "profit_loss_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class ProfitLossMonths(Base):
    __tablename__ = "profit_loss_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class ProfitLoss(Base):
    __tablename__ = "profit_loss"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("ProfitLossCell", cascade="all, delete")


# Balance Sheet
class BalanceSheetCell(Base):
    __tablename__ = "balance_sheet_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("balance_sheet_indexes.id"))
    month_id = Column(Integer, ForeignKey("balance_sheet_months.id"))
    table_id = Column(Integer, ForeignKey("balance_sheet.id"))
    value = Column(String)
    idx = relationship("BalanceSheetIndexes")
    month = relationship("BalanceSheetMonths")


class BalanceSheetIndexes(Base):
    __tablename__ = "balance_sheet_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class BalanceSheetMonths(Base):
    __tablename__ = "balance_sheet_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class BalanceSheet(Base):
    __tablename__ = "balance_sheet"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("BalanceSheetCell", cascade="all, delete")


# Cash Flow
class CashFlowCell(Base):
    __tablename__ = "cash_flow_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("cash_flow_indexes.id"))
    month_id = Column(Integer, ForeignKey("cash_flow_months.id"))
    table_id = Column(Integer, ForeignKey("cash_flow.id"))
    value = Column(String)
    idx = relationship("CashFlowIndexes")
    month = relationship("CashFlowMonths")


class CashFlowIndexes(Base):
    __tablename__ = "cash_flow_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class CashFlowMonths(Base):
    __tablename__ = "cash_flow_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class CashFlow(Base):
    __tablename__ = "cash_flow"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("CashFlowCell", cascade="all, delete")


# Ratios
class RatiosCell(Base):
    __tablename__ = "ratios_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("ratios_indexes.id"))
    month_id = Column(Integer, ForeignKey("ratios_months.id"))
    table_id = Column(Integer, ForeignKey("ratios.id"))
    value = Column(String)
    idx = relationship("RatiosIndexes")
    month = relationship("RatiosMonths")


class RatiosIndexes(Base):
    __tablename__ = "ratios_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class RatiosMonths(Base):
    __tablename__ = "ratios_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class Ratios(Base):
    __tablename__ = "ratios"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("RatiosCell", cascade="all, delete")


# Shareholding
class ShareholdingCell(Base):
    __tablename__ = "shareholding_cell"
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("shareholding_indexes.id"))
    month_id = Column(Integer, ForeignKey("shareholding_months.id"))
    table_id = Column(Integer, ForeignKey("shareholding.id"))
    value = Column(String)
    idx = relationship("ShareholdingIndexes")
    month = relationship("ShareholdingMonths")


class ShareholdingIndexes(Base):
    __tablename__ = "shareholding_indexes"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class ShareholdingMonths(Base):
    __tablename__ = "shareholding_months"
    id = Column(Integer, primary_key=True)
    month = Column(String)


class Shareholding(Base):
    __tablename__ = "shareholding"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    consolidated = Column(Boolean)
    cells = relationship("ShareholdingCell", cascade="all, delete")


class CompoundedSalesGrowth(Base):
    __tablename__ = "compounded_sales_growth"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    ten_years = Column(String)
    five_years = Column(String)
    three_years = Column(String)
    TTM = Column(String)
    consolidated = Column(Boolean)


class CompoundedProfitGrowth(Base):
    __tablename__ = "compounded_profit_growth"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    ten_years = Column(String)
    five_years = Column(String)
    three_years = Column(String)
    TTM = Column(String)
    consolidated = Column(Boolean)


class StockPriceCAGR(Base):
    __tablename__ = "stock_price_cagr"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    ten_years = Column(String)
    five_years = Column(String)
    three_years = Column(String)
    one_year = Column(String)
    consolidated = Column(Boolean)


class ReturnOnQuality(Base):
    __tablename__ = "return_on_quality"
    id = Column(Integer, primary_key=True)
    company = Column(Integer, ForeignKey("company_info.id"))
    ten_years = Column(String)
    five_years = Column(String)
    three_years = Column(String)
    last_year = Column(String)
    consolidated = Column(Boolean)
