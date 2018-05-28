#!/usr/bin/python
# -* coding: utf-8 *-*

"""
***********************************************************
*  - Script   : currency_converter.py                     *
*  - Creation : 2018-05-22                                *
*  - Version  : 0.11_20180527                             *
*  - Author   : Jose Luis Rodriguez Ales                  *
*                                                         *
*  Script to Convert Currencies for Kiwi.com Test         *
*                                                         *     
*  (*) Set accepted currencies and default exchange rate  *
* values at cEXCHANGE class                               *
*                                                         * 
***********************************************************
"""

# IMPORT LIBRARIES
import os
import argparse
import json
from decimal import *
from forex_python.converter import CurrencyRates
import datetime
import psycopg2
import cgi

global APP  # APP Entry point, == cMAIN

# IMPORTANT: Set accepted currencies at cEXCHANGE -> accepted_currencies list
# IMPORTANT: Set manual exchange rate values at cEXCHANGE -> set_default_all_exchange_rates function " 

# cMAIN: Main class that holds rest of classes
# ===================================================================
class cMAIN:
    [IO, PARSER, DB, EXCHANGE] = ['', '', '', '']
    
    def __init__(self):
        self.load_classes()    # Initialize classes
        global APP
        APP = self
        
    def MAIN(self):
        global APP
        if APP.IO.get_method() == 'UPDATE_DB': # To be used under crontab
            APP.MAIN_UPDATE_DB()
        elif APP.IO.get_method() == 'CLI':
            APP.MAIN_CLI()
        elif APP.IO.get_method() == 'WEB':
            APP.MAIN_WEB()
    
    def MAIN_UPDATE_DB(self):
        global APP
        APP.DB.init_conn()
        for db_input_currency in APP.EXCHANGE.accepted_currencies:
            for db_output_currency in APP.EXCHANGE.accepted_currencies:
                if db_input_currency == db_output_currency:
                    continue
                else:
                    try:
                        new_exchange_rate = APP.EXCHANGE.load_exchange_rate_value_from_forex_server(db_input_currency, db_output_currency)
                        APP.DB.update_exchange_rate(db_input_currency, db_output_currency, new_exchange_rate)
                    except:
                        APP.PARSER.exit_msg("[ERROR] Retrieving data from Python Forex Server error")
        APP.DB.set_variable("last_updated_time", str(datetime.datetime.now()))
        
    def MAIN_CLI(self):
        APP.IO.set_output_json(APP.generate_json())
        if APP.IO.get_use_of_manual_value():
            print "* [WARNING] Use of manual values (set on %s)\n" % APP.EXCHANGE.get_date_of_manual_values()
        print APP.IO.get_output_json()
    
    def MAIN_WEB(self):
        APP.IO.set_output_json(APP.generate_json())
        print APP.IO.get_output_json()
    
    def generate_json(self):
        global APP
        # JSON OBJECT
        output_json_d = {}
        # INPUT
        output_json_d['input'] = {
                'amount'   : str(Decimal(format(APP.IO.get_amount(), '.3f'))),
                'currency' : str(APP.IO.get_input_currency())
            }
        # OUTPUT
        output_json_d['output'] = {}
        if APP.IO.get_output_all_currencies() == False:
            APP.EXCHANGE.fill_exchange_rate_single_used_value()
            output_json_d['output'][APP.IO.get_output_currency()] = self.calc_output_amount(APP.IO.get_input_currency(), APP.IO.get_amount(), APP.IO.get_output_currency())
        else:
            APP.EXCHANGE.fill_exchange_rate_multiple_used_values()
            for output_currency in APP.EXCHANGE.accepted_currencies:
                if output_currency == APP.IO.get_input_currency():
                    continue
                else:
                    output_json_d['output'][output_currency] = APP.calc_output_amount(APP.IO.get_input_currency(), APP.IO.get_amount(), output_currency)
        # RETURN OF JSON OBJECT            
        return json.dumps(output_json_d)

    def calc_output_amount(self, v_input_currency, v_amount, v_output_currency):
        global APP
        exchange_rate = APP.EXCHANGE.get_exchange_rate(APP.IO.get_input_currency(), v_output_currency)
        output_amount = Decimal(exchange_rate) * Decimal(APP.IO.get_amount())
        return str(Decimal(format(output_amount, '.3f')))
    
    def load_classes(self):
        self.IO       = cIO()
        self.PARSER   = cPARSER()
        self.DB       = cDB()
        self.EXCHANGE = cEXCHANGE()
    

# cEXCHANGE: EXCHANGE class with Currency Exchange functions
# ==========================================================
class cEXCHANGE:
    date_of_manual_values = datetime.date(2018, 05, 22)
    accepted_currencies   = ['EUR', 'CZK', 'USD', 'PLN', 'HRK']
    exchange_rate         = {}
    forex_cr              = object
    
    currency_aliases    = {
        '€'      : 'EUR',
        'EURO'   : 'EUR',
        'EUROS'  : 'EUR',
        '$'      : 'USD',
        'DOLLAR' : 'USD',
        'Kc'     : 'CZK',
        'Zloty'  : 'PLN',
        'kuna'   : 'HRK'
        }
        # ...
    
    def __init__(self):
        self.create_exchange_rate_matrix()
        self.forex_cr = CurrencyRates()
        
    def create_exchange_rate_matrix(self):
        for currency in self.accepted_currencies:
            self.exchange_rate[currency] = {}
            for currency_alt in self.accepted_currencies:
                if not currency == currency_alt:
                    self.exchange_rate[currency][currency_alt] = ''
        
    def get_exchange_rate(self, v_input_currency, v_output_currency):
        ret = False
        try:
            ret = self.exchange_rate[v_input_currency][v_output_currency]
            return ret
        except:
            if APP.EXCHANGE.fill_exchange_rate_single_used_value():
                return self.exchange_rate[v_input_currency][v_output_currency]
            else:
                return False
            
    def currency_alias(self, v_currency_alias):
        ret = v_currency_alias
        if str(v_currency_alias).strip() in self.currency_aliases:
            ret = self.currency_aliases[v_currency_alias]
        elif str(v_currency_alias).strip().upper() in self.currency_aliases:
            ret = self.currency_aliases[str(v_currency_alias).strip().upper()]
        elif str(v_currency_alias).strip().upper() in self.accepted_currencies:
            ret = v_currency_alias.upper()
        return ret
    
    def load_exchange_rate_value_from_file(self, v_input_currency, v_input_file): # To implement
        # Fill Exchange rate VALUE from file
        pass
    
    def load_exchange_rate_values_from_file(self, v_input_currency, v_input_file): # To implement
        # Fill Exchange rate VALUES from file
        pass
    
    def load_exchange_rate_value_from_forex_server(self, v_input_currency, v_output_currency):
        # Load Exchange rte VALUE from Forex Server
        exchange_rate = self.forex_cr.get_rate(v_input_currency, v_output_currency)
        return exchange_rate
    
    
    def load_exchange_rate_values_from_forex_server(self, v_input_currency): # For developing
        # Load Exchange rate VALUES from Forex Server
        for output_currency in APP.EXCHANGE.accepted_currencies:
            if output_currency == APP.IO.get_input_currency():
                continue
            else:
                self.exchange_rate[v_input_currency][output_currency] = APP.EXCHANGE.load_exchange_rate_value_from_forex_server(v_input_currency, output_currency)
        return True
    
    
    def load_exchange_rate_value_from_db(self, v_input_currency, v_output_currency):
        # Load Exchange Rate VALUE from DataBase
        self.exchange_rate[v_input_currency][v_output_currency] = APP.DB.select("SELECT exchange_rate FROM main_exchange_rate WHERE input_currency = '%s' AND output_currency = '%s';" % (v_input_currency, v_output_currency))
    
    def load_exchange_rate_values_from_db(self, v_input_currency):
        # Load Exchange Rate VALUES From DataBase
        try:
            for output_currency in APP.EXCHANGE.accepted_currencies:
                if output_currency == APP.IO.get_input_currency():
                    continue
                else:
                    self.exchange_rate[v_input_currency][output_currency] = APP.DB.select("SELECT exchange_rate FROM main_exchange_rate WHERE input_currency = '%s' AND output_currency = '%s';" % (v_input_currency, output_currency))
        except:
            return False
        return True
    
    def load_exchange_rate_manual_values(self, v_input_currency):
        # Load Exchange Rate VALUES from Manual Values
        self.exchange_rate['EUR']['CZK'] = 25.69      # 2018-05-22, source = Google searcher
        self.exchange_rate['EUR']['USD'] =  1.18      # 2018-05-22, source = Google searcher
        self.exchange_rate['CZK']['EUR'] =  0.039     # 2018-05-22, source = Google searcher
        self.exchange_rate['CZK']['USD'] =  0.046     # 2018-05-22, source = Google searcher
        self.exchange_rate['USD']['EUR'] =  0.85      # 2018-05-22, source = Google searcher
        self.exchange_rate['USD']['CZK'] = 21.80      # 2018-05-22, source = Google searcher
        return True
    
    
    def fill_exchange_rate_single_used_value(self):
        ret = APP.EXCHANGE.load_exchange_rate_value_from_db(APP.IO.get_input_currency(), APP.IO.get_output_currency())
        if ret == '':
            ret = APP.EXCHANGE.load_exchange_rate_value_from_forex_server(APP.IO.get_input_currency(), APP.IO.get_output_currency())
            if ret == '':
                APP.EXCHANGE.load_exchange_rate_manual_values(APP.IO.get_input_currency())
                if ret == '':
                    APP.PARSER.exit_msg("[ERROR] We can't retrieve exchage rate value")
        return True
    
    def fill_exchange_rate_multiple_used_values(self):
        if APP.EXCHANGE.load_exchange_rate_values_from_db(APP.IO.get_input_currency()):
            pass
        elif APP.EXCHANGE.load_exchange_rate_values_from_forex_server(APP.IO.get_input_currency()):
            pass
        elif APP.EXCHANGE.load_exchange_rate_manual_values(APP.IO.get_input_currency()):
            pass
        else:
            APP.PARSER.exit_msg("[ERROR] We can't retrieve exchage rate values")
    
    def get_date_of_manual_values(self):
        return self.date_of_manual_values 
    
    def get_accepted_currencies(self):
        return self.accepted_currencies
    

