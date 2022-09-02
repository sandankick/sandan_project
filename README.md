# 한국산업단지 ESG 대응

이 파일은 plotly에서 개발한 python 대화형 프레임워크인 dash을 사용해 작성되었습니다. [Plotly](https://plot.ly/).

## Getting Started

### Running the app locally

First create a virtual environment with conda or venv inside a temp folder, then activate it.

```
virtualenv venv

# Windows
venv\Scripts\activate
# Or Linux
source venv/bin/activate

```

Clone the git repo, then install the requirements with pip

```

git clone https://github.com/plotly/dash-sample-apps
cd dash-sample-apps/apps/dash-oil-and-gas
pip install -r requirements.txt

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

![animated1](screenshots/animated1.gif)

![screenshot](screenshots/screenshot1.png)

![screenshot](screenshots/screenshot2.png)

![screenshot](screenshots/screenshot3.png)

