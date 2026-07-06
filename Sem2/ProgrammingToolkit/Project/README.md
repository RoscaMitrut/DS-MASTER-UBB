# DataLab — Multi-User Dataset Manager

A web application for managing a dataset end-to-end: log in, upload a CSV,
explore it, clean & encode it, train a machine-learning model, and make
predictions. Multiple users can use the app at the same time — accounts are
stored in a database and **each user gets a completely isolated workspace**
(their own dataset and trained model).

## Tech stack
- **Backend:** Flask + Flask-JWT-Extended (auth) + Flask-SQLAlchemy (SQLite) + pandas + scikit-learn
- **Frontend:** React (Vite) + axios + react-router

## Features
| # | Feature | Where |
|---|---------|-------|
| 1 | Login / register, users stored in a SQLite database | `Sign In` screen |
| 2 | Many users at once, each isolated (`threaded=True`, per-user workspaces) | server-wide |
| 3 | Upload a CSV file | **Upload** tab |
| 4 | Rows × columns (`df.shape`) | **Explore → Shape** |
| 5 | Column names + details (`df.dtypes`, nulls, cardinality) | **Explore → Columns & Types** |
| 6 | First **N** rows in a table (`df.head`) | **Explore → First N rows** |
| 7 | Last **N** rows in a table (`df.tail`) | **Explore → Last N rows** |
| 8 | Summary statistics (`df.describe`) | **Explore → Statistics** |
| 9 | Drop empty-value rows (`df.dropna`) | **Explore → Drop Empty Rows** |
| 10 | Choose feature columns for the algorithm | **Train → Feature columns** |
| 11 | Encode/normalize (`pd.get_dummies` / `OrdinalEncoder.fit_transform`) | **Preprocess** tab |
| 12 | Train Regression / Classification / Clustering | **Train** tab |
| 13 | Enter data → server predicts with the trained model | **Predict** tab (form auto-generated from the chosen features) |

## Running it

### 1. Backend (port 5000)
```powershell
pip install -r requirements.txt
python server.py
```

### 2. Frontend (port 5173)
```powershell
cd front
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173), register an account
and sign in.

## Notes
- A sample dataset is included at `data/world-happiness-report-2019.csv`.
- User accounts live in `instance/users.db`; each user's uploaded data and
  trained model are persisted under `instance/userdata/<hash>/`, so work
  survives a server restart.
- The JWT secret in `server.py` is a placeholder — change it before any real
  deployment.