# cIO: class for getter and setter functions
# ===================================================================
class cIO:
    [input_currency, output_currency, amount]    = ['', '', '']
    [output_all_currencies, manual_values]       = [False, False]
    [parse_method, update_db_task, db_connected] = ['CLI', False, False]
    output_json                                  = object
    
    def __init__(self):
        pass
    
    # Getter functions
    def get_input_currency(self):
        return self.input_currency
    
    def get_output_currency(self):
        return self.output_currency
    
    def get_amount(self):
        return Decimal(self.amount)
    
    def get_output_all_currencies(self):
        return self.output_all_currencies
    
    def get_output_json(self):
        return self.output_json
    
    def get_use_of_manual_value(self):
        return self.manual_values
    
    def get_crontab_db_fill(self):
        return self.crontab_db_fill
    
    def get_method(self):
        return self.method
    
    def get_db_connected(self):
        return self.db_connected
    
    # Setter functions
    def set_input_currency(self, v_input_currency):
        self.input_currency = v_input_currency
        
    def set_output_currency(self, v_output_currency):
        self.output_currency = v_output_currency
        
    def set_amount(self, v_amount):
        self.amount = str(v_amount)
        
    def set_output_all_currencies(self, b_output_all_currencies):
        self.output_all_currencies = b_output_all_currencies

    def set_output_json(self, v_output_json):
        self.output_json = v_output_json

    def set_use_of_manual_values(self, b_manual_values):
        self.manual_values = b_manual_values
        
    def set_crontab_db_fill(self, b_crontab_db_fill):
        self.crontab_db_fill = b_crontab_db_fill
    
    def set_method(self, v_method):
        self.method = v_method
        
    def set_db_connected(self, b_db_connected):
        self.get_db_connected = True
        

