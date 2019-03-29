import numpy as np

import sqlite3

import MonteCarloRun
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.config import Config
from kivy.graphics import Mesh, InstructionGroup, Color
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.filechooser import FileChooserListView

from kivy.utils import get_color_from_hex, get_hex_from_color

from kivy.core.window import Window

from kivy.uix.scrollview import ScrollView

from kivy.lang import Builder
from tkinter.constants import LEFT
from kivy.uix.filechooser import FileChooser

from kivy.uix.floatlayout import FloatLayout
import os

Builder.load_string("""
<MyScreenManager>:
    MainRoot:
        id: MainRoot
    AssumptionsRoot:
        id: Assumptions

<AssumptionsRoot>:
    name: '_assumptionsroot_'

<MainRoot>:
    name: '_mainroot_'


<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserListView:
            id: filechooser

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: root.cancel()

            Button:
                text: "Load Plan"
                on_release: root.load_db(filechooser.path, filechooser.selection)
<SaveDialog>:
    text_input: text_input
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserListView:
            id: filechooser
            on_selection: text_input.text = self.selection and self.selection[0] or ''

        TextInput:
            id: text_input
            size_hint_y: None
            height: 30
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: root.cancel()

            Button:
                text: "Create Plan"
                on_release: root.save_db(filechooser.path, text_input.text)

""")

listrow = []
asr = ''
advroot = ''


class Assumptions():
    start_year = 0
    end_year = 0
    runs = 0
    sd = 0
    roi = 0
    tax_rate = 0
    inv_tax_rate = 0
    inflation_rate = 0
    inflation_SD = 0


class Advanced():
    asset_color = ''
    income_color = ''
    spending_color = ''
    run_summary_color = ''
    run_detail_color = ''
    run_detail_header_color = ''
    currency_symbol = ''
    color_chosen = ''
    more_details = False


