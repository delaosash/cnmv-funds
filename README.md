# cnmv-funds
Import to an Excel file, portfolio securities from [CNMV](http://cnmv.es/portal/home.aspx) periodic fund reports. Optionally, data can also be loaded into a MongoDB database.

Importa a hoja Excel, posiciones de un informe de fondo de inversión español publicado en la web de la [CNMV](http://cnmv.es/portal/home.aspx).
Opcionalmente, también se pueden cargar los datos en una base de datos MongoDB.

# Purpose
Nothing really serious, just a small example of utility programmed in python. I'm trying to follow the python coding conventions. I'm not a Python expert.

# Install
* Install python and pip.
* Install Java 8 (a tabula-py dependency).
* Install required python libraries:
  - pip install PyPDF2
  - pip install tabula-py
  - pip install XlsxWriter
  - pip install mongoengine
* By default, MongoDB functionality is disabled.

# Use
* Download a set of fund report files. An example: https://www.cnmv.es/portal/Consultas/IIC/Fondo.aspx?nif=V82732942&vista=1
* Call the program, passing the files and each one' s percentage in our portfolio, as arguments. All percentages must add up to 100. A file named *portfolio.xlsx* will be generated.
* Example:
  ```
  python cnmv_funds.py 'fund_A.pdf' '10' 'fund_B.pdf' '50' 'fund_C.pdf' '40'
  ```
 # License
 [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)