# cDB: class for DB functions
# ===========================
class cDB:
    conn, cur, db_connected = ['', '', False]
    
    def __init__(self):
        pass
    
    def init_conn(self):
        global APP
        # CONNECTOR INITIALIZATION
        try:
            self.conn=psycopg2.connect("dbname='currency_converter' user='currency_converter' password='kiwi_test' host='127.0.0.1'")
        except:
            APP.PARSER.exit_msg('[ERROR] Unable to connect to the database')
        # CURSOR INITIALIZATION
        self.cur = self.conn.cursor()
        self.db_connected = True
                
    def update_exchange_rate(self, v_input_currency, v_output_currency, v_exchange_rate):
        if not APP.IO.get_db_connected():
            APP.DB.init_conn()
        self.cur.execute("SELECT exchange_rate FROM main_exchange_rate WHERE input_currency = '%s' AND output_currency = '%s';" % (v_input_currency, v_output_currency))
        if self.cur.rowcount == 0:
            self.cur.execute("INSERT INTO main_exchange_rate (input_currency, output_currency, exchange_rate) VALUES ('%s', '%s', '%s');" % (v_input_currency, v_output_currency, v_exchange_rate))
        elif self.cur.rowcount == 1:
            self.cur.execute("UPDATE main_exchange_rate SET exchange_rate = '%s' WHERE input_currency = '%s' AND output_currency ='%s'" % (v_exchange_rate, v_input_currency, v_output_currency))
        elif self.cur.rowcount > 1:
            self.cur.execute("DELETE FROM main_exchange_rate WHERE input_currency = '%s' AND output_currency = '%s';" % (v_input_currency, v_output_currency))
            self.cur.execute("INSERT INTO main_exchange_rate (input_currency, output_currency, exchange_rate) VALUES ('%s', '%s', '%s');" % (v_input_currency, v_output_currency, v_exchange_rate))
        self.conn.commit()
    
    def select(self, v_sql_select):
        if not APP.IO.get_db_connected():
            APP.DB.init_conn()
        self.cur.execute(v_sql_select)
        ret = self.cur.fetchone()[0]
        return ret
    
    def get_variable(self, v_variable):
        if not APP.IO.get_db_connected():
            APP.DB.init_conn()
        self.cur.execute("SELECT value FROM aux_variable WHERE variable = '%s';" % (v_variable))
        ret = self.cur.fetchone()[0]
        return ret
    
    def set_variable(self, v_variable, v_value):
        if not APP.IO.get_db_connected():
            APP.DB.init_conn()
        self.cur.execute("SELECT value FROM aux_variable WHERE variable = '%s';" % (v_variable))
        if self.cur.rowcount == 0:
            self.cur.execute("INSERT INTO aux_variable (variable, value) VALUES ('%s', '%s');" % (v_variable, v_value))
        elif self.cur.rowcount == 1:
            self.cur.execute("UPDATE aux_variable SET value = '%s' WHERE variable = '%s'" % (v_value, v_variable))
        elif self.cur.rowcount > 1:
            self.cur.execute("DELETE FROM aux_variable WHERE variable = '%s'" % (v_variable))
            self.cur.execute("INSERT INTO aux_variable (variable, value) VALUES ('%s', '%s');" % (v_variable, v_value))
        self.conn.commit()
        
    
    def __del__(self):
        if self.db_connected:
            self.cur.close()
            self.conn.close()
        
    