class SQLstuff():

    def insert_income(self, table, name_in, value_in, fromyear, toyear, change, non_standard_tax, tax_rate):

        value_in = value_in.strip(" ")
        fromyear = fromyear.strip(" ")
        toyear = toyear.strip(" ")
        value_in = value_in.replace(Advanced.currency_symbol, '')
        value_in = value_in.replace(',', '')

        connection = sqlite3.connect(Advanced.dbname)

        sql = "begin transaction"
        cursor = connection.cursor()
        cursor.execute(sql)

        sql = "insert into " + table + " values ('" + name_in + "'," + value_in + ",'" + fromyear + "','" + toyear + "','" + change.replace(
            '%', '') + "','" + str(non_standard_tax) + "','" + tax_rate + "')"
        print(sql)

        try:
            cursor.execute(sql)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            content = GridLayout(rows=2)
            popup = Popup(content=content, size_hint=(None, None), title='Error', size=(400, 400))
            b1 = Button(text='Close')
            content.add_widget(Label(text='Update Failed - Potential Duplicate Data'))
            content.add_widget(b1)
            b1.bind(on_press=popup.dismiss)
            popup.open()
            print('errror')

        sql = "commit"

        cursor.execute(sql)

    def insert_asset(self, table, name_in, value_in, type, fromyear, toyear):

        value_in = value_in.strip(" ")
        fromyear = fromyear.strip(" ")
        toyear = toyear.strip(" ")
        value_in = value_in.replace(Advanced.currency_symbol, '')
        value_in = value_in.replace(',', '')

        connection = sqlite3.connect(Advanced.dbname)

        sql = "begin transaction"
        cursor = connection.cursor()
        cursor.execute(sql)

        sql = "insert into " + table + " values ('" + name_in + "'," + value_in + ",'" + type + "','" + fromyear + "','" + toyear + "')"
        print('insert sql=', sql)

        try:
            cursor.execute(sql)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            content = GridLayout(rows=2)
            popup = Popup(content=content, size_hint=(None, None), title='Error', size=(400, 400))
            b1 = Button(text='Close')
            b1.bind(on_press=popup.dismiss)
            content.add_widget(Label(text='Update Failed - Probably Duplicate Name'))
            content.add_widget(b1)
            popup.open()

            print('Insert Error')

        print('done')

        sql = "commit"

        cursor.execute(sql)

    def insert_row(self, table, name_in, value_in, fromyear, toyear, change):

        ##print ('name',name_in,'val',value_in)
        if table != 'advanced':
            value_in = value_in.replace(Advanced.currency_symbol, '')
            value_in = value_in.replace(',', '')
        name_in = name_in.strip()
        if table == 'assumptions':
            value_in = value_in.strip("%")
        value_in = value_in.strip(" ")
        fromyear = fromyear.strip(" ")
        toyear = toyear.strip(" ")

        connection = sqlite3.connect(Advanced.dbname)

        sql = "begin transaction"
        cursor = connection.cursor()
        cursor.execute(sql)

        sql = ''
        if table == 'assets':
            sql = "insert into " + table + " values ('" + name_in + "'," + value_in + ",'" + str(
                fromyear) + "','" + "','" + "')"
        else:
            if table == 'spending':
                sql = "insert into " + table + " values ('" + name_in + "'," + value_in + ",'" + fromyear + "','" + toyear + "','" + change.replace(
                    '%', '') + "')"
            else:
                if table == 'income':
                    sql = "insert into " + table + " values ('" + name_in + "'," + value_in + ",'" + fromyear + "','" + toyear + "','" + change.replace(
                        '%', '') + "')"
                else:
                    if table == 'assumptions' or table == 'advanced':
                        sql = "insert into " + table + " values ('" + name_in.strip() + "','" + value_in + "')"
                    else:
                        if table == 'run':
                            sql = "insert into " + table + " values ('" + name_in + "','" + value_in + "')"
                        else:
                            if table == 'dblocation':
                                sql = "insert into " + table + " values ('" + name_in + "')"

        print(sql)

        try:
            cursor.execute(sql)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            content = GridLayout(rows=2)
            popup = Popup(content=content, size_hint=(None, None), title='Error', size=(400, 400))
            b1 = Button(text='Close')
            content.add_widget(Label(text='Update Failed - Potential Duplicate Data'))
            content.add_widget(b1)
            b1.bind(on_press=popup.dismiss)
            popup.open()

            print('errror')

        sql = "commit"

        cursor.execute(sql)

    def load_advanced(self):

        advanced = Advanced()

        dbfile = 'montecarloapp.db'

        connection = sqlite3.connect(dbfile)
        cursor = connection.cursor()

        sql = "select * from dblocation"
        print(sql)
        try:
            cursor.execute(sql)
        except sqlite3.Error as er:
            print('create dblocation  error', er)
            Advanced.dbname = 'montecarloapp.db'
            SQLstuff.create_tables('')

            connection = sqlite3.connect(dbfile)
            sql = "select * from dblocation"
            cursor.execute(sql)
            print('error')
        rows = cursor.fetchall()
        col = ''
        for row in rows:
            for col in row:
                Advanced.dbname = col
                print(col)

        try:
            connection = sqlite3.connect(col)
        except sqlite3.Error as er:
            col = 'montecarloapp.db'
            connection = sqlite3.connect(col)
            Advanced.dbname = col
            print('error')

        cursor = connection.cursor()
        sql = "select * from advanced"
        print(sql)
        try:
            cursor.execute(sql)
        except sqlite3.Error as er:
            SQLstuff.create_tables('')
            sql = "select * from assumptions"
            cursor.execute(sql)
            print('error')

        rows = cursor.fetchall()
        lastcol = ""
        for row in rows:
            for col in row:
                print('Advanced:', col)
                if lastcol == 'Asset_color':
                    Advanced.asset_color = col
                if lastcol == 'Spending_color':
                    Advanced.spending_color = col
                if lastcol == 'Income_color':
                    Advanced.income_color = col
                if lastcol == 'Run_Summary_color':
                    Advanced.run_summary_color = col
                if lastcol == 'run_detail_color':
                    Advanced.run_detail_color = col
                if lastcol == 'run_detail_header_color':
                    Advanced.run_detail_header_color = col
                if lastcol == 'Currency Symbol':
                    Advanced.currency_symbol = col
                lastcol = col

    def get_assumptions(self):

        list1 = []
        connection = sqlite3.connect(Advanced.dbname)
        cursor = connection.cursor()
        sql = "select * from assumptions"
        print('db', Advanced.dbname)
        try:
            cursor.execute(sql)
        except sqlite3.Error as er:
            SQLstuff.create_tables('')
            sql = "select * from assumptions"
            cursor.execute(sql)
            print('error')

        rows = cursor.fetchall()
        lastcol = ''
        for row in rows:
            for col in row:

                if lastcol == 'Current Age :':
                    Assumptions.start_year = int(col)
                    print("start year=", col)
                if lastcol == 'Life Expectancy :':
                    Assumptions.end_year = int(col)
                    # print ("end year=",col)
                if lastcol == '# of Runs :':
                    Assumptions.runs = int(col)
                    # print ('runs=',col)
                if lastcol == 'ROI SD :':
                    Assumptions.sd = float(col)
                    # print ('SD=',col)
                if lastcol == 'Rate of Return :':
                    Assumptions.roi = float(col)
                    # print ('ROI=',col)
                if lastcol == 'Tax Rate :':
                    Assumptions.tax_rate = float(col)
                if lastcol == 'Investment Tax Rate :':
                    Assumptions.inv_tax_rate = float(col)
                    print('Inv Tax rate=', col)
                if lastcol == 'Inflation Rate :':
                    Assumptions.inflation_rate = float(col)
                    # print ('IR=',col)
                if lastcol == 'Inflation SD :':
                    Assumptions.inflation_SD = float(col)
                    # print ('ISD=',col)

                lastcol = col

    def delete_row(self, table, name_in):

        connection = sqlite3.connect(Advanced.dbname)
        cursor = connection.cursor()
        sql = "begin transaction"
        cursor.execute(sql)

        sql = "delete from  " + table + " where name = '" + name_in + "'"
        print('sql=' + sql)
        cursor.execute(sql)
        sql = "commit"
        cursor.execute(sql)

    def delete_assumptions(self):

        connection = sqlite3.connect(Advanced.dbname)
        cursor = connection.cursor()
        sql = "begin transaction"
        cursor.execute(sql)

        sql = "delete from assumptions"
        print('sql=' + sql)
        cursor.execute(sql)
        sql = "commit"
        cursor.execute(sql)  # cursor.execute("commit")

    def delete_advanced(self):

        connection = sqlite3.connect(Advanced.dbname)
        cursor = connection.cursor()
        sql = "begin transaction"
        cursor.execute(sql)

        sql = "delete from advanced"
        print('sql=' + sql)
        cursor.execute(sql)
        sql = "commit"
        cursor.execute(sql)  # cursor.execute("commit")

        sql = "begin transaction"
        cursor.execute(sql)

        sql = "delete from dblocation"
        try:
            cursor.execute(sql)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            print('dblocation not needed')

        print('sql=' + sql)
        sql = "commit"
        cursor.execute(sql)

        # cursor.execute("commit")

    def update_db_location(self, dbnamen):

        connection = sqlite3.connect('montecarloapp.db')
        cursor = connection.cursor()
        sql = "begin transaction"
        cursor.execute(sql)

        sql = "update dblocation set dblocation = '" + dbnamen + "'"
        print('sql=', dbnamen, sql)
        cursor.execute(sql)
        sql = "commit"
        cursor.execute(sql)  # cursor.execute("commit")

    def create_tables(self):

        print('dbname', Advanced.dbname)

        try:
            connection = sqlite3.connect(Advanced.dbname)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            content = GridLayout(rows=2)
            popup = Popup(content=content, size_hint=(None, None), title='Error', size=(400, 400))
            b1 = Button(text='Close')
            content.add_widget(Label(text='Invaid Location'))
            content.add_widget(b1)

            # bind the on_press event of the button to the dismiss function
            b1.bind(on_press=popup.dismiss)

            popup.open()
            Advanced.dbname = 'montecarloapp.db'
            connection = sqlite3.connect(Advanced.dbname)
            return

        cursor = connection.cursor()

        sql = "begin transaction"
        cursor.execute(sql)

        # print ('create spending')
        sql = "CREATE TABLE dblocation ( dblocation TEXT);"

        print('dblocaton created', Advanced.dbname)
        cursor.execute(sql)

        # print ('create spending')
        sql = "CREATE TABLE `spending` ( `name` TEXT UNIQUE, `amount` NUMERIC, `fromyear` int, `toyear` int, `change` NUMERIC );"
        cursor.execute(sql)

        # print ('create spending')
        sql = "insert into dblocation values('montecarloapp.db');"
        cursor.execute(sql)

        # print ('create income')
        sql = "CREATE TABLE income ( `name` TEXT UNIQUE, `amount` NUMERIC, `fromyear` int, `toyear` int, `change` NUMERIC )"
        cursor.execute(sql)

        # print ('create assumptions')
        sql = "CREATE TABLE assumptions (`name` TEXT UNIQUE,`value` text)"

        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Current Age :','55')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Life Expectancy :','95')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Rate of Return :','4')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('ROI SD :','2')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Tax Rate :','1')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Investment Tax Rate :','1')"
        cursor.execute(sql)

        sql = "INSERT INTO `assumptions` VALUES ('Inflation Rate :','1')"
        cursor.execute(sql)
        sql = "INSERT INTO `assumptions` VALUES ('Inflation SD :','1')"
        cursor.execute(sql)
        sql = "INSERT INTO `assumptions` VALUES ('# of Runs :','1')"
        cursor.execute(sql)

        # print ("create assets")
        sql = "CREATE TABLE assets ( `name` TEXT UNIQUE, `amount` NUMERIC, `type` text, `dummy1` TEXT, `dummy2` TEXT )"
        cursor.execute(sql)

        # print ("create assetType")
        sql = "CREATE TABLE Advanced ( `name` TEXT, `value` TEXT )"
        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('Currency Symbol','$');"
        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('run_detail_header_color','#ff7f32ff');"

        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('Spending_color','#7f9fffff');"

        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('Spending_color','#7f9fffff');"
        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('Income_color','#ff3232ff');"
        cursor.execute(sql)

        sql = "INSERT INTO Advanced VALUES ('Run_Summary_color','');"
        cursor.execute(sql)

        sql = "commit"
        cursor.execute(sql)

    def get_data(self, table, where):
        # print('sqlstuff')
        list = []
        list.clear()

        connection = sqlite3.connect(Advanced.dbname)
        cursor = connection.cursor()
        sql = "select * from " + table

        if table == "assetsx":
            sql = "select name,amount from assets"

        if where != '':
            sql = sql + where

        sql = sql + " order by 1"

        print('db', Advanced.dbname)
        try:
            cursor.execute(sql)
            # cursor.execute("commit")

        except sqlite3.Error as er:
            SQLstuff.create_tables('')
            sql = "select * from " + table
            cursor.execute(sql)
            print('errror')

        rows = cursor.fetchall()

        if table == 'assetsx':
            list.append("ASSET")
            list.append("VALUE")
        else:
            if table == 'spendingx':
                list.append("NAME")
                list.append("VALUE")
                list.append("FROM")
                list.append("TO")
            else:
                if table == 'incomex':
                    list.append("NAME")
                    list.append("VALUE")
                    list.append("FROM")
                    list.append("TO")
                else:
                    if table == 'assumptions':
                        list.append("PARAMETER")
                        list.append("VALUE")
                    else:
                        if table == 'run':
                            list.append("OUTPUT")
                            list.append("VALUE")
        for row in rows:
            for col in row:
                list.append(col)

        # print ("After SQLStuff",len(list))

        return list

    def format_row_with_markup(self, table):

        lista = SQLstuff.get_data(self, table, '')

        listall = []

        ix = 0
        ix1 = 0

        markup4 = ''
        markup5 = ''
        markup6 = ''

        number_of_cols = 5
        if table == 'assets':
            color = Advanced.asset_color
            number_of_cols = 5
        else:
            if table == 'spending':
                color = Advanced.spending_color
                number_of_cols = 5
            else:
                if table == 'income':
                    color = Advanced.income_color
                    number_of_cols = 7

        while ix < len(lista) / number_of_cols:
            markup4 = ''
            if table == 'assets':

                markup = SQLstuff.format_markup(self, str(lista[ix1]), color, '', '30', 'i', 'b')
                markup2 = SQLstuff.format_markup(self, '\nValue: ' + Advanced.currency_symbol + str(
                    format(lista[ix1 + 1], ",d")),
                                                 color, '', '20', '', '')
                markup3 = SQLstuff.format_markup(self, '\n' + str(lista[ix1 + 2]), color, '', '20', '', '')
                # markup4 = SQLstuff.formatMarkup(self, '\n' + str(lista[ix1 + 3]), color, '', '20', '', '')
                # markup5 = SQLstuff.formatMarkup(self, '\n' + str(lista[ix1 + 4]), color, '', '20', '', '')
                if int(lista[ix1 + 3]) <= Assumptions.start_year:
                    markup4 = ''
                else:
                    lista[ix1 + 3] = "Aquire at Age " + str(lista[ix1 + 3])
                    markup4 = SQLstuff.format_markup(self,
                                                     '\n ' + str(lista[ix1 + 3]),
                                                     color, '', '20', '', '')

            else:
                markup = SQLstuff.format_markup(self, str(lista[ix1]), color, '', '30', 'i', 'b')
                markup2 = SQLstuff.format_markup(self,
                                                 '\n' + Advanced.currency_symbol + str(
                                                     format(lista[ix1 + 1], ",d")) + ' a year',
                                                 color, '', '20', '', '')

                if lista[ix1 + 2] <= Assumptions.start_year:
                    lista[ix1 + 2] = "Start of Plan"
                else:
                    lista[ix1 + 2] = "Age " + str(lista[ix1 + 2])

                if lista[ix1 + 3] >= Assumptions.end_year:
                    lista[ix1 + 3] = "End of Plan"
                else:
                    lista[ix1 + 3] = "Age " + str(lista[ix1 + 3])

                if str(lista[ix1 + 2]) == 'Start of Plan' and str(lista[ix1 + 3]) == 'End of Plan':
                    markup3 = SQLstuff.format_markup(self, '\n' + 'For Life', color, '', '20', '', '')
                else:
                    if str(lista[ix1 + 2]) == str(lista[ix1 + 2]):
                        markup3 = SQLstuff.format_markup(self,
                                                         '\nAt  ' + str(lista[ix1 + 2]),
                                                         color, '', '20', '', '')
                    else:
                        markup3 = SQLstuff.format_markup(self,
                                                         '\nFrom  ' + str(lista[ix1 + 2]) + ' to ' + str(
                                                             lista[ix1 + 3]),
                                                         color, '', '20', '', '')

                if str(lista[ix1 + 4]) != "0":
                    markup4 = SQLstuff.format_markup(self, '\nAdjust by   ' + str(lista[ix1 + 4]) + "% A year", color,
                                                    '', '20', '', '')
                if table == 'income':
                    print ('HERE',table,lista[ix1 + 5],lista[ix1 + 6])
                if table == 'income' and lista[ix1 + 5] == 'True':
                    if lista[ix1 + 6] == 0:
                        markup6 = SQLstuff.format_markup(self, '\nTax Free', color,
                                                     '', '20', '', '')
                    else:
                        markup6 = SQLstuff.format_markup(self, '\nTax Rate   ' + str(lista[ix1 + 6]) + "% A year",
                                                         color,
                                                         '', '20', '', '')
                else:
                    markup6 = ''

            listall.append(markup + markup2 + markup3 + markup4 + markup5 + markup6)

            # listall.append([b]Hello [color=ff0000]world[/color][/b])
            ix = ix + 1
            ix1 = ix1 + number_of_cols

        return listall

    def format_markup(self, textIn, colorIn, fontIn, sizeIn, formatIn, format2In):
        markup_startcol = '[color=' + colorIn + ']'
        markup_endcol = '[/color]'

        if formatIn != '':
            markup_startformat = '[' + formatIn + ']'
            markup_endformat = '[/' + formatIn + ']'
        else:
            markup_startformat = ''
            markup_endformat = ''

        if format2In != '':
            markup_startformat2 = '[' + format2In + ']'
            markup_endformat2 = '[/' + format2In + ']'
        else:
            markup_startformat2 = ''
            markup_endformat2 = ''

        markup_startfont = '[size=' + sizeIn + ']'
        markup_endfont = '[/size]'
        return markup_startcol + markup_startformat + markup_startformat2 + markup_startfont + textIn + markup_endfont + markup_endformat2 + markup_endformat + markup_endcol


