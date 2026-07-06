# Data dictionary
|  Column |  Type |  Description |
|---|---|---|
|  record_id |  String |  Unique identifier for the record |
|  date |  Date |  Date of the record in YYYY-MM-DD format |
|  category |  String |  Category of the entry (normalized to lowercase, no whitespace) |
|  value  |  Float |  Numerical value of the record (cleaned to ensure >= 0) |
|     unit    |    String    |                  Unit of measurement of value (eg. 'USD', 'ml', 'SEK')                  |
|  source  |  String |  Origin system (merged from source(2022) and source_system(2023)) |
|     status     |     String    |                            Operational status (eg. 'cancelled'/'OK')                           |
|  department  |  String |  Originating department (Only available in 2023 data, missing values in 2022) |
|       priority       |     String    |                            Urgency classification ('low'/'medium'/'high', only available in 2023 data)                           |
|           is_complete           |        Boolean       |                                                                 Derived flag. True if all categorical fields are known (not 'unknown') and value is non-zero.                                                                 |