# cPARSER: class for PARSE arguments
# ===================================================================
class cPARSER:
    args, method  = ['', 'CLI']
    web_usage_msg = "<br /><br /> * USAGE: /currency_converter.py?amount=&lt;amount&gt;&input_currency=&lt;input_currency_code&gt;&output_currency=&lt;output_currency&gt;<br /> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/currency_converter.py?amount=&lt;amount&gt;&input_currency=&lt;input_currency_code&gt;&output_currency=&lt;output_currency&gt;"
    cli_usage_msg = "\n\n * Use %s -h for help" % os.path.basename(__file__)
    
    def __init__(self):
        pass

    def PARSE(self):
        global APP
        if 'REQUEST_METHOD' in os.environ :
            print "Content-type: text/html\n\n"
            print 
            APP.IO.set_method('WEB')
            APP.PARSER.WEB_PARSE()
        else :
            APP.IO.set_method('CLI')
            APP.PARSER.CLI_PARSE()
    
    # CLI PARSE
    # =========
    def CLI_PARSE(self):
        global APP
        # PARSER ARGUMENTS
        parser  = argparse.ArgumentParser()
        group_cli = parser.add_argument_group()
        group_cli.add_argument( "-i", "--input_currency"  , help="Input currency"  )
        group_cli.add_argument( "-o", "--output_currency" , help="Output currency" )
        group_cli.add_argument( "-a", "--amount"          , help="Currency Amount" )
        
        group_crontab = parser.add_argument_group()
        group_crontab.add_argument( "--update_db_exchange_rates"     , help="Recommended to be used at programmed tasks (i.e.: Linux crontab)" , action='store_true' )
        self.args = parser.parse_args()
        
        # PARSING VARIABLE SETTING
        if self.args.update_db_exchange_rates:
            APP.IO.set_crontab_db_fill(self.args.update_db_exchange_rates)
            APP.IO.set_method('UPDATE_DB')
        else:
            APP.IO.set_input_currency  (APP.EXCHANGE.currency_alias(self.args.input_currency))
            APP.IO.set_amount          (APP.PARSER.amount_notattion(self.args.amount))
            APP.IO.set_output_currency (APP.EXCHANGE.currency_alias(self.args.output_currency))
            if APP.IO.get_output_currency() == None:
                APP.IO.set_output_all_currencies(True)
            APP.IO.set_method('CLI')
            # CHECKINGS
            APP.PARSER.do_checks()
    
    # WEB_PARSE
    # =========
    def WEB_PARSE(self):
        global APP
        self.cgi_args = cgi.FieldStorage()
        if not 'input_currency' in self.cgi_args:
            APP.PARSER.exit_msg("[ERROR] It must be entered an accepted input currency code: %s" % str(APP.EXCHANGE.get_accepted_currencies()) + APP.PARSER.get_usage_msg())
        if not 'amount' in self.cgi_args:
            APP.PARSER.exit_msg("[ERROR] It must be entered a valid amount for currency conversion" + APP.PARSER.get_usage_msg())
        # SETTING WEB ARGUMENTS
        APP.IO.set_input_currency  ( str(APP.EXCHANGE.currency_alias(self.cgi_args['input_currency'].value))      )
        APP.IO.set_amount          ( str(APP.PARSER.amount_notattion(self.cgi_args['amount'].value))              )
        if 'output_currency' in self.cgi_args:
            APP.IO.set_output_currency ( str(APP.EXCHANGE.currency_alias(self.cgi_args['output_currency'].value)) )
        else:
            APP.IO.set_output_currency(None)
            APP.IO.set_output_all_currencies(True)
        APP.PARSER.do_checks()
        
    # CHECKINGS
    # =========
    def do_checks(self):
        global APP
        APP.PARSER.check_input_currency()
        APP.PARSER.check_output_currency()
        APP.PARSER.check_amount()
        if APP.IO.get_input_currency() == APP.IO.get_output_currency():
            APP.PARSER.exit_msg("[ERROR] It must be entered a different currency code for input and output currencies" + APP.PARSER.get_usage_msg())
    
    def check_input_currency(self):
        if APP.IO.get_input_currency() == '':
            APP.PARSER.exit_msg("[ERROR] It must be specified A non empty input currency code: %s" % str(APP.EXCHANGE.accepted_currencies()) + APP.PARSER.get_usage_msg())
        elif not APP.IO.get_input_currency() in APP.EXCHANGE.get_accepted_currencies():
            APP.PARSER.exit_msg("[ERROR] (%s) It must be entered an accepted input currency code: %s" % (APP.IO.get_input_currency(), str(APP.EXCHANGE.get_accepted_currencies())) + APP.PARSER.get_usage_msg() )
    
    def check_output_currency(self):
        # Case output_currency NOT defined
        if APP.IO.get_output_currency() == None:
            APP.IO.set_output_all_currencies(True)
        else:
            if not APP.IO.get_output_currency() in APP.EXCHANGE.get_accepted_currencies():
                APP.PARSER.exit_msg("[ERROR] (%s) It must be entered an accepted output currency code: %s" % (APP.IO.get_output_currency(), str(APP.EXCHANGE.get_accepted_currencies())) + APP.PARSER.get_usage_msg())
            APP.IO.set_output_all_currencies(False)

    def check_amount(self):
        try:
            amount_alt = float(APP.IO.get_amount())
        except:
            APP.PARSER.exit_msg("[ERROR] It must be entered a valid amount for currency conversion" + APP.PARSER.get_usage_msg())

    # Other functions
    def amount_notattion(self, v_amount):
        if str(v_amount).count(',') == 1:
            v_amount = str(v_amount).replace(',', '.')
        return v_amount

    def get_usage_msg(self):
        if APP.IO.get_method() == 'WEB':
            return self.web_usage_msg
        else:
            return self.cli_usage_msg

    def exit_msg(self, v_message):
        global APP
        if APP.IO.get_method() == 'WEB':
            print v_message
            exit()
        else:
            exit(v_message)
            

# REFERENCES:
# Currency 3-letter codes: http://www.allembassies.com/currency_codes_by_3-letter_code.htm


# Entry point of the application:
# - initialize APP
# - parse parameters
# - call APP.MAIN()
# ===================================================================

if __name__ == "__main__":
    global APP
    APP = cMAIN();
    APP.PARSER.PARSE()   
    APP.MAIN()
    
    