class MainRoot(Screen):
    root2 = BoxLayout()

    def edit_assets(self, instance):
        # print ("save Assets")
        # print('The button <%s> is being pressed' % instance.text)
        self.remove_widget(self.root2)

        whereClause = self.get_where(instance.text)
        global listrow
        listrow = SQLstuff.get_data(self, 'assets', whereClause)

        # print('Listrowbef',str(listrow))
        print(str(listrow))

        print('APN: edit_assets')
        # self.manager.current = '_assetpopupnew_'
        # popup = AssetPopupNew()
        self.Assetspopup.open()
        # print ("BACkFrompop")

    def get_where(self, textIn):
        # print( " where name = '" + textIn[textIn.find('[size=30]')+9:textIn.find('[/size]')] + "'")
        return " where name = '" + textIn[textIn.find('[size=30]') + 9:textIn.find('[/size]')] + "'"

    def edit_spending(self, instance):
        # print ("save spending")
        # print('The button <%s> is being pressed' % instance.text)
        self.remove_widget(self.root2)
        # btna.text.find('[size=30]')

        whereClause = self.get_where(instance.text)
        # whereClause = " where name = '" + instance.text[instance.text.find('[size=30]')+9:instance.text.find('[/size]')] + "'"
        global listrow
        listrow = SQLstuff.get_data(self, 'spending', whereClause)
        self.Spendingpopup.open()
        # print ("BACkFrompop")

    def edit_income(self, instance):
        # print ("save Income")
        # print('The button <%s> is being pressed' % instance.text)
        self.remove_widget(self.root2)
        # print ('Income:', instance.text[14+9:instance.text.find('[/size]')])

        whereClause = self.get_where(instance.text)
        global listrow
        listrow = SQLstuff.get_data(self, 'income', whereClause)
        self.Incomepopup.open()
        # print ("BACkFrompop")

    def add_asset(self, instance):
        # print ('add aset')
        global listrow
        listrow.clear()

        self.Assetspopup.open()

    def add_income(self, instance):

        # print ('add income')
        listall = SQLstuff.format_row_with_markup('', 'income')
        global listrow

        listrow.clear()
        self.Incomepopup.open()

    def add_spending(self, instance):

        # SQLstuff.insertRow(self, 'assets',"##New_Asset##",'0','','')

        # print ('add spending')
        global listrow

        listrow.clear()
        self.Spendingpopup.open()

    def run(self, instance):
        Advanced.more_details = False
        listrow.clear()
        self.Runpopup.open()

    def runD(self, instance):
        Advanced.more_details = True
        listrow.clear()
        self.Runpopup.open()

    def advanced(self, instance):

        self.Advancedpopup.open()

    def assumptions(self, instance):
        self.manager.current = '_assumptionsroot_'

    # i =  self.index

    def __init__(self, **kwargs):
        super(MainRoot, self).__init__(**kwargs)

        global asr
        asr = self
        self.layout = self.create_screen()
        self.add_widget(self.layout)
        self.Assetspopup = AssetPopup()
        self.Incomepopup = IncomePopup()
        self.Spendingpopup = SpendingPopup()
        self.Advancedpopup = AdvancedPopup(size_hint=(.8, 1))
        self.Runpopup = RunPopup(size_hint=(1, 1), size=(1000, 1000))

        # self.add_widget(self.root2)

    def create_screen(self):

        listall = SQLstuff.format_row_with_markup('', 'assets')
        layouta = GridLayout(cols=1, spacing=10, size_hint_y=None)
        # print ('len=',len(listall))
        layouta.bind(minimum_height=layouta.setter('height'))
        for i in range(len(listall)):
            # for i in range(2):
            btna = Button(text=str(i), size_hint_y=None, height=130)

            btna.markup = True
            text = "[color=ffff99]" + listall[i] + "\n[/color] [color=ff0099]World[/color]\n"
            btna.text = text
            btna.text = listall[i]

            # btn.font_size =  '20pt'
            btna.bind(on_press=self.edit_assets)
            layouta.add_widget(btna)

        listall = SQLstuff.format_row_with_markup('', 'income')
        layouti = GridLayout(cols=1, spacing=10, size_hint_y=None)
        # print ('len=',len(listall))
        layouti.bind(minimum_height=layouti.setter('height'))
        for i in range(len(listall)):
            # for i in range(2):
            btni = Button(text=str(i), size_hint_y=None, height=130)

            btni.markup = True
            text = "[color=ffff99]" + listall[i] + "\n[/color] [color=ff0099]World[/color]\n"
            btni.text = text
            btni.text = listall[i]

            # btn.font_size =  '20pt'
            btni.bind(on_press=self.edit_income)
            layouti.add_widget(btni)

        listall = SQLstuff.format_row_with_markup('', 'spending')
        layouts = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layouts.clear_widgets()
        # print ('len= spend',len(listall))
        layouts.bind(minimum_height=layouts.setter('height'))
        # for i in range(len(listall)):
        layouts.clear_widgets()
        for i in range(len(listall)):
            btns = Button(text=str(i), size_hint_y=None, height=130)
            btns = Button(size_hint=(1.0, None), halign="left", valign="middle", height=130)

            btns.markup = True
            btns.text = listall[i]

            text = "[color=fff099]" + listall[i] + "\n[/color] [color=ff0099]World[/color]\n"
            btns.text = text
            btns.text = listall[i]
            # print ('text=',btns.text)

            # btn.font_size =  '20pt'
            btns.bind(on_press=self.edit_spending)
            layouts.add_widget(btns)

        s1 = ScrollView(size_hint=(1, 1))
        s2 = ScrollView(size_hint=(1, 1))
        s3 = ScrollView(size_hint=(1, 1))

        s3.add_widget(layouts)
        s2.add_widget(layouti)

        s1.add_widget(layouta)
        # bl2.height = self.minimum_height
        wl = Label(text="       Monte Carlo or Bust?", size_hint=(.1, .03))

        wl.markup = True
        wl.text = "[color=fff099]" + "       Monte Carlo or Bust?" + "\n[/color]"

        wl.font_size = min(self.height, self.width) / 3

        layout = GridLayout(cols=3, row_force_default=False, row_default_height=20)

        l1 = Label(text='Assets', size_hint=(.1, .015))
        layout.add_widget(l1)
        markup_startcol = '[color=' + Advanced.asset_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        l1.markup = True
        l1.text = markup_startcol + markup_startfont + "Assets" + markup_endfont + markup_endcol

        l1.text = SQLstuff.format_markup(self, "Assets", Advanced.asset_color, '', '30', 'i', 'b')

        l2 = Label(text='Income', size_hint=(.1, .015))
        layout.add_widget(l2)
        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        l2.markup = True

        l2.text = SQLstuff.format_markup(self, "Income", Advanced.income_color, '', '30', 'i', 'b')

        l3 = Label(text='Spending', size_hint=(.1, .015))
        layout.add_widget(l3)
        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        l3.markup = True
        l3.text = markup_startcol + markup_startfont + Advanced.spending_color + markup_endfont + markup_endcol

        l3.text = SQLstuff.format_markup(self, "Spending", Advanced.spending_color, '', '30', 'i', 'b')

        b1 = Button(text='+', size_hint=(.1, .015))
        b2 = Button(text='+', size_hint=(.1, .015))
        b3 = Button(text='+', size_hint=(.1, .015))

        layout.add_widget(b1)
        layout.add_widget(b2)
        layout.add_widget(b3)
        b1.bind(on_press=self.add_asset)
        b2.bind(on_press=self.add_income)
        b3.bind(on_press=self.add_spending)
        layout.add_widget(s1)
        layout.add_widget(s2)
        layout.add_widget(s3)

        layout.add_widget(Label(text='', size_hint=(.1, None), height=5))
        layout.add_widget(Label(text='', size_hint=(.1, None), height=5))
        layout.add_widget(Label(text='', size_hint=(.1, None), height=5))
        btnRun = Button(text='Run', size_hint=(.1, .01))
        btnRunD = Button(text='Run', size_hint=(.1, .01))

        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        btnRun.markup = True
        btnRun.text = markup_startcol + markup_startfont + "Run" + markup_endfont + markup_endcol

        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        btnRunD.markup = True
        btnRunD.text = markup_startcol + markup_startfont + "Detailed Run \n**longer runtime" + markup_endfont + markup_endcol

        buttons  = GridLayout(cols=4, spacing=10, size_hint_y=None,height=50)


        buttons.add_widget(btnRun)
        btnRun.bind(on_press=self.run)
        buttons.add_widget(btnRunD)
        btnRunD.bind(on_press=self.runD)
        btnA = Button(text='Assumptions', size_hint=(.1, .015))
        btnB = Button(text='Advanced', size_hint=(.1, .015))

        buttons.add_widget(btnA)
        buttons.add_widget(btnB)
        btnA.bind(on_press=self.assumptions)
        btnB.bind(on_press=self.advanced)

        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        btnA.markup = True
        btnA.text = markup_startcol + markup_startfont + "Assumptions" + markup_endfont + markup_endcol

        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=15]'
        markup_endfont = '[/size]'
        btnB.markup = True
        btnB.text = markup_startcol + markup_startfont + "Settings" + markup_endfont + markup_endcol

        runlayout = FloatLayout()

        runlayout.add_widget(layout)
        runlayout.add_widget(buttons)

        return runlayout


