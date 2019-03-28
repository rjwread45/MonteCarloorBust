'''
Created on Feb 7, 2019

@author: rread
'''
import sqlite3
import time
from idlelib import runscript
import numpy as np
import decimal
import copy
import statistics


class MonteCarloRunSim():
    asset_values_orig = []
    income_before_tax = []
    income_after_tax = []
    income_tax = []
    spending = []
    withdrawals = []
    output = []
    start_assets = []
    roi_list = []
    roi_value_list = []
    inflation_list = []
    end_asset_list = []
    start_asset_list = []
    start_asset_type_list = []
    cashflow = []
    Years = []
    portfolio_value = []
    income_pretax = []
    income_aftertax = []
    investment_return_tax = []
    withdrawals_after_tax = []
    assets_value_end = []
    asset_values = []

    start_year = 0
    start_time = ''
    end_year = 0
    runs = 0
    sd = 0
    roi = 0
    tax_rate = 0
    inv_tax_rate = 0
    inflation_rate = 0
    inflation_SD = 0
    assets_value_init = 0
    asset_types = []
    tax_rates = []
    investment_tax_rates = []
    assetCnt = 0
    dbname = ''

    def __init__(self):
        pass

    def run_simulation(self, dbname_in, currency_symbol):

        print(self.asset_values_orig)
        self.asset_values_orig.append(0)
        self.dbname = dbname_in
        self.start_time = time.time()
        self.get_assumptions()
        self.get_assets()
        self.create_lists()
        self.get_net_cashFlow()

        success = self.simulation_loop()
        self.create_output_lists(self.runs, success, currency_symbol)
        return self.output

    def create_lists(self):

        i = 0
        self.income_before_tax.clear()
        self.income_after_tax.clear()
        self.income_tax.clear()
        self.spending.clear()
        self.withdrawals.clear()
        self.start_asset_list.clear()
        self.start_asset_type_list.clear()
        self.end_asset_list.clear()
        self.roi_list.clear()
        self.roi_value_list.clear()
        self.inflation_list.clear()

        while i <= (self.end_year - self.start_year):

            self.income_before_tax.append(0)
            self.income_after_tax.append(0)
            self.income_tax.append(0)
            self.spending.append(0)
            self.withdrawals.append(0)
            self.start_asset_list.append([])
            self.start_asset_type_list.append([])
            for a in self.asset_types:
                self.start_asset_type_list[i].append([])
                self.new_asset_type_list[i].append([])
            self.end_asset_list.append([])
            self.roi_list.append([])
            self.roi_value_list.append([])
            self.inflation_list.append([])
            i = i + 1
        r = 0
        zero_list = []

        y = 0

    def get_assumptions(self):

        connection = sqlite3.connect(self.dbname)
        cursor = connection.cursor()
        sql = "select * from assumptions"
        cursor.execute(sql)
        rows = cursor.fetchall()
        lastcol = ""
        for row in rows:
            for col in row:

                if lastcol == 'Current Age :':
                    self.start_year = int(col)
                if lastcol == 'Life Expectancy :':
                    self.end_year = int(col)
                if lastcol == '# of Runs :':
                    self.runs = int(col)
                if lastcol == 'ROI SD :':
                    self.sd = float(col)
                if lastcol == 'Rate of Return :':
                    self.roi = float(col)
                if lastcol == 'Tax Rate :':
                    self.tax_rate = float(col)

                if lastcol == 'Investment Tax Rate :':
                    self.inv_tax_rate = float(col)
                if lastcol == 'Inflation Rate :':
                    self.inflation_rate = float(col)
                if lastcol == 'Inflation SD :':
                    self.inflation_SD = float(col)
                    print('ISD=', col)

                lastcol = col

    def get_assets(self):

        connection = sqlite3.connect(self.dbname)
        cursor = connection.cursor()

        print('xxxx', self.inv_tax_rate)
        print('yyyy', self.asset_values_orig)

        sql = "select distinct type,ifnull(sum(amount),0)," + str(
            self.tax_rate) + ",0, 2 as ord from assets  where start_year <= " + str(
            self.start_year) + " and type = 'Tax Deferred'  group by type  union select distinct type,ifnull(sum(amount),0),'0'," + str(
            self.inv_tax_rate) + ",1 from assets  where start_year <= " + str(
            self.start_year) + " and  type = 'Taxable'  group by type   union select distinct type,ifnull(sum(amount),0),'0','0',3 from assets  where start_year <= " + str(
            self.start_year) + " and  type = 'Tax Free'  group by type order by ord"
        print(sql)
        cursor.execute(sql)
        rows = cursor.fetchall()
        self.assets_value_init = 0
        self.asset_values_orig.clear()
        self.asset_types.clear()
        self.tax_rates.clear()
        self.investment_tax_rates.clear()
        for row in rows:
            ix = 0
            for col in row:
                if ix == 0:
                    self.asset_types.append(col)
                    print(col)
                if ix == 1:
                    self.asset_values_orig.append(float(col))
                    self.assets_value_init = float(self.assets_value_init + col)
                    print("assets_value=", col)
                if ix == 2:
                    self.tax_rates.append(float(col))

                    print("tax rate=", col)

                if ix == 3:
                    self.investment_tax_rates.append(float(col))

                    print("inv tax rate=", col)
                ix = ix + 1
        self.new_asset_type_list = []
        i = 0
        while i <= (self.end_year - self.start_year):
            self.new_asset_type_list.append([])
            self.new_asset_type_list[i].append(0)
            self.new_asset_type_list[i].append(0)
            self.new_asset_type_list[i].append(0)
            i = i + 1

        sql = "select type,start_year ,sum(amount) from assets where start_year > " + str(
            self.start_year) + " group by type"
        print(sql)
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            if row[0] == 'Tax Deferred':
                self.new_asset_type_list[int(row[1]) - self.start_year][1] = float(row[2])
            if row[0] == 'Taxable':
                self.new_asset_type_list[int(row[1]) - self.start_year][0] = float(row[2])
            if row[0] == 'Tax Free':
                self.new_asset_type_list[int(row[1]) - self.start_year][2] = float(row[2])

        print("assets_value=", str(self.asset_values_orig))

        print('avi', str(self.assets_value_init) + ',' + str(self.tax_rates) + "," + str(self.investment_tax_rates))

    def get_net_cashFlow(self):

        year = self.start_year

        connection = sqlite3.connect(self.dbname)
        cursor = connection.cursor()
        year = self.start_year
        self.cashflow.clear()
        while (year <= self.end_year):

            sql = "select distinct change,ifnull(sum(amount),0)," + str(self.tax_rate) + " from income " \
                                                                                         "where non_standard_tax_rate = 'False' and fromyear <= " + str(
                year) + " and toyear >= " + str(year) + " group by change"

            sql2 = sql + " union select distinct change,ifnull(sum(amount),0),tax_rate  from income " \
                         "where non_standard_tax_rate = 'True' and fromyear <= " + str(
                year) + " and toyear >= " + str(year) + " group by change"

            sql = "select distinct change,ifnull(sum(amount),0)," + str(self.tax_rate) + " from income " \
                                                                                         "where `non_standard` = 'False' and fromyear <= " + str(
                year) + " and toyear >= " + str(year) + " group by change"

            sql = sql + " union select distinct change,ifnull(sum(amount),0),tax_rate  from income " \
                        "where `non_standard` = 'True' and fromyear <= " + str(
                year) + " and toyear >= " + str(year) + " group by change"

            print(sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            income = 0
            income_before_tax = 0
            income_after_tax = 0
            tax = 0

            for row in rows:
                print('income', row)
                income_in = float(row[1])
                tax_rate_in = float(row[2])

                change = row[0]
                if change != 0:
                    income_in = self.adjust(income_in, change, year)

                tax_row = float(income_in * (tax_rate_in / 100))
                income_after_tax_row = float(income_in - tax_row)
                income_before_tax = float(income_before_tax + income_in)
                income_after_tax = float(income_after_tax + income_after_tax_row)
                tax = float(tax + tax_row)


            sql = "select ifnull(sum(amount),0) from spending where fromyear <= " + str(year) + " and toyear >= " + str(
                year)
            sql = "select distinct change,ifnull(sum(amount),0) from spending where fromyear <= " + str(
                year) + " and toyear >= " + str(year) + " group by change"

            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                Spending_in = row[1]
                change = row[0]
                if change != 0:
                    spending = self.adjust(Spending_in, change, year)
            self.cashflow.append(float(income_after_tax - spending))

            self.spending[year - self.start_year] = float(spending)
            self.income_before_tax[year - self.start_year] = float(income_before_tax)
            self.income_after_tax[year - self.start_year] = float(income_before_tax - tax)
            self.income_tax[year - self.start_year] = float(tax)
            self.withdrawals[year - self.start_year] = float(income_after_tax - spending)

            year = year + 1

    def adjust(self, value_in, change, year_in):
        adjusted = value_in
        year = self.start_year

        while (year < year_in):
            adjusted = adjusted + ((float(change) / 100) * adjusted)

            year = year + 1

        return adjusted

    def simulation_loop(self):

        test_time = 1
        self.last_time = self.start_time
        success = 0
        fail = 0
        year = self.start_year
        run = 0
        self.assets_value_end.clear()
        if test_time == 1:
            current_time = time.time()
            print("Start Loop", current_time - self.start_time, ',', current_time - self.last_time)
            self.last_time = current_time

        while (run < self.runs):
            ROIarray = self.get_ROI_random(self.end_year - self.start_year + 1, self.roi, self.sd)
            Inflationarray = self.get_inflation_random(self.end_year - self.start_year + 1, self.inflation_rate,
                                                       self.inflation_SD)

            assetCnt = 0
            year = 0
            assets_value = self.assets_value_init
            self.asset_values.clear()

            for l in self.asset_values_orig:
                self.asset_values.append(l)

            failedrun = "n"
            assetCnt = 0;
            while (year <= (self.end_year - self.start_year)):
                if failedrun == 'n':
                    """
                    If cashflow is positive just add it to tax-free asset value
                    """



                    self.start_asset_list[year].append(assets_value)

                    ix2 = 0
                    for av in self.asset_values:
                        self.start_asset_type_list[year][ix2].append(self.asset_values[ix2])

                        ix2 = ix2 + 1


                    if self.cashflow[year] >= 0:
                        assets_value = assets_value + self.cashflow[year]
                        assetCnt = 0
                        self.asset_values[assetCnt] = self.asset_values[assetCnt] + self.cashflow[year]


                    else:
                        amount_to_cover = -self.cashflow[year]

                        """
                        Loop thru assets to fund the required cashflow
                        """
                        while amount_to_cover > 0 and failedrun != 'y':
                            amount_to_cover_after_tax = (amount_to_cover / (1 - (self.tax_rates[assetCnt]) / 100))
                            if amount_to_cover_after_tax <= self.asset_values[assetCnt]:
                                self.asset_values[assetCnt] = self.asset_values[assetCnt] - amount_to_cover_after_tax
                                assets_value = assets_value - amount_to_cover_after_tax
                                amount_to_cover = 0
                            else:
                                amountCovered = self.asset_values[assetCnt] * (1 - ((self.tax_rates[assetCnt]) / 100))
                                amount_to_cover = amount_to_cover - amountCovered
                                assets_value = assets_value - self.asset_values[assetCnt]
                                self.asset_values[assetCnt] = 0
                                assetCnt = assetCnt + 1
                                if assetCnt + 1 > len(self.asset_values):
                                    failedrun = 'y'
                                    fail = fail + 1

                    interest_inflation = self.calculcate_interest_and_inflation(assets_value, ROIarray[year],
                                                                                Inflationarray[year], year)

                    assets_value = assets_value + interest_inflation[0]
                    assets_value = assets_value - interest_inflation[1]
                    assets_value = assets_value + interest_inflation[2]

                    self.roi_list[year].append(ROIarray[year])
                    self.roi_value_list[year].append(interest_inflation[0])

                    self.inflation_list[year].append(interest_inflation[1])
                    self.end_asset_list[year].append(assets_value)
                else:
                    self.start_asset_list[year].append(0)
                    self.roi_value_list[year].append(0)
                    self.end_asset_list[year].append(0)
                    self.inflation_list[year].append(0)
                    self.roi_list[year].append(0)
                    for i in range(0, len(self.asset_values)):
                        self.start_asset_type_list[year][i].append(0)

                year = year + 1

            if failedrun == "n":
                self.assets_value_end.append(assets_value)
                success = success + 1
            else:
                self.assets_value_end.append(0)

            run = run + 1
        if test_time == 1:
            current_time = time.time()
            print("End Loop", current_time - self.start_time, ',', current_time - self.last_time)
            self.last_time = current_time

        return success

    def get_ROI_random(self, years, roi, sd):

        return np.random.normal(size=years, loc=roi, scale=sd)

    def get_inflation_random(self, years, inflation, inflation_sd):

        return np.random.normal(size=years, loc=inflation, scale=inflation_sd)

    def calculcate_interest_and_inflation(self, assets_value, roi, inflation_in, year):

        ix = 0
        interest = 0
        inflation = 0
        new_assets = 0
        for l in self.asset_values:
            asset_interest = (l * ((roi) / 100))
            if asset_interest > 0:
                asset_interest = asset_interest - ((asset_interest) * ((self.investment_tax_rates[ix]) / 100))
            else:
                asset_interest = asset_interest - ((asset_interest) * ((self.investment_tax_rates[ix]) / 100))

            interest = interest + asset_interest
            asset_inflation = (self.asset_values[ix] * ((inflation_in) / 100))
            inflation = inflation + asset_inflation
            new_assets = new_assets + self.new_asset_type_list[year][ix]

            self.asset_values[ix] = self.asset_values[ix] + asset_interest
            self.asset_values[ix] = self.asset_values[ix] - asset_inflation + self.new_asset_type_list[year][ix]

            interest_inflation = []
            interest_inflation.clear
            interest_inflation.append(interest)
            interest_inflation.append(inflation)
            interest_inflation.append(new_assets)
            ix = ix + 1
        return interest_inflation

    def create_output_lists(self, runs, success, currency_symbol):

        runData = []
        headers = []
        headers.clear()

        runData.append('Probabiity')

        runData.append(
            str(decimal.Decimal(success * 100 / runs).quantize(decimal.Decimal('.01'))).replace('.00', '') + "%")
        runData.append('Initial Assets:')
        runData.append(str(format(int(sum(self.asset_values_orig)), ",d")))

        runData.append('Average Spending:')

        runData.append(str(format(int(sum(self.spending) / float(len(self.spending))), ",d")))

        runData.append('Average After-Tax Income:')
        runData.append(str(format(int(statistics.mean((self.income_after_tax))), ",d")))

        runData.append('Average Tax:')
        runData.append(str(format(int(statistics.mean(self.income_tax)), ",d")))

        runData.append('Average Withdrawals:')
        runData.append(str(format(int(statistics.mean(self.withdrawals)), ",d")))

        runData.append('Median End Value:')

        print ('EV',self.assets_value_end)

        runData.append(str(format(int(statistics.mean(self.assets_value_end)), ",d")))

        detailedRunData = []
        detailedRunData.clear()
        chart_years = []
        chart_years.clear()
        chart_assets = []
        chart_assets.clear()
        chart_asset_names = []
        chart_asset_names.clear()

        for a in self.start_asset_type_list[0]:
            chart_assets.append([])

        i = 0
        while i <= (self.end_year - self.start_year):


            chart_years.append(str(i + self.start_year))

            detailedRunData.append(i + self.start_year)

            if i == 0:
                headers.append('Year')

            detailedRunData.append(currency_symbol + format(int(self.income_before_tax[i]), ",d"))

            if i == 0:
                headers.append('Income')

            detailedRunData.append(currency_symbol + format(int(self.income_tax[i]), ",d"))

            if i == 0:
                headers.append('Income Tax')

            detailedRunData.append(currency_symbol + format(int(self.income_after_tax[i]), ",d"))

            if i == 0:
                headers.append('Income \nAfter Tax')

            detailedRunData.append(currency_symbol + format(int(self.spending[i]), ",d"))

            if i == 0:
                headers.append('Spending')

            detailedRunData.append(currency_symbol + format(int(-1 * self.withdrawals[i]), ",d"))

            if i == 0:
                headers.append('Withdrawals')


            detailedRunData.append(
                currency_symbol + str(format(int(statistics.median(self.start_asset_list[i])), ",d")))

            if i == 0:
                headers.append('Start Assets')

            at = 0
            for a in self.start_asset_type_list[i]:
                detailedRunData.append(
                    currency_symbol + str(format(int(statistics.median(self.start_asset_type_list[i][at])), ",d")))
                chart_assets[at].append(statistics.median(self.start_asset_type_list[i][at]))

                if i == 0:
                    headers.append(self.asset_types[at])
                    chart_asset_names.append(self.asset_types[at])

                at = at + 1

            detailedRunData.append(
            str(decimal.Decimal(statistics.median(self.roi_list[i])).quantize(decimal.Decimal('.01'))) + "%")

            if i == 0:
                headers.append('ROI')

            detailedRunData.append(currency_symbol + str(format(int(statistics.median(self.roi_value_list[i])), ",d")))

            if i == 0:
                headers.append('Roi Value')

            detailedRunData.append(currency_symbol + str(format(int(statistics.median(self.inflation_list[i])), ",d")))

            if i == 0:
                headers.append('Inflation')

            detailedRunData.append(currency_symbol + str(format(int(statistics.median(self.end_asset_list[i])), ",d")))

            if i == 0:
                headers.append('End Value')

            i = i + 1


        self.output.clear()
        self.output.append(headers)
        self.output.append(runData)
        self.output.append(detailedRunData)
        self.output.append(chart_years)
        self.output.append(chart_assets)
        self.output.append(chart_asset_names)


        current_time = time.time()
        print("End Run", current_time - self.start_time, ',', current_time - self.last_time)


