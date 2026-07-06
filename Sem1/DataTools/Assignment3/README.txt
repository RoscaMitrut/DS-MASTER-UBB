Title:
    KarstCave_FormationData_2024

Institution:
    Multidisciplinary research group

File name structure:
    Structure: [CaveName]_[SampleType]_[Year].csv
    Attributes: Location (KarstCave), Content (FormationData), Year of collection (2024)

File formats:
    Comma Separated Values (csv) containing tabular data

Column headings for tabular data:
    Sample_ID:
        Description: Unique code identifying the sample
        Type: String
    GPS_Latitude 
        Description: Latitude coordinate of sampling point 
        Units: Decimal degrees 
        Type: Float
    GPS_Longitude 
        Description: Longitude coordinate of sampling point
        Units: Decimal degrees 
        Type: Float
    Formation_Type 
        Description: Speleothem type (stalactite, stalagmite, column, flowstone)
        Type: Categorical
    Mineral_Composition  
        Description: Primary minerals identified via XRD (calcite, aragonite, dolomite, etc.)
        Type: String
    Moisture_Level 
        Description: Measured relative humidity in cave at sampling point
        Units: %
        Type: Float
    Temperature 
        Description: Local cave air temperature
        Units: °C 
        Type: Float
    Collection_Date
        Description: Date when the sample was collected 
        Units: YYYY-MM-DD 
        Type: Date