class AssumptionsRoot(Screen):
    # print('here1')

    # name = '_assumptionsroot_'
    t1 = TextInput(size_hint_x=None, width=60, height=50)
    l02 = Label(text="", size_hint=(0.2, 0.5), halign="left", valign="middle", width=50, height=50)

    l03 = Label(text="", size_hint=(0.2, 0.5), halign="left", valign="middle", width=50, height=50)

    l1 = Label(text="Current Age :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50, height=50)

    s1 = Slider(min=0, max=100)

    l2 = Label(text="Life Expectancy :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50,
               height=50)

    t2 = TextInput(size_hint_x=None, width=60, height=50)

    s2 = Slider(min=25, max=120)

    l3 = Label(text="Rate of Return :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50,
               height=50)

    t3 = TextInput(size_hint_x=None, width=60, height=50)

    s3 = Slider(min=-10, max=20)

    l4 = Label(text="ROI SD :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50, height=50)

    t4 = TextInput(size_hint_x=None, width=60, height=50)

    s4 = Slider(min=0, max=6)

    l5 = Label(text="Tax Rate :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50, height=50)
    l9 = Label(text="Investment Tax Rate :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50,
               height=50)

    t5 = TextInput(size_hint_x=None, width=60, height=50)
    t9 = TextInput(size_hint_x=None, width=60, height=50)

    s5 = Slider(min=0, max=60)
    s9 = Slider(min=0, max=60)

    l6 = Label(text="Inflation Rate :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50,
               height=50)
    t6 = TextInput(size_hint_x=None, width=60, height=50)
    s6 = Slider(min=0, max=15)

    l7 = Label(text="Inflation SD :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50, height=50)
    t7 = TextInput(size_hint_x=None, width=60, height=50)
    s7 = Slider(min=0, max=10)

    l8 = Label(text="# of Runs :     ", size_hint=(0.2, 0.5), halign="center", valign="middle", width=50, height=50)
    t8 = TextInput(size_hint_x=None, width=60, height=50)
    s8 = Slider(min=1, max=20000)

    def __init__(self, **kwargs):
        super(AssumptionsRoot, self).__init__(**kwargs)

        assumptions = SQLstuff.get_assumptions('')

        print('start year2', Assumptions.start_year)

        self.t1.text = str(Assumptions.start_year)
        self.t2.text = str(Assumptions.end_year)
        self.t3.text = str(Assumptions.roi)
        self.t4.text = str(Assumptions.sd)
        self.t5.text = str(Assumptions.tax_rate)
        self.t6.text = str(Assumptions.inflation_rate)
        self.t7.text = str(Assumptions.inflation_SD)
        self.t8.text = str(Assumptions.runs)
        self.t9.text = str(Assumptions.inv_tax_rate)
        self.s1.value = Assumptions.end_year
        self.s2.value = Assumptions.end_year
        self.s3.value = Assumptions.roi
        self.s4.value = Assumptions.sd
        self.s5.value = Assumptions.tax_rate
        self.s6.value = Assumptions.inflation_rate
        self.s7.value = Assumptions.inflation_SD
        self.s8.value = Assumptions.runs

        # self.popupR = RunPopupNew(size_hint=(1, 1), size=(1000, 1000))

        bl = BoxLayout(orientation='vertical')
        bl.title = 'Assumption'
        gl = GridLayout(rows=30, cols=3, row_force_default=True, row_default_height=40)
        l1 = Label(text="Current Age :", size_hint=(1.0, 1.0), halign="center", valign="middle")

        l1.bind(size=l1.setter('text_size'))

        # l0 = Label(text="Assumptions:                                                       ", size_hint=(0.2, 0.5), halign="left", valign="middle", width=50,height=50)
        title = 'Assumptions:                                                                                            '
        l0 = Label(text=title, color=[150, 106, 188, 1])
        gl.add_widget(l0)
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))

        # gl.add_widget(Label(text='Current Age:',size_hint_x=None, width=50,height=100))
        gl.add_widget(l1)
        gl.add_widget(self.t1)
        self.s1.bind(value=self.on_slide_value_change)
        gl.add_widget(self.s1)

        gl.add_widget(self.l2)
        gl.add_widget(self.t2)
        self.s2.bind(value=self.on_slide_value_change_s2)
        gl.add_widget(self.s2)

        gl.add_widget(self.l3)
        gl.add_widget(self.t3)
        self.s3.bind(value=self.on_slide_value_change_s3)
        gl.add_widget(self.s3)

        gl.add_widget(self.l4)
        gl.add_widget(self.t4)
        self.s4.bind(value=self.on_slide_value_change_s4)
        gl.add_widget(self.s4)

        gl.add_widget(self.l5)
        gl.add_widget(self.t5)
        self.s5.bind(value=self.on_slide_value_change_s5)
        gl.add_widget(self.s5)

        gl.add_widget(self.l9)
        gl.add_widget(self.t9)
        self.s9.bind(value=self.on_slide_value_change_s9)
        gl.add_widget(self.s9)

        gl.add_widget(self.l6)
        gl.add_widget(self.t6)
        self.s6.bind(value=self.on_slide_value_change_s6)
        gl.add_widget(self.s6)

        gl.add_widget(self.l7)
        gl.add_widget(self.t7)
        self.s7.bind(value=self.on_slide_value_change_s7)
        gl.add_widget(self.s7)

        gl.add_widget(self.l8)
        gl.add_widget(self.t8)
        self.s8.bind(value=self.on_slide_value_change_s8)
        gl.add_widget(self.s8)

        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))

        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))
        gl.add_widget(Label(text='', size_hint_x=None, width=50, height=100))

        bl2 = GridLayout(rows=2, cols=3, row_force_default=True, row_default_height=40,
                         pos_hint={'center_x': .9, 'center_y': .8}, size_hint=(None, None))

        bl2.bind(minimum_size=bl2.setter('size'))
        # bind the top of the grid to it's height'
        bl2.bind(height=bl2.setter('top'))

        button1 = Button(text='Save', size_hint_x=None, width=100, height=100)
        button2 = Button(text='Cancel', size_hint_x=None, width=100, height=100)
        button3 = Button(text='Run', size_hint_x=None, width=100, height=100)
        button1.bind(on_press=self.save)
        button2.bind(on_press=self.cancel)
        button3.bind(on_press=self.run)
        bl2.add_widget(button1)
        bl2.add_widget(button2)
        # bl2.add_widget(button3)

        gl.add_widget(bl2)

        bl.add_widget(gl)

        self.add_widget(bl)

    #

    def on_slide_value_change(self, instance, value):
        self.t1.text = str(round(value))

    def on_slide_value_change_s2(self, instance, value):
        self.t2.text = str(round(value))

    def on_slide_value_change_s3(self, instance, value):
        value = self.round05(value)
        self.t3.text = str(value) + "%"

    def on_slide_value_change_s4(self, instance, value):
        value = self.round05(value)
        self.t4.text = str(value) + "%"

    def on_slide_value_change_s5(self, instance, value):
        value = self.round05(value)
        self.t5.text = str(value) + "%"

    def on_slide_value_change_s6(self, instance, value):
        value = self.round05(value)
        self.t6.text = str(value) + "%"

    def on_slide_value_change_s7(self, nstance, value):
        value = self.round05(value)
        self.t7.text = str(value) + "%"

    def on_slide_value_change_s8(self, instance, value):
        self.t8.text = str(round(value))

    def on_slide_value_change_s9(self, instance, value):
        value = self.round05(value)
        self.t9.text = str(value) + "%"

    def round05(self, number):
        return (round(number * 4) / 4)

    def save(self, instance):
        self.save_assumptions()
        self.manager.current = '_mainroot_'
        # print('save')

    def save_assumptions(self):
        SQLstuff.delete_assumptions(self)

        SQLstuff.insert_row(self, "assumptions", self.l1.text, str(self.t1.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l2.text, str(self.t2.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l3.text, str(self.t3.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l4.text, str(self.t4.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l5.text, str(self.t5.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l6.text, str(self.t6.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l7.text, str(self.t7.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l8.text, str(self.t8.text), "", "", '')
        SQLstuff.insert_row(self, "assumptions", self.l9.text, str(self.t9.text), "", "", '')

        # print('save assumnptions')

    def cancel(self, instance):
        # print('cancel')
        self.manager.current = '_mainroot_'

    def assets(self):
        # print('In Assets')

        # col_cnt = 3
        self.manager.current = '_mainroot_'

    def income(self):
        # print('test2')

        # col_cnt = 2
        data_items = ListProperty([])
        self.manager.current = '_incomeroot_'

    def spending(self):
        # print('test2')

        self.manager.current = '_spendingroot_'

    def run(self, instance):
        # print('test2')
        self.save_assumptions()

        # print ("abt to run")
        MonteC_run.MCrun().runmc()
        SQLstuff.get_data('', "run", '')

        self.Runpopup.open()


class AdvancedPopup(Popup):
    print("APN")

    title = 'Advanced'

    bl = BoxLayout(orientation='vertical')

    main = GridLayout(rows=1, cols=2)
    content = main
    gl3 = GridLayout(rows=1, cols=9, size_hint_x=.2, size_hint_y=.1, row_force_default=True, row_default_height=40)
    g2 = GridLayout(rows=14, cols=2, row_force_default=False, row_default_height=60)
    b1 = Button(text="Save", size_hint_x=None, width=200)
    b3 = Button(text="Cancel", size_hint_x=None, width=200)
    l1 = Label(text="Select Schema")
    l2 = Label(
        text="Text Colors\n - Select Color using tool on the right \n - Click appropriate button on right to assign ")
    l3 = Label(text="")
    l4 = Label(text="")
    l11 = Label(text="")
    l7 = Label(text="Currency Symbol")
    l12 = Label(text="Plan")
    l13 = Button(size_hint_x=None, width=250)
    l5 = Label(text="")
    l6 = Label(text="")
    l8 = Label(text="")
    l9 = Label(text="")
    l10 = Label(text="")
    clr_picker = ColorPicker()

    # To monitor changes, we can bind to color property changes

    # t1 = FileChooserListView(size_hint_y=None, path='/home/')
    t1 = Button(text='Select Plan', size_hint_x=None, width=200)
    b2 = Button(text='New Plan', size_hint_x=None, width=200)

    t2 = Button(size_hint_x=None, width=250)
    markup_startcol = '[color=' + Advanced.asset_color + ']'
    markup_endcol = '[/color]'
    markup_startfont = '[size=22]'
    markup_endfont = '[/size]'
    t2.markup = True
    t2.text = markup_startcol + markup_startfont + 'Asset' + markup_endfont + markup_endcol

    t3 = Button(text='', size_hint_x=None, width=250)

    t4 = Button(text='', size_hint_x=None, width=250)

    t5 = Button(size_hint_x=None, width=250)

    t6 = Button(size_hint_x=None, width=250)

    t7 = TextInput(size_hint_x=None, width=120)
    t11 = Button(size_hint_x=None, width=250)

    color_picker = ColorPicker(size_hint_x=2, size_hint_y=2, width=100)

    g2.add_widget(l12)
    g2.add_widget(l13)
    g2.add_widget(l7)
    g2.add_widget(t7)
    g2.add_widget(Label())
    g2.add_widget(Label())
    g2.add_widget(l2)
    g2.add_widget(t2)

    g2.add_widget(l3)
    g2.add_widget(t3)

    g2.add_widget(l4)
    g2.add_widget(t4)

    g2.add_widget(l11)
    g2.add_widget(t11)

    g2.add_widget(l5)
    g2.add_widget(t5)

    g2.add_widget(l6)
    g2.add_widget(t6)
    g2.add_widget(l8)
    g2.add_widget(l9)
    g2.add_widget(l10)

    # g2.add_widget(color_picker)

    g2.add_widget(Label())
    g2.add_widget(Label())
    # g2.add_widget(l8)

    # g2.add_widget(clr_picker)
    gl3.add_widget(b1)
    gl3.add_widget(t1)
    gl3.add_widget(b2)
    gl3.add_widget(b3)
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    # bl.add_widget(g2)

    glm = GridLayout(rows=2, cols=1, size_hint_x=3, size_hint_y=5)
    glm.add_widget(g2)
    glm.add_widget(gl3)
    main.add_widget(glm)
    mainr = GridLayout(rows=3, cols=1, size_hint_x=1, size_hint_y=.2)

    mainr.add_widget(Label(text='Color Picker'))
    mainr.add_widget(color_picker)
    mainr.add_widget(Label())

    main.add_widget(mainr)

    def dismiss_popup(self):
        self._popup.dismiss()

    def __init__(self, *args, **kwargs):
        super(AdvancedPopup, self).__init__(*args, **kwargs)
        self.b3.bind(on_release=self.cancel)
        self.t1.bind(on_release=self.load_db)
        self.l13.bind(on_release=self.load_db)
        self.b2.bind(on_release=self.new_db)
        self.b1.bind(on_release=self.save)
        self.t2.bind(on_release=self.choose_color_asset)
        self.t3.bind(on_release=self.choose_color_income)
        self.t4.bind(on_release=self.choose_color_spending)
        self.t5.bind(on_release=self.choose_color_run_summary)
        self.t6.bind(on_release=self.choose_color_run_detail)
        self.t11.bind(on_release=self.choose_color_run_detail_header)
        self.color_picker.bind(color=self.on_color)
        global advroot
        advroot = self

    def open(self, correct=True):
        super(AdvancedPopup, self).open(correct)

        print('ADV=', Advanced.currency_symbol)

        markup_startcol = '[color=' + Advanced.asset_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t2.markup = True
        self.t2.text = markup_startcol + markup_startfont + 'Assets' + markup_endfont + markup_endcol

        markup_startcol = '[color=' + Advanced.income_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.l13.text = Advanced.dbname.replace(' ', '')
        self.l13.width = 10 * len(Advanced.dbname)
        self.t3.markup = True
        self.t3.text = markup_startcol + markup_startfont + 'Income' + markup_endfont + markup_endcol

        markup_startcol = '[color=' + Advanced.spending_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t4.markup = True
        self.t4.text = markup_startcol + markup_startfont + 'Spending' + markup_endfont + markup_endcol

        print('RSC' + Advanced.run_summary_color + "," + Advanced.asset_color)
        markup_startcol = '[color=' + Advanced.run_summary_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t5.markup = True
        self.t5.text = markup_startcol + markup_startfont + 'Run Summary' + markup_endfont + markup_endcol

        markup_startcol = '[color=' + Advanced.run_detail_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t6.markup = True
        self.t6.text = markup_startcol + markup_startfont + 'Run Detail' + markup_endfont + markup_endcol

        markup_startcol = '[color=' + Advanced.run_detail_header_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t11.markup = True
        self.t11.text = markup_startcol + markup_startfont + 'Run Detail Header' + markup_endfont + markup_endcol

        self.t7.text = Advanced.currency_symbol
        # self.l23.color = [asset_color]

    def load(self, path, filename):
        # with open(os.path.join(path, filename[0])) as stream:
        #   self.text_input.text = stream.read()
        print("here", filename, path)

        self.dismiss()

    def on_color(self, instance, value):
        Advanced.color_chosen = instance.hex_color

    def choose_color_asset(self, instance):
        Advanced.asset_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.asset_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t2.markup = True
        self.t2.text = markup_startcol + markup_startfont + 'Asset' + markup_endfont + markup_endcol

    def choose_color_income(self, instance):
        Advanced.income_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.income_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t3.markup = True
        self.t3.text = markup_startcol + markup_startfont + 'Income' + markup_endfont + markup_endcol

    def choose_color_spending(self, instance):
        Advanced.spending_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.spending_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t4.markup = True
        self.t4.text = markup_startcol + markup_startfont + 'Spending' + markup_endfont + markup_endcol

    def choose_color_run_summary(self, instance):
        Advanced.run_summary_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.run_summary_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t5.markup = True
        self.t5.text = markup_startcol + markup_startfont + 'Run - Summary' + markup_endfont + markup_endcol

    def choose_color_run_detail(self, instance):
        Advanced.run_detail_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.run_detail_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t6.markup = True
        self.t6.text = markup_startcol + markup_startfont + 'Run - Detail' + markup_endfont + markup_endcol

    def choose_color_run_detail_header(self, instance):
        Advanced.run_detail_header_color = Advanced.color_chosen
        markup_startcol = '[color=' + Advanced.run_detail_header_color + ']'
        markup_endcol = '[/color]'
        markup_startfont = '[size=22]'
        markup_endfont = '[/size]'
        self.t11.markup = True
        self.t11.text = markup_startcol + markup_startfont + 'Run - Detail Header' + markup_endfont + markup_endcol

    def save(self, instance):
        SQLstuff.delete_advanced(self)

        SQLstuff.insert_row(self, "dblocation", Advanced.dbname, "", "", "", '')
        print('CS12', self.t7.text, len(self.t7.text))
        Advanced.currency_symbol = self.t7.text
        SQLstuff.insert_row(self, "advanced", "Currency Symbol", self.t7.text, "", "", '')
        SQLstuff.insert_row(self, "advanced", 'Asset_color', str(Advanced.asset_color), "", "", '')
        SQLstuff.insert_row(self, "advanced", 'Spending_color', str(Advanced.income_color), "", "", '')
        SQLstuff.insert_row(self, "advanced", 'Income_color', str(Advanced.spending_color), "", "", '')
        SQLstuff.insert_row(self, "advanced", 'Run_Summary_color', str(Advanced.run_summary_color), "", "", '')
        SQLstuff.insert_row(self, "advanced", 'run_detail_color', str(Advanced.run_detail_color), "", "", '')
        SQLstuff.insert_row(self, "advanced", 'run_detail_header_color', str(Advanced.run_detail_header_color), "", "",
                            '')
        currency_symbol = self.t7.text

        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()

        root.add_widget(root.layout)
        self.dismiss()

    def cancel(self, instance):
        self.dismiss()

    def choose(self, instance):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load_db(self, instance):
        print("HERE1")
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))

        self._popup.open()
        print("HERE2", Advanced.dbname)
        self.l13.text = Advanced.dbname.replace(' ', '')
        self.l13.width = 10 * len(Advanced.dbname)

    def new_db(self, instance):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))

        self._popup.open()
        self.l13.text = Advanced.dbname.replace(' ', '')
        self.l13.width = 10 * len(Advanced.dbname)

    def load_file(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.text_input.text = stream.read()
        self.l13.text = Advanced.dbname.replace(' ', '')
        self.l13.width = 10 * len(Advanced.dbname)

        self.dismiss_popup()


class RunPopup(Popup):
    print("APN")

    title = 'Run'

    layout = GridLayout(cols=1, row_force_default=False, row_default_height=20)

    content = layout

    labPercent = Label(text='Run', size_hint=(1, 1))

    layouta = GridLayout(cols=2, spacing=2, size_hint_y=None, size_hint=(1, 1))
    # print ('len=',len(listall))
    layouta.bind(minimum_height=layouta.setter('height'))
    # for i in range(len(listall)):

    headers = GridLayout(cols=10, row_force_default=False, row_default_height=30, size_hint=(.2, .04))
    layouti = GridLayout(cols=10, spacing=2, size_hint_y=None)
    # print ('len=',len(listall))
    layouti.bind(minimum_height=layouti.setter('height'))

    s1 = ScrollView(size_hint=(1, 1))
    s2 = ScrollView(size_hint=(1, 1))

    s2.add_widget(layouti)

    s1.add_widget(layouta)

    gl1 = GridLayout(cols=2, spacing=2, size_hint_y=None, size_hint=(1, .4))

    gl1.add_widget(labPercent)
    gl1.add_widget(s1)

    # bl2.height = self.minimum_height
    wl = Label(text="       Monte Carlo or Bust?", size_hint=(.1, .03))

    wl.markup = True
    wl.text = "[color=fff099]" + "       Monte Carlo or Bust?" + "\n[/color]"

    layout.add_widget(gl1)
    layout.add_widget(headers)
    layout.add_widget(s2)

    buttons = GridLayout(cols=5, row_force_default=False, row_default_height=20, size_hint=(.1, .04))

    btnRun = Button(text='Run', size_hint=(.1, .01))
    btnChart = Button(text='Chart', size_hint=(.1, .01))

    markup_startcol = '[color=fff099]'
    markup_endcol = '[/color]'
    markup_startfont = '[size=15]'
    markup_endfont = '[/size]'
    btnRun.markup = True
    btnRun.text = markup_startcol + markup_startfont + "Done" + markup_endfont + markup_endcol

    markup_startcol = '[color=fff099]'
    markup_endcol = '[/color]'
    markup_startfont = '[size=15]'
    markup_endfont = '[/size]'
    btnChart.markup = True
    btnChart.text = markup_startcol + markup_startfont + "Chart" + markup_endfont + markup_endcol

    buttons.add_widget(btnRun)
    buttons.add_widget(btnChart)
    buttons.add_widget(Label(text=''))
    btnA = Button(text='Assumptions', size_hint=(.1, .015))
    btnAdv = Button(text='Advanced', size_hint=(.1, .015))

    # buttons.add_widget(btnA)

    markup_startcol = '[color=fff099]'
    markup_endcol = '[/color]'
    markup_startfont = '[size=15]'
    markup_endfont = '[/size]'
    btnA.markup = True
    btnA.text = markup_startcol + markup_startfont + "Assumptions" + markup_endfont + markup_endcol
    layout.add_widget(buttons)

    def __init__(self, *args, **kwargs):
        super(RunPopup, self).__init__(*args, **kwargs)
        self.btnRun.bind(on_release=self.cancel)
        self.btnChart.bind(on_release=self.chart)

    def open(self, correct=True):
        super(RunPopup, self).open(correct)

        # print ("abt to run")
        mc = MonteCarloRun.MonteCarloRunSim()
        self.runOut = mc.run_simulation(Advanced.dbname, Advanced.currency_symbol,Advanced.more_details)
        #self.runOut = mc.run_simulation(Advanced.dbname, Advanced.currency_symbol)
        print("runout", self.runOut)
        # SQLstuff.getData('', "run",'')
        # listall = SQLstuff.getData(self, 'run','')
        headersIn = self.runOut[0]

        self.headers.cols = len(headersIn)
        self.layouti.cols = len(headersIn)

        self.headers.clear_widgets()
        for h in headersIn:
            btn = Button(size_hint=(.5, 4), height=10)
            btn.markup = True
            btn.text = SQLstuff.format_markup(self, h, Advanced.run_detail_header_color, '', '14', 'i', 'b')

            self.headers.add_widget(btn)

        listall = self.runOut[1]
        # print ('len=',len(listall))
        # for i in range(len(listall)):

        markup_startcol = '[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=20]'
        markup_endfont = '[/size]'
        self.labPercent.markup = True
        markup1 = markup_startcol + markup_startfont + "Chance of Success" + markup_endfont + markup_endcol
        markup_startcol = '\n[color=fff099]'
        markup_endcol = '[/color]'
        markup_startfont = '[size=70]'
        markup_endfont = '[/size]'
        self.labPercent.markup = True
        self.labPercent.text = markup1 + markup_startcol + markup_startfont + listall[
            1] + markup_endfont + markup_endcol

        self.layouta.clear_widgets()
        for i in range(len(listall)):
            if i > 1:
                btna = Button(text=str(i), size_hint_y=None, height=25)
                btna.markup = True
                if i % 2 == 1:
                    btna.text = SQLstuff.format_markup(self, Advanced.currency_symbol + str(listall[i]),
                                                       Advanced.run_summary_color, '',
                                                       '25', 'i', 'b')
                else:
                    btna.text = SQLstuff.format_markup(self, str(listall[i]), Advanced.run_summary_color, '', '25', 'i',
                                                       'b')

                    # btn.font_size =  '20pt'
                self.layouta.add_widget(btna)

        listall = self.runOut[2]
        self.layouti.clear_widgets()
        for i in range(len(listall)):
            # for i in range(2):
            btni = Button(text=str(i), size_hint_y=None, height=25)



            btni.markup = True

            btni.text = SQLstuff.format_markup(self, str(listall[i]),

                                         Advanced.run_detail_color, '', '17', 'i', 'b')

            #btni.text = str(listall[i])

            # btni.text = str(listall[i])

            # btn.font_size =  '20pt'
            self.layouti.add_widget(btni)

    def on_slide_value_change_s2(self, instance, value):
        self.t2.text = Advanced.currency_symbol + str(format((round(value / 1000) * 1000), ",d"))

    def save(self, instance):
        print('save', self.spinnerObject.text)
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'assets', listrow[0])
        SQLstuff.insert_row('', 'assets', self.t1.text, self.t2.text, self.spinnerObject.text, '', '')
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def delete(self, instance):
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'assets', listrow[0])
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def cancel(self, instance):
        self.dismiss()

    def chart(self, instance):

        import pandas as pd

        import matplotlib.pyplot as plt

        df = df = pd.DataFrame()

        print('len', len(self.runOut[5]))
        if len(self.runOut[5]) == 3:
            df = pd.DataFrame(index=self.runOut[3],
                              data={self.runOut[5][0]: self.runOut[4][0],
                                    self.runOut[5][1]: self.runOut[4][1],
                                    self.runOut[5][2]: self.runOut[4][2]})
        else:
            if len(self.runOut[5]) == 2:
                df = pd.DataFrame(index=self.runOut[3],
                                  data={self.runOut[5][0]: self.runOut[4][0],
                                        self.runOut[5][1]: self.runOut[4][1]})
            else:
                if len(self.runOut[5]) == 1:
                    print('here', len(self.runOut[5]))
                    df = pd.DataFrame(index=self.runOut[3],
                                      data={self.runOut[5][0]: self.runOut[4][0]})

        ax = df.plot(kind="bar", stacked=True, figsize=(16, 6), title='Asset Values')

        # df.sum(axis=1).plot(ax=ax, color="k")

        plt.show()

    def chart_old(self, instance):
        N = len(self.runOut[4][0])
        print(self.runOut[3])
        print(self.runOut[4][0])
        print(self.runOut[4][1])
        print(self.runOut[4][2])

        print(self.runOut[5])
        menMeans = self.runOut[4][0]
        womenMeans = self.runOut[4][1]
        third = self.runOut[4][2]
        ind = np.arange(N)  # the x locations for the groups
        width = 0.35  # the width of the bars: can also be len(x) sequence

        fig, ax = plt.subplots(num=None, figsize=(16, 6), dpi=80, facecolor='w', edgecolor='k')

        rects1 = ax.bar(ind, menMeans, width)
        rects2 = ax.bar(ind, womenMeans, width,
                        bottom=menMeans)
        rects3 = ax.bar(ind, third, width,
                        bottom=womenMeans)

        ax.set_ylabel('Value (' + Advanced.currency_symbol + ')')
        ax.set_title('Asset Values')
        ax.set_xticks(ind + width)
        ax.set_xticklabels(self.runOut[3])

        ax.legend((rects1[0], rects2[0], rects3[0]), self.runOut[5])

        plt.show()


class AssetPopup(Popup):
    print("APN")
    glm = BoxLayout(orientation='vertical')
    bl = BoxLayout(orientation='vertical')
    content = glm
    title = "Assets"
    glm.title = 'Assumption'
    gl3 = GridLayout(rows=1, cols=7, row_force_default=True, row_default_height=40)
    g2 = GridLayout(rows=5, cols=3, row_force_default=True, row_default_height=40)
    spinnerObject = Spinner(values=("Tax Free", "Taxable", "Tax Deferred"), size_hint_x=None, width=120)
    b1 = Button(text="save")
    b2 = Button(text="delete")
    b3 = Button(text="cancel")
    l1 = Label(text="Name")
    l2 = Label(text="Value")

    l3 = Label(text="Type")

    l4 = Label(text="Aquire Age")

    l5 = Label(text="To age")
    t1 = TextInput(size_hint_x=None, width=250)
    t2 = TextInput(size_hint_x=None, width=120)
    t3 = TextInput(size_hint_x=None, width=120)
    t4 = TextInput(size_hint_x=None, width=120)
    t5 = TextInput(size_hint_x=None, width=120)
    s1 = Label()
    s2 = Slider()
    s2 = Slider(min=0, max=3000000, value=str(1000000))
    s3 = Label()

    s4 = Slider(min=str(Assumptions.start_year), max=96, value=str(Assumptions.start_year))

    s5 = Slider(min=str(Assumptions.start_year), max=96, value=str(95))
    g2.add_widget(l1)
    g2.add_widget(t1)
    g2.add_widget(s1)
    g2.add_widget(l2)
    g2.add_widget(t2)
    g2.add_widget(s2)
    g2.add_widget(l3)
    g2.add_widget(spinnerObject)
    g2.add_widget(s3)

    g2.add_widget(l4)
    g2.add_widget(t4)
    g2.add_widget(s4)

    # g2.add_widget(l5)
    # g2.add_widget(t5)
    # g2.add_widget(s5)

    gl3.add_widget(b1)
    gl3.add_widget(b2)
    gl3.add_widget(b3)
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    bl.add_widget(g2)
    bl.add_widget(gl3)
    glm.add_widget(bl)

    def __init__(self, *args, **kwargs):
        super(AssetPopup, self).__init__(*args, **kwargs)

    def open(self, correct=True):
        super(AssetPopup, self).open(correct)

        if len(listrow) > 0:
            print('LR', listrow)
            self.t1.text = listrow[0]
            self.t2.text = Advanced.currency_symbol + str(format(listrow[1], ",d"))
            self.spinnerObject.text = listrow[2]
            self.s2.value = listrow[1]
            self.s4.value = listrow[3]
            self.s5.value = listrow[4]
            self.t4.text = str(listrow[3])
            self.t5.text = str(listrow[4])
            print('LR', listrow, listrow[3])
        else:
            self.t1.text = 'New Asset'
            self.t2.text = Advanced.currency_symbol + '0'
            self.spinnerObject.text = 'Taxable'
            self.s2.value = 0
            self.t4.text = str(Assumptions.start_year)
            self.t5.text = str(95)
            self.s4.value = str(Assumptions.start_year)
            self.s5.value = str(Assumptions.end_year)
        self.b1.bind(on_release=self.save)

        self.b2.bind(on_release=self.delete)
        self.b3.bind(on_release=self.cancel)
        self.s2.bind(value=self.on_slide_value_change_s2)
        self.s4.bind(value=self.on_slide_value_change_s4)
        self.s5.bind(value=self.on_slide_value_change_s5)

    def on_slide_value_change_s2(self, instance, value):
        self.t2.text = Advanced.currency_symbol + str(format((round(value / 1000) * 1000), ",d"))

    def on_slide_value_change_s4(self, instance, value):
        self.t4.text = str(round(value))

    def on_slide_value_change_s5(self, instance, value):
        self.t5.text = str(round(value))

    def save(self, instance):
        print('save', self.spinnerObject.text)
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'assets', listrow[0])
        SQLstuff.insert_asset('', 'assets', self.t1.text, self.t2.text, self.spinnerObject.text, self.t4.text,
                              self.t5.text)
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def delete(self, instance):
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'assets', listrow[0])
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def cancel(self, instance):
        self.dismiss()


