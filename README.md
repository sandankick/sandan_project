# 한국산업단지 ESG 대응

이 파일은 plotly에서 개발한 python 대화형 프레임워크인 dash을 사용해 작성되었습니다. [Plotly](https://plot.ly/).

## Getting Started

### 파일구조

```
apps

├── ...

├── 산단발차기 # app project
│ ├── .gitignore # Backup File, Log File
│ ├── .csv(산단별 데이터 csv파일)
│ ├── .geojson(산단 위치정보 geojson파일)
│ ├── assets
│ │ ├── dash-logo.png
│ │ ├── s1.css
│ │ ├── resizing_script.js
│ │ ├── styles.css
│ ├── app.py or app.ipynb

```


Run the app

```

python app.py

```

## About the app

This Dash app displays oil production in western New York. There are filters at the top of the app to update the graphs below. By selecting or hovering over data in one plot will update the other plots ('cross-filtering').

## Built With

- [Dash](https://dash.plot.ly/) - Main server and interactive components
- [Plotly Python](https://plot.ly/python/) - Used to create the interactive plots

## Screenshots

The following are screenshots for the app in this repo:


