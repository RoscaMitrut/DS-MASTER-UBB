# Assignments
## 1
1. Formulate a problem relevant to your domain of expertise that needs a data collection process
2. Create a data collection plan either as Information Workflow Diagram or a Plan Table using the following guidelines:
- identify the question that needs to be answered (1st topic in this document)
- identify data sources (try to have at least 2, 3; one should be the file from 3rd topic here)
- consider what type of data you must collect: is it quantitative or qualitative?
- can it be sampled or not?
- how do you store the data- where do you store the data
3. Create an excel/libre office calc file that contains some data related to the problem, making sure that for at least 1 column data contains values specified in different formats (Yes/No and True/False and 0/1) and at least one numeric column has some data with "." separator.

[Workflow Diagrams](https://www.lucidchart.com/pages/tutorial/workflow-diagram)
A Plan Table is just a (excel) file containing all data needed, with source and collection mode.

## 2
Using either a self hosted Jupyter (https://jupyter.org/install or using pip and Python) or https://colab.research.google.com/ available if you have a google (gmail) account, create a Jupyter Notebook that contains the documentation from the first assignment.
Still using the notebook:
- if appropriate, find an API that is relevant for the problem you are solving, and collect some data from it; if not appropriate, skip this step.
- find a website that has data you could use for your use case (currency conversion, weather data, air quality, fuel price, etc...) and build a scraper that collects relevant data and saves it to a csv file. (scraper is mandatory)
For all the steps add text cells that detail the procedures.

## 3
1. Using the files you have already created/downloaded, and the notebook you have created with scrapped data, perform necessary data cleaning and transformation tasks.

Write down in a text cells the steps you perform.

2. Based on the result data from previous step, create a list of entities with attributes and datatypes identified for your use case.  
Create a diagram by hand or using a tool (https://online.visual-paradigm.com/app/diagrams/#diagram:proj=0&type=ClassDiagram&width=11&height=8.5&unit=inch , https://online.visual-paradigm.com/app/diagrams/#diagram:proj=0&type=ERDiagram&width=11&height=8.5&unit=inch)  
to depict the entities and their relationships (also specifying cardinalities).

## 4
1. Install PostgreSQL (version 18 recommended) from https://www.postgresql.org/download/
2. Using pgAdmin4, DBeaver or other IDE, create a new user (dcm_user) that can login and create database
3. Logout and logon with newly created user; create a new database (dcm_db)
4. In 'public' schema of this new database create tables that will store the content of the files you prepared previously
5. Load data from the files you have prepared for pervious assignments into the tables

for Postgresql data types you can check https://www.postgresql.org/docs/current/datatype.html

6. Create a file that stores all the CREATE TABLE scripts and also add the steps you performed to load your data files into your database tables

## 5 
Building upon the previously collected, integrated, and cleaned dataset, the project must also incorporate a comprehensive feature-engineering and data-transformation stage. This includes the identification, construction, and justification of new features that meaningfully enhance the predictive or descriptive capacity of the dataset, as well as the application of appropriate normalization or scaling techniques to ensure comparability across numerical attributes. Furthermore, all categorical variables must be encoded using methods suitable for some potential analytical or machine-learning approach. The rationale behind each transformation step should be clearly explained, demonstrating how these engineered and preprocessed features contribute to the overall effectiveness and robustness of the subsequent data-science workflow. All these steps with their explanations should be included in a document that will be uploaded as assignment solution.

## 6
Starting from the initial analytical objective and the prepared dataset, choose a machine-learning approach that is suitable for the given problem. Focus on matching the model choice with the characteristics of the data, the type of target variable, and possible practical limitations. Explain why the selected model is appropriate in comparison with other possible methods, describe how the model should be trained and evaluated, and how to analyze its performance using suitable evaluation metrics. The document should explain how the modeling choices are consistent with the original problem definition and the data-collection process.