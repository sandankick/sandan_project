# ESG 선제지원 추천 웹사이트

이 파일은 plotly에서 개발한 python 대화형 프레임워크인 dash을 사용해 작성되었습니다. [Plotly](https://plot.ly/).

## 파일설명 

산업단지내 기업의 매출액, 기업규모, 종사자수 등의 정보가 들어있는 csv파일을 분석, 시각화하여 웹 사이트상에 구현하는 코드입니다.

## 파일 실행

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

### 파일 실행방법 

- app.ipynb or app.py코드 실행


1. jupyter notebook과 같은 어플리케이션을 활용하여 app.ipynb실행

2. app.ipynb 코드를 실행시키기 어려울경우 app.py파일을 실행하기 위해 console창에 다음 명령어 입력

```
python app.py

py코드 실행시 다음과 같은 라이브러리가 준비되어야함 

라이브러리(pip install)
dash==2.6.1
plotly==5.10.0
numpy==1.20.3
install pandas==1.3.4
install seaborn
```

3. 다음코드를 실행시킬시 로컬상에서 웹사이트가 실행되며 http://127.0.0.1:8050/ 주소로 들어가서 웹 구현을 확인할수 있음


## 배포

다음 코드는 웹사이트 상에 배포되어 있어 [웹 사이트 바로가기](goodmoni-parksangje.pythonanywhere.com). 다음과 같은 링크에서 확인할 수 있습니다.

## 빌드

- [Dash](https://dash.plot.ly/) - Main server and interactive components
- [Plotly Python](https://plot.ly/python/) - Used to create the interactive plots


## 스크린샷
![KakaoTalk_20220902_160756362](https://user-images.githubusercontent.com/103256030/188083988-0cdbf2c4-1944-4e07-8551-df751d57c5a7.png)



