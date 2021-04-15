from typing import Dict, Any, List, Tuple

import requests
import pandas as pd
from lxml import html, etree as ET
from models.tables import *


class ToSQL(object):
    HEADERS: Dict = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}

    URLS: Dict = {
        "main": "https://www.screener.in/company/{}/",
        "search_company": "https://www.screener.in/api/company/search/?q={}",
        "schedules": "https://www.screener.in/api/company/{}/schedules/?parent={}&section={}",
        "shareholders": "https://www.screener.in/api/{}/investors/{}/",
        "peers": "https://www.screener.in/api/company/{}/peers/"
    }

    def __init__(self, comp_name: str) -> None:
        self.comp_name = comp_name
        self.details: Dict = self.__get_comp_details(self.comp_name)[0]
        self.db_session: Any = session()
        self.exist: Any = self.db_session.query(CompanyInfo).filter(CompanyInfo.nse == self.comp_name).one_or_none()

        if self.exist:
            self.db_session.delete(self.exist)
            self.db_session.commit()

        self.company_table: Any = CompanyInfo()

    def build(self):
        page = self.__get_content()

        # Steps
        self.__build_links(page)
        self.__build_company_info(page)
        self.__build_peers(page)
        self.__build_quarters(page)
        self.__build_profit(page)
        self.__build_balance(page)
        self.__build_cash_flows(page)
        self.__build_ratios(page)
        self.__build_shareholding(page)
        self.__build_compounded_sales_growth(page)
        self.__build_compounded_profit_growth(page)
        self.__build_stock_price_cgar(page)
        self.__build_return_on_quality(page)

        if page.xpath("//a[contains(@href,'consolidated')]"):
            consolidated_page = self.__get_content(consolidated=True)
            self.__build_quarters(consolidated_page, consolidated=True)
            self.__build_profit(consolidated_page, consolidated=True)
            self.__build_balance(consolidated_page, consolidated=True)
            self.__build_cash_flows(consolidated_page, consolidated=True)
            self.__build_ratios(consolidated_page, consolidated=True)
            self.__build_compounded_sales_growth(consolidated_page, consolidated=True)
            self.__build_compounded_profit_growth(consolidated_page, consolidated=True)
            self.__build_stock_price_cgar(consolidated_page, consolidated=True)
            self.__build_return_on_quality(consolidated_page, consolidated=True)

        self.db_session.add(self.company_table)
        self.db_session.commit()

    def __get_comp_details(self, name: str) -> Dict:
        url: str = self.URLS["search_company"].format(name)
        r: Any = requests.get(url, headers=self.HEADERS)
        return r.json()

    def __get_content(self, consolidated: bool = False) -> Any:
        if not consolidated:
            url: str = self.URLS["main"].format(self.comp_name)
        else:
            url: str = self.URLS["main"].format(self.comp_name) + "/consolidated/"

        r: Any = requests.get(url, headers=self.HEADERS)
        parsed: Any = html.fromstring(r.content)
        return parsed

    # Operations
    def __build_links(self, page: Any):
        xp: str = "//div[@id='top']"
        el: Any = page.xpath(xp)[0]
        title_xp: str = "div/h1"
        title: str = el.xpath(title_xp)[0].text_content()
        links_xp: str = "div[2]/a/span"
        links: List = []
        for span in el.xpath(links_xp):
            links.append(span.text.replace(" ", "").replace("\n", ""))

        try:
            self.company_table.website = links[0]
        except:
            self.company_table.website = None

        try:
            self.company_table.bse = links[1].split(":")[1]
        except:
            self.company_table.bse = None

        try:
            self.company_table.nse = links[2].split(":")[1]
        except:
            self.company_table.nse = None

        self.company_table.name = title

        return

    def __build_company_info(self, page: Any):
        ratios_xp: str = "//ul[@id='top-ratios']"
        ul: Any = page.xpath(ratios_xp)[0]
        values: List[str] = []

        for el in ul.xpath("./li/span[@class='nowrap value']"):
            string: str = el.text_content().replace("\n", "")
            value: str = self.__string_fix(string)
            values.append(value)

        self.company_table.market_cap = values[0]
        self.company_table.current_price = values[1]
        self.company_table.high_low = values[2]
        self.company_table.stock_p_e = values[3]
        self.company_table.book_value = values[4]
        self.company_table.dividend_yield = values[5]
        self.company_table.roce = values[6]
        self.company_table.roe = values[7]
        self.company_table.face_value = values[8]

        return

    def __build_peers_info(self, page: Any):
        xp: str = "//section[@id='peers']"
        el: Any = page.xpath(xp)[0]
        title_xp: str = "//section[@id='peers']//h2"
        title: str = el.xpath(title_xp)[0].text
        title = title + "\n"
        p: Any = el.xpath(".//p")[0]
        trick: List[str] = p.text_content().replace(" ", "").replace("\n", "").split("Industry")
        trick[1]: str = "Industry" + trick[1]
        trick: List[str] = [el.replace(":", ": ") for el in trick]
        peers_head_df: Any = pd.DataFrame(trick)
        return peers_head_df

    def __build_peers(self, page: Any):
        warehouse_id = page.xpath("//div[@id='company-info']")[0].attrib.get("data-warehouse-id")
        self.details["warehouse-id"] = warehouse_id

        peers_url = self.URLS["peers"].format(warehouse_id)
        peers_res = requests.get(peers_url, headers=self.HEADERS)
        parsed = html.fromstring(peers_res.content)
        table = parsed.xpath(".//table")[0]
        peers_df = pd.DataFrame(pd.read_html(html.tostring(table, pretty_print=True))[0])
        peers_df.fillna(0, inplace=True)
        peers_df["S.No."] = peers_df["S.No."].astype(int)

        for value in peers_df.values:
            peer_record = PeerComparison(
                s_no=value[0],
                name=value[1],
                current_price=value[2],
                price_to_earning=value[3],
                market_cap=value[4],
                dividend_yield=value[5],
                net_profit=value[6],
                yoy_profit_growth=value[7],
                sales=value[8],
                yoy_sales_growth=value[9],
                roce=value[10],
            )
            self.company_table.peer.append(peer_record)
        return

    def __build_quarters(self, page: Any, consolidated: bool = False):
        quarters_table: Any = page.xpath("//section[@id='quarters']//table")[0]
        buttons: Any = quarters_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section, consolidated=consolidated)
        tbody: Any = quarters_table.xpath(".//tbody")[0]
        last_tr: Any = tbody.xpath("./tr[last()]")[0]
        tbody.remove(last_tr)
        pd_html: Any = pd.read_html(html.tostring(quarters_table, pretty_print=True))[0]
        quarters_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        quarters_df.index = quarters_df.index.str.replace("+", "")

        self.__insert_months(quarters_df.columns, QuarterlyMonths)
        self.__insert_indexes(quarters_df.index, QuarterlyIndexes)

        quarterly_table = self.__insert_cell(quarters_df, QuarterlyMonths, QuarterlyIndexes, QuarterlyCell,
                                             QuarterlyResults, consolidated=consolidated)

        self.company_table.quarterly_results.append(quarterly_table)
        return quarters_df

    def __build_profit(self, page: Any, consolidated: bool = False):
        profit_table: Any = page.xpath("//section[@id='profit-loss']/div[@data-result-table]/table")[0]
        buttons: Any = profit_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section, consolidated=consolidated)

        pd_html: Any = pd.read_html(html.tostring(profit_table))[0]
        profit_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        profit_df.fillna(0, inplace=True)
        profit_df.index = profit_df.index.str.replace("+", "")

        self.__insert_months(profit_df.columns, ProfitLossMonths)
        self.__insert_indexes(profit_df.index, ProfitLossIndexes)

        profit_table = self.__insert_cell(profit_df, ProfitLossMonths, ProfitLossIndexes, ProfitLossCell,
                                          ProfitLoss, consolidated=consolidated)

        self.company_table.profit_loss.append(profit_table)
        return profit_table

    def __build_compounded_sales_growth(self, page: Any, consolidated=False):
        table_range_1: Any = page.xpath("//table[@class='ranges-table']")[0]
        table_range_1_df = pd.read_html(html.tostring(table_range_1))[0]

        ten_years = table_range_1_df[table_range_1_df.columns[1]][0]
        five_years = table_range_1_df[table_range_1_df.columns[1]][1]
        three_years = table_range_1_df[table_range_1_df.columns[1]][2]
        ttm = table_range_1_df[table_range_1_df.columns[1]][3]

        table = CompoundedSalesGrowth(
            ten_years=ten_years,
            five_years=five_years,
            three_years=three_years,
            TTM=ttm,
            consolidated=consolidated
        )

        if consolidated:
            self.company_table.compounded_sales_growth_c.append(table)
        else:
            self.company_table.compounded_sales_growth.append(table)

        return

    def __build_compounded_profit_growth(self, page: Any, consolidated=False):
        table_range_2: Any = page.xpath("//table[@class='ranges-table']")[1]
        table_range_2_df = pd.read_html(html.tostring(table_range_2))[0]

        ten_years = table_range_2_df[table_range_2_df.columns[1]][0]
        five_years = table_range_2_df[table_range_2_df.columns[1]][1]
        three_years = table_range_2_df[table_range_2_df.columns[1]][2]
        ttm = table_range_2_df[table_range_2_df.columns[1]][3]

        table = CompoundedProfitGrowth(
            ten_years=ten_years,
            five_years=five_years,
            three_years=three_years,
            TTM=ttm,
            consolidated=consolidated
        )

        if consolidated:
            self.company_table.compounded_profit_growth_c.append(table)
        else:
            self.company_table.compounded_profit_growth.append(table)

        return

    def __build_stock_price_cgar(self, page: Any, consolidated=False):
        table_range_3: Any = page.xpath("//table[@class='ranges-table']")[2]
        table_range_3_df = pd.read_html(html.tostring(table_range_3))[0]

        ten_years = table_range_3_df[table_range_3_df.columns[1]][0]
        five_years = table_range_3_df[table_range_3_df.columns[1]][1]
        three_years = table_range_3_df[table_range_3_df.columns[1]][2]
        one_year = table_range_3_df[table_range_3_df.columns[1]][3]

        table = StockPriceCAGR(
            ten_years=ten_years,
            five_years=five_years,
            three_years=three_years,
            one_year=one_year,
            consolidated=consolidated
        )

        if consolidated:
            self.company_table.stock_price_cgar_c.append(table)
        else:
            self.company_table.stock_price_cgar.append(table)

        return

    def __build_return_on_quality(self, page: Any, consolidated=False):
        table_range_4: Any = page.xpath("//table[@class='ranges-table']")[3]
        table_range_4_df = pd.read_html(html.tostring(table_range_4))[0]

        ten_years = table_range_4_df[table_range_4_df.columns[1]][0]
        five_years = table_range_4_df[table_range_4_df.columns[1]][1]
        three_years = table_range_4_df[table_range_4_df.columns[1]][2]
        last_year = table_range_4_df[table_range_4_df.columns[1]][3]

        table = ReturnOnQuality(
            ten_years=ten_years,
            five_years=five_years,
            three_years=three_years,
            last_year=last_year,
            consolidated=consolidated
        )

        if consolidated:
            self.company_table.return_on_quality_c.append(table)
        else:
            self.company_table.return_on_quality.append(table)

        return

    def __build_balance(self, page: Any, consolidated: bool = False):
        balance_table: Any = page.xpath("//section[@id='balance-sheet']//table")[0]
        buttons: Any = balance_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section, consolidated=consolidated)

        pd_html: Any = pd.read_html(html.tostring(balance_table))[0]
        balance_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        balance_df.fillna(0, inplace=True)
        balance_df.index = balance_df.index.str.replace("+", "")

        self.__insert_months(balance_df.columns, BalanceSheetMonths)
        self.__insert_indexes(balance_df.index, BalanceSheetIndexes)

        balance_table = self.__insert_cell(balance_df, BalanceSheetMonths, BalanceSheetIndexes, BalanceSheetCell,
                                           BalanceSheet, consolidated=consolidated)

        self.company_table.balance_sheet.append(balance_table)
        return balance_table

    def __build_cash_flows(self, page: Any, consolidated: bool = False):
        cash_flows_table: Any = page.xpath("//section[@id='cash-flow']//table")[0]
        buttons: Any = cash_flows_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section, consolidated=consolidated)

        pd_html: Any = pd.read_html(html.tostring(cash_flows_table))[0]
        cash_flows_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        cash_flows_df.fillna(0, inplace=True)
        cash_flows_df.index = cash_flows_df.index.str.replace("+", "")

        self.__insert_months(cash_flows_df.columns, CashFlowMonths)
        self.__insert_indexes(cash_flows_df.index, CashFlowIndexes)

        cash_flow_table = self.__insert_cell(cash_flows_df, CashFlowMonths, CashFlowIndexes, CashFlowCell,
                                             CashFlow, consolidated=consolidated)

        self.company_table.cash_flow.append(cash_flow_table)
        return cash_flow_table

    def __build_ratios(self, page: Any, consolidated: bool = False):
        ratios_table: Any = page.xpath("//section[@id='ratios']//table")[0]
        buttons: Any = ratios_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section, consolidated=consolidated)

        pd_html: Any = pd.read_html(html.tostring(ratios_table))[0]
        ratios_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        ratios_df.fillna(0, inplace=True)
        ratios_df.index = ratios_df.index.str.replace("+", "")

        self.__insert_months(ratios_df.columns, RatiosMonths)
        self.__insert_indexes(ratios_df.index, RatiosIndexes)

        ratios_table = self.__insert_cell(ratios_df, RatiosMonths, RatiosIndexes, RatiosCell,
                                          Ratios, consolidated=consolidated)

        self.company_table.ratios.append(ratios_table)
        return ratios_table

    def __build_shareholding(self, page: Any):

        if not page.xpath("//section[@id='shareholding']//table"):
            return
        else:
            shareholding_table: Any = page.xpath("//section[@id='shareholding']//table")[0]

        buttons: Any = shareholding_table.xpath(".//button[@onclick]")
        for button in buttons:
            tr: Any = button.getparent().getparent()
            parent, section = self.__parse_button(button)
            self.__alter_table(tr, parent, section)

        pd_html: Any = pd.read_html(html.tostring(shareholding_table))[0]
        shareholding_df: Any = pd_html.set_index("Unnamed: 0", drop=True)
        shareholding_df.fillna(0, inplace=True)
        shareholding_df.index = shareholding_df.index.str.replace("+", "")

        self.__insert_months(shareholding_df.columns, ShareholdingMonths)
        self.__insert_indexes(shareholding_df.index, ShareholdingIndexes)

        shareholding_table = self.__insert_cell(shareholding_df, ShareholdingMonths, ShareholdingIndexes,
                                                ShareholdingCell,
                                                Shareholding)

        self.company_table.shareholding.append(shareholding_table)
        return shareholding_table

    def __alter_table(self, tr: Any, parent: str, section: str, consolidated: bool = False) -> Any:
        rows: Any = self.__get_new_rows(parent, section, consolidated)
        trs: List[Any] = []
        tr_th = tr.getparent().getparent().getchildren()[0].getchildren()[0].getchildren()
        heads = [tr_th[idx].text for idx in range(0, len(tr_th))]
        heads.pop(0)
        temp_data = {h: 0 for h in heads}

        for row, items in rows.items():
            if "setAttributes" in items.keys():
                items.__delitem__("setAttributes")
            new_tr: Any = ET.XML("<tr></tr>")
            tds: List[Any] = []
            # new_td: Any = ET.XML("<td>{}</td>".format(row))
            new_td: Any = html.fromstring("<td>{}</td>".format(row))
            tds.append(new_td)

            for item_k, item_v in items.items():
                if item_k in temp_data.keys():
                    temp_data[item_k] = item_v

            for k, v in temp_data.items():
                # new_td: Any = ET.XML("<td>{}</td>".format(v))
                new_td: Any = html.fromstring("<td>{}</td>".format(v))
                tds.append(new_td)

            new_tr.extend(tds)
            trs.append(new_tr)
        tr.extend(trs)
        return

    def __get_new_rows(self, parent, section, consolidated: bool = False):

        if not section:  # Shareholder
            url: str = self.URLS["shareholders"].format(self.details["id"], parent)
        else:
            url: str = self.URLS["schedules"].format(self.details["id"], parent, section)

        if consolidated:
            url += "&consolidated="

        res: Any = requests.get(url, headers=self.HEADERS)
        return res.json()

    @staticmethod
    def __string_fix(string: str) -> str:
        old = string[0]
        res_str = old
        for idx in range(1, len(string)):
            new_str = string[idx]
            if not new_str == old == " ":
                res_str += new_str

            old = new_str

        if res_str.startswith(" "):
            res_str: str = res_str[1:]
        if res_str.endswith(" "):
            res_str: str = res_str[:-1]

        return res_str

    @staticmethod
    def __parse_button(button: Any) -> Tuple:
        arr: List[str] = button.attrib.get("onclick").split("(")[1].split(")")[0].replace(", this", "").replace("'",
                                                                                                                "").replace(
            ", ", ",").split(",")
        if len(arr) == 1:
            t = (arr[0], "")
        else:
            t = tuple(arr)
        return t

    def __insert_months(self, columns, table):
        for col in columns:
            if not self.db_session.query(table).filter(table.month == col).one_or_none():
                new_month = table(month=col)
                self.db_session.add(new_month)
                self.db_session.commit()

    def __insert_indexes(self, index, table):
        for idx in index:
            if not self.db_session.query(table).filter(table.name == idx).one_or_none():
                new_index = table(name=idx)
                self.db_session.add(new_index)
                self.db_session.commit()

    def __insert_cell(self, df, months_table, index_table, cell_table, data_table, consolidated=False):

        data_table_obj = data_table(consolidated=consolidated)

        for month, col in df.items():
            month_obj = self.db_session.query(months_table).filter(months_table.month == month).one()
            for idx, value in col.items():
                index_obj = self.db_session.query(index_table).filter(
                    index_table.name == idx).one()

                cell = cell_table(idx=index_obj, month=month_obj, value=value)

                data_table_obj.cells.append(cell)

        return data_table_obj
