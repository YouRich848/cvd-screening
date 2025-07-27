from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# Упрощённая таблица (добавим 30, 50, 60, 70; женщины аналогично)
RISK = {
    30: {"M": {"SBP<140": {"TC<5": {"No": 1, "Yes": 2},
                          "TC>=5": {"No": 1, "Yes": 3}},
               "SBP140-159": {"TC<5": {"No": 1, "Yes": 3},
                              "TC>=5": {"No": 2, "Yes": 4}},
               "SBP>=160": {"TC<5": {"No": 2, "Yes": 4},
                            "TC>=5": {"No": 3, "Yes": 5}}},
          "F": {"SBP<140": {"TC<5": {"No": 1, "Yes": 1},
                            "TC>=5": {"No": 1, "Yes": 2}},
                "SBP140-159": {"TC<5": {"No": 1, "Yes": 2},
                               "TC>=5": {"No": 1, "Yes": 3}},
                "SBP>=160": {"TC<5": {"No": 1, "Yes": 2},
                             "TC>=5": {"No": 2, "Yes": 4}}}},
    40: {"M": {"SBP<140": {"TC<5": {"No": 2, "Yes": 4},
                          "TC>=5": {"No": 3, "Yes": 6}},
               "SBP140-159": {"TC<5": {"No": 3, "Yes": 6},
                              "TC>=5": {"No": 5, "Yes": 8}},
               "SBP>=160": {"TC<5": {"No": 4, "Yes": 7},
                            "TC>=5": {"No": 6, "Yes": 10}}},
          "F": {"SBP<140": {"TC<5": {"No": 1, "Yes": 2},
                            "TC>=5": {"No": 2, "Yes": 4}},
                "SBP140-159": {"TC<5": {"No": 2, "Yes": 4},
                               "TC>=5": {"No": 3, "Yes": 6}},
                "SBP>=160": {"TC<5": {"No": 3, "Yes": 5},
                             "TC>=5": {"No": 4, "Yes": 8}}}},
    50: {"M": {"SBP<140": {"TC<5": {"No": 5, "Yes": 9},
                          "TC>=5": {"No": 7, "Yes": 12}},
               "SBP140-159": {"TC<5": {"No": 7, "Yes": 12},
                              "TC>=5": {"No": 10, "Yes": 16}},
               "SBP>=160": {"TC<5": {"No": 9, "Yes": 14},
                            "TC>=5": {"No": 13, "Yes": 20}}},
          "F": {"SBP<140": {"TC<5": {"No": 3, "Yes": 5},
                            "TC>=5": {"No": 4, "Yes": 7}},
                "SBP140-159": {"TC<5": {"No": 4, "Yes": 7},
                               "TC>=5": {"No": 6, "Yes": 10}},
                "SBP>=160": {"TC<5": {"No": 6, "Yes": 9},
                             "TC>=5": {"No": 8, "Yes": 13}}}},
    60: {"M": {"SBP<140": {"TC<5": {"No": 8, "Yes": 14},
                          "TC>=5": {"No": 12, "Yes": 19}},
               "SBP140-159": {"TC<5": {"No": 12, "Yes": 19},
                              "TC>=5": {"No": 16, "Yes": 24}},
               "SBP>=160": {"TC<5": {"No": 15, "Yes": 22},
                            "TC>=5": {"No": 20, "Yes": 28}}},
          "F": {"SBP<140": {"TC<5": {"No": 5, "Yes": 9},
                            "TC>=5": {"No": 7, "Yes": 11}},
                "SBP140-159": {"TC<5": {"No": 7, "Yes": 11},
                               "TC>=5": {"No": 10, "Yes": 15}},
                "SBP>=160": {"TC<5": {"No": 10, "Yes": 14},
                             "TC>=5": {"No": 13, "Yes": 19}}}},
    70: {"M": {"SBP<140": {"TC<5": {"No": 14, "Yes": 21},
                          "TC>=5": {"No": 19, "Yes": 27}},
               "SBP140-159": {"TC<5": {"No": 19, "Yes": 27},
                              "TC>=5": {"No": 24, "Yes": 32}},
               "SBP>=160": {"TC<5": {"No": 23, "Yes": 31},
                            "TC>=5": {"No": 28, "Yes": 36}}},
          "F": {"SBP<140": {"TC<5": {"No": 9, "Yes": 14},
                            "TC>=5": {"No": 12, "Yes": 18}},
                "SBP140-159": {"TC<5": {"No": 12, "Yes": 18},
                               "TC>=5": {"No": 16, "Yes": 23}},
                "SBP>=160": {"TC<5": {"No": 16, "Yes": 22},
                             "TC>=5": {"No": 20, "Yes": 27}}}}
}

def classify_sbp(sbp: int) -> str:
    if sbp < 140:
        return "SBP<140"
    elif sbp < 160:
        return "SBP140-159"
    else:
        return "SBP>=160"

def classify_tc(tc: float) -> str:
    return "TC<5" if tc < 5 else "TC>=5"

@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return HTMLResponse("""
<html>
<head><title>CVD Risk Check</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;margin:40px;} label{display:block;margin:8px 0}</style>
</head>
<body>
<h2>10-летний риск ССЗ (WHO/ISH)</h2>
<form action="/calc" method="post">
  <label>Возраст:
    <select name="age">
      <option value="30">30-39</option>
      <option value="40">40-49</option>
      <option value="50">50-59</option>
      <option value="60">60-69</option>
      <option value="70">70-79</option>
    </select>
  </label>
  <label>Пол:
    <select name="sex"><option value="M">Мужчина</option><option value="F">Женщина</option></select>
  </label>
  <label>Систолическое давление (мм рт. ст.):
    <select name="sbp"><option value="120">до 139</option><option value="150">140-159</option><option value="170">160 и выше</option></select>
  </label>
  <label>Холестерин общий (ммоль/л):
    <select name="tc"><option value="4.5">< 5</option><option value="5.5">≥ 5</option></select>
  </label>
  <label>Курите?
    <select name="smoke"><option value="No">Нет</option><option value="Yes">Да</option></select>
  </label>
  <button type="submit">Рассчитать</button>
</form>
</body></html>
""")

@app.post("/calc", response_class=HTMLResponse)
def calc(age: int = Form(...),
         sex: str = Form(...),
         sbp: int = Form(...),
         tc: float = Form(...),
         smoke: str = Form(...)):
    risk = RISK[age][sex][classify_sbp(sbp)][classify_tc(tc)][smoke]
    advice = []
    if smoke == "Yes":
        advice.append("Отказ от курения снижает риск на 30-50 %.")
    if sbp >= 140:
        advice.append("Снижение давления на 10 мм рт. ст. уменьшает риск на 20 %.")
    if tc >= 5:
        advice.append("Снижение холестерина на 1 ммоль/л снижает риск на ~25 %.")
    return HTMLResponse(f"""
<html><head><title>Результат</title><style>body{{font-family:Arial;margin:40px}}</style></head>
<body>
<h2>Ваш 10-летний риск ССЗ: <span style="color:red">{risk}%</span></h2>
<p>{"<br>".join(advice)}</p>
<a href="/">← Назад</a>
</body></html>
""")