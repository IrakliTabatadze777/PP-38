import pandas as pd

######################################################################
# Series - ერთ განზომილებიანი
######################################################################
s = pd.Series([10, 20, 30, 40, 50], index=['a', 'b', 'c', 'd', 'e'])

print(s['b'])
print(s.b)


temps = pd.Series(
    [22.5, 18.3, 25.1, 21.0],
    index=["Mon","Tue","Wed","Thu"],
    name="temperature_C"
)


print(temps)


print(temps.iloc[0])
print(temps.iloc[-1])
print(temps[temps > 21])
print(temps.describe())


######################################################################
# DataFrames - ორ განზომილებიანი
######################################################################
emp_dict = {
    "name": ["Alice","Bob","Carol","David"],
    "dept": ["Eng","Mktg","Eng","HR"],
    "salary": [95000., 82000., 110000., 78000.],
    "years": [5, 3, 8, 2],
}




df = pd.DataFrame(emp_dict)

df.to_csv('output.csv', index=False)

salary_df = df.salary
print(salary_df)




emp_dict = [
    {"name": "Alice", "score": 95},
    {"name": "Bob",   "score": 82},
]

df = pd.DataFrame(emp_dict)





# CSV ფაილიდან წაკითხვა/ჩაწერა


df = pd.read_csv(
    'data.csv',
    sep=';',
    index_col='employee_id',
    na_values=["N/A","-","", 'ara'],
    dtype={'salary': float},
    parse_dates=['start_date']
)


print(df.columns.tolist())
print(df.head())
print(df.info())

# ფილტრი
print(df.loc[df["salary"]<70000, "name"])

# გაფილტვრა და შეცვლა
df.loc[df["department"]=="IT", "salary"] *= 1.1

# თარიღის ფორმატის წაკითხვა
print(df.start_date.dt.dayofweek)

# ახალი სვეტის დამატება
df["annual_bonus"] = df["salary"] * 0.10


# რამდენიმე ახალი სვეტის ერთდროულად დამატება
import numpy as np

df = (df.assign(annual_bonus=lambda x: x["salary"] * 0.10,
        total_comp=lambda x: x["salary"] * 1.10,
        seniority=lambda x: np.where(x["years"]>=5, "Senior","Junior"),
    )
)


df.to_csv('output.csv', index=False)


