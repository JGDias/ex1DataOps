from pathlib import Path
import pandas as pd


def run_pipeline(input_file: str, output_file: str) -> None:
    df = pd.read_csv(input_file)

    required_columns = {"order_id", "customer", "amount"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_columns}")

    if (df["amount"] < 0).any():
        raise ValueError("Valores negativos não são permitidos na coluna amount")

    summary = pd.DataFrame(
        {
            "total_sales": [df["amount"].sum()],
            "avg_sales": [df["amount"].mean()],
            "total_orders": [df["order_id"].nunique()],
        }
    )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)


def create_annual_report(input_file: str, output_file: str) -> None:
    df = pd.read_csv(input_file)

    required_columns = {"order_id", "customer", "amount", "date"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_columns}")

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    annual_summary = (
        df.groupby("year")["amount"]
        .agg(total_sales="sum", avg_sales="mean", total_orders="nunique")
        .reset_index()
    )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    annual_summary.to_csv(output_path, index=False)


if __name__ == "__main__":
    run_pipeline("data/sales.csv", "output/summary.csv")
    create_annual_report("data/sales.csv", "output/annual_summary.csv")
