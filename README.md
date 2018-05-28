# kiwi_currency_converter
Script for currency conversions that calculate output currency amount of an output currency or all accepted currencies (set at script) from a given input currency. It takes data from DB that ideally are filled up from Forex Server through a crontab task each short time (i.e.:3 hours). In case DB values are inexistent or obsolet it retrieves data from Forex Server or in last case from Manually inserted Values.

Retrieve exchange_rate: from DB (*) > forex > manual_values
* Recommended to fill DB values from cron tab 

To be used as WEB / CLI / CRON_TASK (--update_db_exchange_rates)

# USAGE
```
usage: currency_converter [-h] [-i INPUT_CURRENCY] [-o OUTPUT_CURRENCY]
                          [-a AMOUNT] [--update_db_exchange_rates]

optional arguments:
  -h, --help            show this help message and exit

  -i INPUT_CURRENCY, --input_currency INPUT_CURRENCY
                        Input currency
  -o OUTPUT_CURRENCY, --output_currency OUTPUT_CURRENCY
                        Output currency
  -a AMOUNT, --amount AMOUNT
                        Currency Amount

  --update_db_exchange_rates
                        Recommended to be used at programmed tasks (i.e.:
                        Linux crontab)
```

# DATABASE
```
- DB Server : PostgreSQL
- DB Name   : currency_converter
- DB User   : currency_converter
- DB Pass   : kiwi_test
- TABLES    : main_exchange_rate (id_exchange_rate, input_currency, output_currency), aux_variable (id_variable, variable, value)
```

* See attached file 20180527_database_creation.txt for DB creation

- imported custom modules:
  psycopg2     : PostgreSQL usage
  forex_python : Forex server interaction


# API
```
APP.MAIN
  .MAIN_UPDATE_DB()
  .MAIN_CLI()
  .MAIN_WEB()
  .generate_json()
  .calc_output_amount(v_input_currency, v_amount, v_output_currency)
  .load_classes()
APP.EXCHANGE
  .create_exchange_rate_matrix()
  .get_exchange_rate(v_input_currency, v_output_currency)
  .currency_alias(v_currency_alias)
  .load_exchange_rate_value_from_file(v_input_currency, v_input_file) # To implement
  .load_exchange_rate_values_from_file(v_input_currency, v_input_file) # To implement
  .load_exchange_rate_value_from_forex_server(v_input_currency, v_output_currency)
  .load_exchange_rate_values_from_forex_server(v_input_currency) # For developing
  .load_exchange_rate_value_from_db(v_input_currency, v_output_currency)
  .load_exchange_rate_values_from_db(v_input_currency)
  .load_exchange_rate_manual_values(v_input_currency)
  .fill_exchange_rate_single_used_value()
  .fill_exchange_rate_multiple_used_values()
  .get_date_of_manual_values()
  .get_accepted_currencies()
APP.IO.
  .get_input_currency()
  .get_output_currency()
  .get_amount()
  .get_output_all_currencies()
  .get_output_json()
  .get_use_of_manual_value()
  .get_crontab_db_fill()
  .get_method()
  .get_db_connected()
  .set_input_currency(v_input_currency)
  .set_output_currency(v_output_currency)
  .set_amount(v_amount)
  .set_output_all_currencies(b_output_all_currencies)
  .set_output_json(v_output_json)
  .set_use_of_manual_values(b_manual_values)
  .set_crontab_db_fill(b_crontab_db_fill)
  .set_method(v_method)
  .set_db_connected(b_db_connected)
APP.DB.
  .init_conn()
  .update_exchange_rate(v_input_currency, v_output_currency, v_exchange_rate)
  .select(v_sql_select)
  .get_variable(v_variable)
  .set_variable(v_variable, v_value)
APP.PARSER.
  .PARSE()
  .CLI_PARSE()
  .WEB_PARSE()
  .do_checks()
  .check_input_currency()
  .check_output_currency()
  .check_amount()
  .amount_notattion(v_amount)
  .get_usage_msg()
  .exit_msg(v_message)
```

# PENDING IMPROVES
- Use of .pgpass (local machine / server side) in order to do NOT attach any password at code
- Call forex_python.exchange_rate() through threats at MAIN_CRON() or used functions for multiple server request at once instead of in a cue
- [IMPORTANT] Use of DB TRANSACTION BLOCK of sentences at .update_exchange_rate() function instead of .commit() calls per each
- Notify when DB values are obsolete (> 6h from variable.last_updated_time)
- Improve of Web Message outputs (font, etc.)