class IncomePopup(Popup):
    print("APN")

    glm = BoxLayout(orientation='vertical')
    bl = BoxLayout(orientation='vertical')
    content = glm
    title = "Income"
    glm.title = 'Assumption'
    gl3 = GridLayout(rows=1, cols=7, row_force_default=True, row_default_height=40)
    g2 = GridLayout(rows=7, cols=3, row_force_default=True, row_default_height=40)
    spinnerObject = Spinner(values=("Tax Free", "Taxable", "Tax Deferred"), size_hint_x=None, width=120)
    b1 = Button(text="save")
    b2 = Button(text="delete")
    b3 = Button(text="cancel")
    l1 = Label(text="Name")
    l2 = Label(text="Annual Amount")
    l3 = Label(text="From age")
    l4 = Label(text="To age")
    l5 = Label(text="Annual Change(%)")
    l6 = Label(text="Non-Standard Tax ")
    l7 = Label(text="Tax Rate")
    t1 = TextInput(size_hint_x=None, width=250)
    t2 = TextInput(size_hint_x=None, width=120)
    t3 = TextInput(size_hint_x=None, width=120)
    t4 = TextInput(size_hint_x=None, width=120)
    t5 = TextInput(size_hint_x=None, width=120)
    t6 = CheckBox(size_hint_x=None, width=120)
    t7 = TextInput(size_hint_x=None, width=120)
    s7 = Label()
    s1 = Label()
    s2 = Slider(min=0, max=250000, value=str(0))
    s3 = Slider(min=str(Assumptions.start_year), max=95, value=str(0))
    s4 = Slider(min=str(Assumptions.start_year), max=100, value=str(95))
    s5 = Slider(min=-5, max=20, value=str(0))
    s6 = Label()
    s7 = Slider(min=-5, max=20, value=str(0))
    g2.add_widget(l1)
    g2.add_widget(t1)
    g2.add_widget(s1)
    g2.add_widget(l2)
    g2.add_widget(t2)
    g2.add_widget(s2)
    g2.add_widget(l3)
    g2.add_widget(t3)
    g2.add_widget(s3)
    g2.add_widget(l4)
    g2.add_widget(t4)
    g2.add_widget(s4)
    g2.add_widget(l5)
    g2.add_widget(t5)
    g2.add_widget(s5)

    g2.add_widget(l6)
    g2.add_widget(t6)
    g2.add_widget(s6)

    gl3.add_widget(b1)
    gl3.add_widget(b2)
    gl3.add_widget(b3)
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    bl.add_widget(g2)
    bl.add_widget(gl3)
    glm.add_widget(bl)

    def __init__(self, *args, **kwargs):
        super(IncomePopup, self).__init__(*args, **kwargs)

    def open(self, correct=True):
        super(IncomePopup, self).open(correct)

        if len(listrow) > 0:
            self.t1.text = listrow[0]
            self.t2.text = Advanced.currency_symbol + str(format(listrow[1], ",d"))
            self.t3.text = str(listrow[2])
            self.t4.text = str(listrow[3])
            self.t5.text = str(listrow[4])
            if listrow[5] == 'True':
                self.t6.active = True
                self.g2.add_widget(self.l7)
                self.g2.add_widget(self.t7)
                self.g2.add_widget(self.s7)

            else:
                self.t6.active = False
                self.g2.remove_widget(self.l7)
                self.g2.remove_widget(self.t7)
                self.g2.remove_widget(self.s7)
            self.t7.text = str(listrow[4]) + "%"
            # self.t4.text = str(listrow[3])
            # self.t5.text = str(listrow[4])
            self.s2.value = listrow[1]
            self.s3.value = listrow[2]
            self.s4.value = listrow[3]
            self.s5.value = str(listrow[4]).replace('%', '')
            self.s7.value = listrow[6]
        else:
            self.t1.text = 'New Income'
            self.t2.text = Advanced.currency_symbol + '0'
            self.t3.text = str(Assumptions.start_year)
            self.t4.text = '99'
            self.t5.text = '0%'
            self.s2.value = '0'
            self.s3.value = '55'
            self.s4.value = '99'
            self.s5.value = '0'
        self.b1.bind(on_release=self.save)
        self.b2.bind(on_release=self.delete)
        self.b3.bind(on_release=self.cancel)
        self.s2.bind(value=self.on_slide_value_change_s2)
        self.s3.bind(value=self.on_slide_value_change_s3)
        self.s4.bind(value=self.on_slide_value_change_s4)
        self.s5.bind(value=self.on_slide_value_change_s5)
        self.s7.bind(value=self.on_slide_value_change_s7)
        self.t6.bind(active=self.on_checkbox_active)

    def on_checkbox_active(self, checkboxInstance, isActive):
        if isActive:
            print('The checkbox is active')
            self.t7.disabled = False
            self.s7.disabled = False

            self.g2.add_widget(self.l7)
            self.g2.add_widget(self.t7)
            self.g2.add_widget(self.s7)
        else:
            print('The checkbox is inactive')

            self.t7.disabled = True
            self.s7.disabled = True

            self.g2.remove_widget(self.l7)
            self.g2.remove_widget(self.t7)
            self.g2.remove_widget(self.s7)

    def on_slide_value_change_s2(self, instance, value):
        self.t2.text = Advanced.currency_symbol + str(format((round(value / 1000) * 1000), ",d"))

    def on_slide_value_change_s3(self, instance, value):
        self.t3.text = str(round(value))

    def on_slide_value_change_s4(self, instance, value):
        self.t4.text = str(round(value))

    def on_slide_value_change_s5(self, instance, value):
        self.t5.text = str(round(value)) + '%'

    def on_slide_value_change_s7(self, instance, value):
        self.t7.text = str(round(value)) + '%'

    def save(self, instance):
        print('save Income')
        global listrow

        if self.t6.active == True:
            self.g2.remove_widget(self.l7)
            self.g2.remove_widget(self.t7)
            self.g2.remove_widget(self.s7)

        if len(listrow) > 0:
            SQLstuff.delete_row('', 'income', listrow[0])

        if self.t6.active == False:
            self.t7.text = -1


        SQLstuff.insert_income('', 'income', self.t1.text, self.t2.text, self.t3.text,
                               self.t4.text, self.t5.text, self.t6.active, self.t7.text.replace('%', ''))
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def delete(self, instance):
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'Income', listrow[0])
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        if self.t6.active == True:
            self.g2.remove_widget(self.l7)
            self.g2.remove_widget(self.t7)
            self.g2.remove_widget(self.s7)

        self.dismiss()

    def cancel(self, instance):
        if self.t6.active == True:
            self.g2.remove_widget(self.l7)
            self.g2.remove_widget(self.t7)
            self.g2.remove_widget(self.s7)

        self.dismiss()


