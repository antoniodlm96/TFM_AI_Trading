import os
import sys
from io_stockdata.io_stockdata import download_stock_data, write_stock_data, \
    read_stock_data, read_stock_log, read_portfolio_list, write_portfolio_list
from display.display_utils import display_graph
from pyspark.sql import SparkSession


def get_valid_period():
    periods = ["1d", "5d", "1mo",
               "3mo", "6mo", "1y",
               "2y", "5y", "10y",
               "ytd", "max"]  # Valid periods
    period = ""
    while period not in periods:
        period = str(input("Please, input a valid period: ") or "max")

    return period


def get_valid_interval():
    intervals = ["1m", "2m", "5m",
                 "15m", "30m", "60m",
                 "90m", "1h", "1d",
                 "5d", "1wk", "1mo",
                 "3mo"]  # Valid intervals
    interval = ""
    while interval not in intervals:
        interval = str(input("Please, input a valid interval: ") or "1d")

    return interval


def main():
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

    spark = SparkSession.builder \
        .master("local[1]") \
        .appName("AI_Trading") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    option = -1

    while option != 0:

        option = int(input("Select a valid option: \n" +
                           "0. Exit\n" +
                           "1. Download stock data.\n" +
                           "2. Show stock graph. \n" +
                           "3. Update ALL. \n" +
                           "4. Create Portfolio. \n"))

        if option == 1:
            try:
                stk = input("Please, input a valid stock name: ").upper()
                period = get_valid_period()
                interval = get_valid_interval()
                df = download_stock_data(spark, stk, period, interval)
                write_stock_data(spark, df, stk, period, interval)

            except:
                print("Symbol " + stk + " not found")

        elif option == 2:
            try:
                read_stock_log(spark).orderBy("Stock").show()
                stk = input("Please, input a valid stock name: ").upper()
                period = get_valid_period()
                interval = get_valid_interval()
                df = read_stock_data(spark, stk, period, interval)
                display_graph(df, "DateTime", "Close", stk)
            except:
                print("Empty data, try option -> 1. Download stock data.\n")

        elif option == 3:
            df_stock = read_stock_log(spark)
            df_stock.orderBy("Stock").orderBy("Stock").show()
            list_stock = df_stock.select("Stock").rdd.flatMap(lambda x: x).collect()
            list_period = df_stock.select("Period").rdd.flatMap(lambda x: x).collect()
            list_interval = df_stock.select("Interval").rdd.flatMap(lambda x: x).collect()
            for i in range(len(list_stock)):
                df = download_stock_data(spark, list_stock[i], list_period[i], list_interval[i])
                write_stock_data(spark, df, list_stock[i], list_period[i], list_interval[i])

        elif option == 4:
            df_stock = read_stock_log(spark)
            df_stock.orderBy("Stock").filter("Period = 'max'").orderBy("Stock").show()
            list_stock = df_stock.select("Stock").rdd.flatMap(lambda x: x).collect()
            stk_list = input("Please, input a list separated by comma of stocks: ").upper().replace(" ", "").split(",")
            stk_list = [i for i in stk_list if i in list_stock]
            print("Invalid stock names are removed. List of stocks of the portfolio: ")
            print(stk_list)
            num_shares_list = []
            for i in stk_list:
                num_shares = int(input("Please, input the number of shares of " + i + ": "))
                num_shares_list.append(num_shares)
            write_portfolio_list(spark, stk_list, num_shares_list)
            read_portfolio_list(spark).show()



if __name__ == "__main__":
    main()
