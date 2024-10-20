import pyodbc
import pandas as pd
if __name__ == "__main__":
     server = 'pa5a2sqlserver.database.windows.net'
     database = 'pa5a2'
     username = 'ntn94210'
     password = 'Password97'
     cnxn = pyodbc.connect(
          'DRIVER={ODBC Driver 18 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
     cursor = cnxn.cursor()
     query = "select scorepos/scoreneg as scoretotal from dbo.score"
     df = pd.read_sql(query, cnxn)
     print(df['scoretotal'].iloc[0])
     print(df)