class SpendingPopup(Popup):
    print("APN")

    glm = BoxLayout(orientation='vertical')
    bl = BoxLayout(orientation='vertical')
    content = glm
    title = "Spending"
    glm.title = 'Assumption'
    gl3 = GridLayout(rows=1, cols=7, row_force_default=True, row_default_height=40)
    g2 = GridLayout(rows=5, cols=3, row_force_default=True, row_default_height=40)
    spinnerObject = Spinner(values=("Tax Free", "Taxable", "Tax Deferred"), size_hint_x=None, width=120)
    b1 = Button(text="save")
    b2 = Button(text="delete")
    b3 = Button(text="cancel")
    l1 = Label(text="Name")
    l2 = Label(text="Annual Amount")
    l3 = Label(text="From age")
    l4 = Label(text="To age")
    l5 = Label(text="Annual Change(%)")
    t1 = TextInput(size_hint_x=None, width=250)
    t2 = TextInput(size_hint_x=None, width=120)
    t3 = TextInput(size_hint_x=None, width=120)
    t4 = TextInput(size_hint_x=None, width=120)
    t5 = TextInput(size_hint_x=None, width=120)
    s1 = Label()
    s2 = Slider(min=0, max=250000, value=str(0))
    s3 = Slider(min=str(Assumptions.start_year), max=95, value=str(0))
    s4 = Slider(min=str(Assumptions.start_year), max=100, value=str(95))
    s5 = Slider(min=-5, max=20, value=str(0))
    g2.add_widget(l1)
    g2.add_widget(t1)
    g2.add_widget(s1)
    g2.add_widget(l2)
    g2.add_widget(t2)
    g2.add_widget(s2)
    g2.add_widget(l3)
    g2.add_widget(t3)
    g2.add_widget(s3)
    g2.add_widget(l4)
    g2.add_widget(t4)
    g2.add_widget(s4)
    g2.add_widget(l5)
    g2.add_widget(t5)
    g2.add_widget(s5)
    gl3.add_widget(b1)
    gl3.add_widget(b2)
    gl3.add_widget(b3)
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    gl3.add_widget(Label())
    bl.add_widget(g2)
    bl.add_widget(gl3)
    glm.add_widget(bl)

    def __init__(self, *args, **kwargs):
        super(SpendingPopup, self).__init__(*args, **kwargs)

    def open(self, correct=True):
        super(SpendingPopup, self).open(correct)

        if len(listrow) > 0:
            self.t1.text = listrow[0]
            self.t2.text = Advanced.currency_symbol + str(format(listrow[1], ",d"))
            self.t3.text = str(listrow[2])
            self.t4.text = str(listrow[3])
            self.t5.text = str(listrow[4])
            # self.t4.text = str(listrow[3])
            # self.t5.text = str(listrow[4])
            self.s2.value = listrow[1]
            self.s3.value = listrow[2]
            self.s4.value = listrow[3]
            self.s5.value = str(listrow[4]).replace('%', '')
        else:
            self.t1.text = 'New Spending'
            self.t2.text = Advanced.currency_symbol + '0'
            self.t3.text = str(Assumptions.start_year)
            self.t4.text = '99'
            self.t5.text = '0%'
            self.s2.value = '0'
            self.s3.value = str(Assumptions.start_year)
            self.s4.value = '99'
            self.s5.value = '0'
        self.b1.bind(on_release=self.save)
        self.b2.bind(on_release=self.delete)
        self.b3.bind(on_release=self.cancel)
        self.s2.bind(value=self.on_slide_value_change_s2)
        self.s3.bind(value=self.on_slide_value_change_s3)
        self.s4.bind(value=self.on_slide_value_change_s4)
        self.s5.bind(value=self.on_slide_value_change_s5)

    def on_slide_value_change_s2(self, instance, value):
        self.t2.text = Advanced.currency_symbol + str(format((round(value / 1000) * 1000), ",d"))

    def on_slide_value_change_s3(self, instance, value):
        self.t3.text = str(round(value))

    def on_slide_value_change_s4(self, instance, value):
        self.t4.text = str(round(value))

    def on_slide_value_change_s5(self, instance, value):
        self.t5.text = str(round(value)) + '%'

    def save(self, instance):
        print('save Spending')
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'spending', listrow[0])
        SQLstuff.insert_row('', 'spending', self.t1.text, self.t2.text, self.t3.text, self.t4.text, self.t5.text)
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def delete(self, instance):
        global listrow
        if len(listrow) > 0:
            SQLstuff.delete_row('', 'spending', listrow[0])
        root = asr
        root.layout.clear_widgets()
        root.remove_widget(root.layout)
        root.layout = root.create_screen()
        root.add_widget(root.layout)
        self.dismiss()

    def cancel(self, instance):
        self.dismiss()


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def new_db(self, path, filename):
        print(path, filename)
        global advroot
        advroot.dismiss_popup()

    def load_db(self, path, filename):
        print(path, filename)
        global advroot
        dbnamen = str(filename)
        dbnamen = dbnamen.replace("['", '')
        dbnamen = dbnamen.replace("']", '')
        dbnamen = dbnamen.replace("\\", '/')
        dbnamen = dbnamen.replace("//", '/')
        dbnamen = dbnamen.replace(",", '.')

        print("DBNAME1=", dbnamen)
        SQLstuff.update_db_location(self, dbnamen)
        Advanced.dbname = dbnamen
        advroot.l13.text = Advanced.dbname
        advroot.l13.length = len(Advanced.dbname) * 10
        advroot.dismiss_popup()


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def save_db(self, path, filename):
        print("DB72", path, filename)
        if path == '/':
            path = 'c:/'
        global advroot
        db_name_new = str(path + '/' + filename)
        db_name_new = db_name_new.replace("['", '')
        db_name_new = db_name_new.replace("']", '')
        db_name_new = db_name_new.replace("\\", '/')
        db_name_new = db_name_new.replace("//", '/')
        db_name_new = db_name_new.replace(",", '.')

        SQLstuff.update_db_location(self, db_name_new)
        Advanced.db_name = db_name_new

        print("DBNAME1=", Advanced.db_name)

        SQLstuff.create_tables(self)
        print(str(path), str(filename), Advanced.db_name)
        advroot.l13.text = Advanced.db_name
        advroot.l13.length = len(Advanced.db_name) * 10

        advroot.dismiss_popup()


class MyScreenManager(ScreenManager):
    fred = 0

    def __init__(self, **kwargs):
        super(MyScreenManager, self).__init__(**kwargs)


class MonteCarloOrBustApp(App):
    """App object"""

    def __init__(self, **kwargs):
        super(MonteCarloOrBustApp, self).__init__(**kwargs)

    def build(self):
        # return MainRoot()
        if 1 == 1:
            Config.set('graphics', 'width', '1500')
            Config.set('graphics', 'height', '800')
            Config.write()

        SQLs = SQLstuff()

        SQLs.load_advanced()

        SQLstuff.get_assumptions('')

        print('DBNAME=', Advanced.dbname)

        return MyScreenManager()


MonteCarloOrBustApp().run()
