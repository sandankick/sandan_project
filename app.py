
#필요 라이브러리
import dash
import dash_table
from dash import Dash, html, dcc, Input, Output, ClientsideFunction, State, ctx

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import math
import numpy as np
import pandas as pd
import json

import seaborn as sns

import dash_bootstrap_components as dbc
#-----------------------------------------------------------------------------------------------------------------------
#데이터 파일 가져오기
#-----------------------------------------------------------------------------------------------------------------------

#산업단지 ESG 관련 데이터 파일
df = pd.read_csv('Final_Data7.csv', encoding='cp949')
#산업단지 위치정보 파일
geo_data_sandan = json.load(open('산단.geojson', encoding='utf-8'))

#-----------------------------------------------------------------------------------------------------------------------
#대시보드 작성 시 필요데이터 생성
#-----------------------------------------------------------------------------------------------------------------------

#등급에 따른 산업단지 색깔 지정
colors_map = ['#fe6161', '#fe9d61', '#feeb61', '#cffe61', '#97fbf4', '#97d1fb', '#a4a5fe', '#dbdbdb']

# 산업분류 리스트 만들기
industry_list = df['대분류'].unique()

#산업단지 geojson 파일에서 산업단지 위경도 좌표 가져오기
sandan_names=[]
sandan_lats=[]
sandan_lons=[]
for sandan in geo_data_sandan.get('features'):
    sandan_names.append(sandan.get('properties')['name'])
    sandan_lats.append(sandan.get('geometry')['coordinates'][0][0][1])
    sandan_lons.append(sandan.get('geometry')['coordinates'][0][0][0])
df_sandan_location = pd.DataFrame({'name':sandan_names,'latitude':sandan_lats, 'longitude':sandan_lons})

#시급성 기준으로 산업단지를 데이터프레임을 5등분해 순차적으로 등급 지정
df_grade = df[['산업단지', 'Score']].groupby('산업단지').sum()
df_grade = pd.DataFrame({'산업단지': list(df_grade.index), 'Score':df_grade['Score']})
df_grade = df_grade.sort_values(by=['Score'], axis=0, ascending=False)

df_grade1_sandan = df_grade[0 : round(len(df_grade)*0.2)]
df_grade2_sandan = df_grade[round(len(df_grade)*0.2) : round(len(df_grade)*0.4)]
df_grade3_sandan = df_grade[round(len(df_grade)*0.4) : round(len(df_grade)*0.6)]
df_grade4_sandan = df_grade[round(len(df_grade)*0.6) : round(len(df_grade)*0.8)]
df_grade5_sandan = df_grade[round(len(df_grade)*0.8) : round(len(df_grade))]

pd.set_option('mode.chained_assignment',  None)
df_grade1_sandan['산단등급'] = 1
df_grade2_sandan['산단등급'] = 2
df_grade3_sandan['산단등급'] = 3
df_grade4_sandan['산단등급'] = 4
df_grade5_sandan['산단등급'] = 5

df_grade_sandan = pd.concat([df_grade1_sandan, df_grade2_sandan, df_grade3_sandan, df_grade4_sandan, df_grade5_sandan])

#산단별 기업등급 데이터 프레임에 위경도 정보 결합
df_grade_sandan['marker_size'] = 1 / (df_grade_sandan['산단등급']**2)
df_grade_sandan = df_grade_sandan.reset_index(drop=True)

df_sandan_loc = pd.merge(df_grade_sandan, df_sandan_location, how='left', left_on='산업단지', right_on='name')

#영업이익 증가율 칼럼 만들기
df['영업이익증가율_2021'] = df['영업이익_2021'] / df['영업이익_2020'] -1 
df['영업이익증가율_2020'] = df['영업이익_2020'] / df['영업이익_2019'] -1
df['영업이익증가율_2019'] = df['영업이익_2019'] / df['영업이익_2018'] -1
 
df['평균영업이익증가율'] = (df['영업이익증가율_2021'] + df['영업이익증가율_2020'] + df['영업이익증가율_2019']) / 3
#-----------------------------------------------------------------------------------------------------------------------
#데이터 분류 함수
#-----------------------------------------------------------------------------------------------------------------------

 
def SandanSearch_df(df, search):
    '''
    Description :
    데이터 프레임과 문자열을 input값으로 받아, 
    해당 문자열이 포함된 산업단지와 검색 성공 유무를 반환 
    
    Parameters :
    df = 분류할 데이터프레임. '산업단지'칼럼을 포함
    return :
    검색문자열을 포함하는 데이터프레임 행과 검색 성공 유무를 booltype으로 반환
    '''

    #결측치 제거
    df_drop = df.dropna(subset=['산업단지'])
    
    #데이터 행 검색, 검색된 데이터가 있을 경우에만 데이터 변경
    is_search = False
    if (search == None) | (search == ""):
        search_sandan = df_drop['산업단지'].str.contains("")
        is_search = False
    else:
        search_sandan = df_drop['산업단지'].str.contains(search)
        if search_sandan.sum() > 0:
            df_drop = df_drop[search_sandan]
            is_search = True
    
    #검색된 데이터가 없을 경우 산업단지명으로 "" 반환
    if is_search:
        return_str = df_drop['산업단지'].values[0]
    else:
        return_str = ""
    return return_str, is_search



def Sandan_df(df, sandan_name):
    '''
    Description :
    데이터 프레임과 산업단지명 문자열을 input값으로 받아,
    해당 산업단지에 속하는 데이터프레임 행을 반환
    
    Parameters :
    df = 분류할 데이터프레임. '산업단지'칼럼을 포함
    return :
    산업단지 칼럼이 산업단지명 문자열과 일치하는 데이터프레임 행을 반환
    '''
    
    #데이터 결측치 제거
    df_drop = df.dropna(subset=['산업단지'])
    
    #데이터 행 선택 조건식
    if sandan_name != "":
        df_condition = df_drop[(df_drop['산업단지']==sandan_name)]
    else:
        df_condition = df_drop
    
    df_return = df_condition
    return df_return
                   
                   

def CompanySize_df(df, company_size):
    '''
    Description :
    데이터 프레임과 기업규모(대기업, 중견기업, 중소기업)문자열을 input값으로 받아, 
    해당 기업규모에 포함되는 데이터프레임 행을 반환
    
    Parameters :
    df = 분류할 데이터프레임. '기업규모'칼럼을 포함
    return :
    해당 기업 규모에 포함되는 데이터프레임 행을 반환
    '''


    #기업규모 결측치 제거
    size_types = ['중기업', '소기업', '소상공인', '대기업', '중견기업', '보호대상중견기업', '한시성중소기업', '중소기업']
    df = df[df['기업규모'].isin(size_types)]
    
    if (company_size == None) | (company_size == '전체'):
        return df
    
    if company_size == '대기업':
        df = df[df['기업규모'].isin(['대기업'])]
    elif company_size == '중견기업':
        df = df[df['기업규모'].isin(['중기업', '중견기업', '보호대상중견기업'])]
    elif company_size == '중소기업':
        df = df[df['기업규모'].isin(['소기업', '소상공인', '한시성중소기업','중소기업'])]
    else:
        print("type_error")
    
    return df



def ExportEU_df(df, country):
    '''
    Description :
    데이터 프레임과 eu수출여부를 input값으로 받아,
    해당 수출여부에 속하는 데이터프레임 행을 반환
    
    Parameters :
    df = 분류할 데이터프레임. '수출 여부 (EU)'칼럼을 포함
    return :
    수출 여부가 '유'일때 수출 여부 항목이 유인 데이터프레임 행을 반환하고 아닐 때는 입력 데이터프레임을 그대로 반환
    '''

    return_df = df

    if 'EU' in country:
        return_df = df[df['수출 여부 (EU)']=='유']

        if 'US' in country:
            return_df = df[(df['수출 여부 (EU)']=='유') & (df['수출 여부 (US)']=='유')]

    elif 'US' in country:
        return_df = df[df['수출 여부 (US)']=='유']

    else:
        return_df = df
        
    return return_df

#-----------------------------------------------------------------------------------------------------------------------
#대시보드 작성 함수 
#-----------------------------------------------------------------------------------------------------------------------


def sales_pie(df):
    '''
    Description :
    데이터 프레임을 input값으로 받아,
    전국 산업단지별 수출액 비율 그래프 생성
    
    Parameters :
    df = 분류할 데이터프레임. ['산업단지','대분류','매출액_2016','매출액_2017',
    '매출액_2018','매출액_2019','매출액_2020','매출액_2021']칼럼을 포함
    return :
    전국 산업단지별 수출액 비율을 나타낸 Plotly Express의 pie chart를 반환 
    '''

    #산업단지별 수출액(매출액)합 분류
    df_temp=df[['산업단지','대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp=df_temp.groupby(['산업단지','대분류']).sum().reset_index()

    dff_pie=df_temp.drop(['대분류'],axis=1).groupby(['산업단지']).sum()
    dff_pie=dff_pie.sort_values(by=['매출액_2021'],ascending=False)[:8]

    title_text="전국"
    colors=colors_map
    fig = px.pie(dff_pie, names=dff_pie.index,
                 values='매출액_2021', hole=0.3, color_discrete_sequence=colors)
    fig.update_layout(
        title=dict(
        text='%s 산업단지별 수출액 비율' % title_text,
        x=0.02,
        y=0.98,
        font_size=40,),
        font=dict(
            family="Arial",
            size=30,
            color="#777777"
            ),
        legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=0.98,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0.02)',
                    font=dict(
                    family="Courier",
                    size=20
                    ),
                ),
        margin=dict(l=10, r=10, t=180, b=5),
        paper_bgcolor='#F9F9F9',
        plot_bgcolor='#F9F9F9')
    return fig



def sales_pie_sandan(df_sandan):
    '''
    Description :
    데이터 프레임을 input값으로 받아,
    산업단지내 업종별 수출액 비율 그래프를 생성
    
    Parameters :
    df = 분류할 데이터프레임. ['산업단지','대분류','매출액_2016','매출액_2017',
    '매출액_2018','매출액_2019','매출액_2020','매출액_2021']칼럼을 포함
    return :
    산업단지내 업종 별 수출액 비율을 나타낸 Plotly Express의 pie chart를 반환 
    '''

    df_temp=df_sandan[['산업단지','대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp=df_temp.groupby(['산업단지','대분류']).sum().reset_index()

    dff_pie=df_sandan.drop(['산업단지'],axis=1).groupby(['대분류']).sum()
    dff_pie=dff_pie.sort_values(by=['매출액_2021'],ascending=False)[:8]

    title_text=df_sandan['산업단지'].values[0]
    fig = px.pie(dff_pie, names=dff_pie.index,
                 values='매출액_2021', hole=0.4, color_discrete_sequence=colors_map)
    fig.update_layout(
    title=dict(
    text='%s 분야별 수출액 비율' % title_text,
    x=0.02,
    y=0.98,
    font_size=40,),
    font=dict(
        family="Arial",
        size=30,
        color="#777777"
        ),
    legend=dict(
                orientation="h",
                yanchor="bottom",
                y=0.75,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.02)',
                font=dict(
                family="Courier",
                size=20,
                ),
            ),
    margin=dict(l=10, r=10, t=150, b=5),
    paper_bgcolor='#F9F9F9',
    plot_bgcolor='#F9F9F9')
    return fig


def entire_EDA(input_df, grade):

    '''
    Description :
    데이터 프레임과 등급을 input값으로 받아,
    산업단지 매출액, 기업 수 그래프를 생성하고 산업단지 추천결과(문자열)과 함께 반환
    ex)input: (df,1)일 때 return: fig, "등급 산업단지는 창원산업단지 외 8건 입니다."
    
    Parameters :
    df = 분류할 데이터프레임. ['산업단지', '매출액_2021', 'Score']칼럼을 포함 
    grade 1~5범위 내의 정수값 
    return :
    Plotly Express의 make_subplots(산업단지 매출액, 기업 수 그래프), 산업단지 추천결과(문자열) 반환 
    '''

    #데이터 프레임 내 기업수
    dict_companies_num=dict(input_df['산업단지'].value_counts())

    #산업단지 별 시급성, 매출액합을 그룹화
    df_gradegroup = input_df[['산업단지','Score']].groupby(['산업단지'])['Score'].sum().reset_index()
    df_salesgroup = input_df[['산업단지', '매출액_2021']].groupby(['산업단지'])['매출액_2021'].sum().reset_index()
    df_grade = pd.merge(df_gradegroup, df_salesgroup, how ='left', on ='산업단지')

    df_grade = df_grade.sort_values(by=['Score'], axis=0, ascending=True)

    #등급에 맞는 산업단지 선택(1등급 상위20퍼, 2등급 상위20~40퍼, 3등급 상위40~60퍼, 3등급 상위60~80퍼, 3등급 상위80~100퍼)
    if(grade == 1):
        df_grade_choose=df_grade[-round(len(df_grade)*0.2):]
        color = colors_map[0]
    elif(grade == 2):
        df_grade_choose=df_grade[-round(len(df_grade)*0.4):-round(len(df_grade)*0.2)]
        color = colors_map[1]
    elif(grade == 3):
        df_grade_choose=df_grade[-round(len(df_grade)*0.6):-round(len(df_grade)*0.4)]
        color = colors_map[2]
    elif(grade == 4):
        df_grade_choose=df_grade[-round(len(df_grade)*0.8):-round(len(df_grade)*0.6)]
        color = colors_map[3]
    elif(grade == 5):
        df_grade_choose=df_grade[:-round(len(df_grade)*0.8)]
        color = colors_map[4]
    else:
        df_grade_choose=df_grade
        color = 'rgba(17, 157, 255, 0.6)'
    df_grade_choose = df_grade_choose.sort_values(by=['Score'], axis=0, ascending=True)

    #각 산업단지 별로 존재하는 기업갯수 정리
    list_companies_num=[]
    for sandan in df_grade_choose['산업단지']:
        list_companies_num.append(dict_companies_num[sandan])
    
    y_saving =df_grade_choose.매출액_2021
    y_net_worth =list_companies_num
    x =df_grade_choose.산업단지

    #산업단지 추천결과 문자열
    grade_text = '등급 산업단지는 {}외 {}건 입니다'.format(x.values[-1], len(df_grade_choose)-1)
    
    #서브플롯 2개생성(산업단지별 매출액 bar그래프, 산업단지별 기업갯수 그래프)
    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True,
                        shared_yaxes=False, vertical_spacing=0.005)

    fig.append_trace(go.Bar(
        x=y_saving,
        y=x,
        marker=dict(
            color=color,
            line=dict(
                color=color,
                width=1
            ),
        ),
        name='단지별 매출액 (단위 : $)',
        orientation='h',
    ), 1, 1)

    fig.append_trace(go.Scatter(
            x=y_net_worth, y=x,
            mode='lines+markers',
            line_color='rgba(217, 95, 2,0.6)',
            name='단지별 기업 수 (단위 : 개)',
            textposition='top left'
        ), 1, 2)

    fig.update_layout(
        font=dict(
        family="Arial",
        size=25),
        title=dict(
        text='전국 산업단지 매출액  &  기업 수',
        x=0.02,
        y=0.98,
        font=dict(
            family="Arial",
            size=40,
            color="#777777"
            )
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.93],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            showticklabels=False,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0, 0.93],
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 0.42],
       ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.47, 1],
            side='top',
            range=[0,max(y_net_worth)+5]
            
        ),
        legend=dict(xanchor="right", yanchor="bottom",y=0.01, font_size=20),
        margin=dict(l=10, r=0, t=30, b=5),
        paper_bgcolor='#F9F9F9',
        plot_bgcolor='#F9F9F9'
    )

    #그래프 라벨 
    annotations = []

    y_s = np.round(y_saving, decimals=2)
    y_nw = np.rint(y_net_worth)

    #매출액 기업수 라벨 지정, 전체 등급 그래프일 때는 라벨이 표시되면 너무 난잡해보이므로 제외
    if(grade != "전체"):
        for ydn, yd, xd in zip(y_nw, y_s, x):
            annotations.append(dict(xref='x2', yref='y2',
                                    y=xd, x=ydn,
                                    text= str(int(ydn)) + '개',
                                    font=dict(family='Arial', size=12, color='rgb(99, 110, 210)',),
                                    showarrow=False))
            
            annotations.append(dict(xref='x1', yref='y1',
                                    y=xd, x=yd,
                                    text='{:,}'.format(yd) + '$',
                                    font=dict(family='Arial', size=12, color='rgb(99, 110, 210)'),
                                    showarrow=False))

    fig.update_layout(annotations=annotations)
    
    return fig, grade_text


#전국 산업단지 그래프 상대분석
def Main_graph(input_df):
    '''
    Description :
    데이터 프레임을 input값으로 받아,
    전국 산업단지 상대분석 그래프를 반환

    Parameters :  
    input_df = 분류할 데이터프레임. ['산업단지', '매출액_2021', '매출액_2020','매출액_2019',
     '종사자수_2021', '종사자수_2020','종사자수_2019','평균영업이익증가율','Score']칼럼을 포함 
    return : 
    Plotly Express의 make_subplots(산업단지 매출액, 기업 수 그래프)
    '''

    #데이터 프레임 내 기업수
    dict_companies_num=dict(input_df['산업단지'].value_counts())

    #산업단지 별 시급성, 매출액합을 그룹화 
    df_gradegroup = input_df[['산업단지','Score']].groupby(['산업단지'])['Score'].sum().reset_index()
    df_salesgroup = input_df[['산업단지','매출액_2019','매출액_2020', '매출액_2021']].groupby(['산업단지'])['매출액_2019','매출액_2020','매출액_2021'].sum().reset_index()
    df_employeegroup = input_df[['산업단지','종사자수_2019','종사자수_2020', '종사자수_2021']].groupby(['산업단지'])['종사자수_2019','종사자수_2020', '종사자수_2021'].sum().reset_index()
    
    df_grade = pd.merge(df_gradegroup, df_salesgroup, how ='left', on ='산업단지')
    df_grade = pd.merge(df_grade, df_employeegroup, how ='left', on ='산업단지')
    
    df_grade = df_grade.sort_values(by=['Score'], axis=0, ascending=True)
    
    #각 산업단지 별로 존재하는 기업갯수 정리
    list_companies_num=[]
    for sandan in df_grade['산업단지']:
        list_companies_num.append(dict_companies_num[sandan])
    
    #상대분석을 위한 로그함수 적용
    y_money=np.log2((df_grade['매출액_2021'] + df_grade['매출액_2020'] + df_grade['매출액_2019']) / 3 ) / 2
    y_employ=np.log2((df_grade['종사자수_2021'] + df_grade['종사자수_2020'] + df_grade['종사자수_2019']) / 3 ) / 2
    y_score =np.log2(df_grade['Score'])
    y_company =np.log2(list_companies_num)
    x =df_grade.산업단지

    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True,
                        shared_yaxes=True, vertical_spacing=0.005)
    
    
    #산업단지 등급별 색상 지정
    axis_length=y_score.shape[0]
    num=int(axis_length/5)
    temp_color=np.array(['rgb(255,255,255)']*axis_length)
    temp_color[:num]=colors_map[4]
    temp_color[num:num*2]=colors_map[3]
    temp_color[num*2:num*3]=colors_map[2]
    temp_color[num*3:num*4]=colors_map[1]
    temp_color[num*4:]=colors_map[0]
    
    fig.append_trace(go.Bar(
        x=y_score,
        y=x,
        marker=dict(
            color=temp_color,
            line=dict(
                color='rgba(50, 171, 96, 1.0)',
                width=1),
        ),
        name='단지별 시급성 (log 분석)',
        orientation='h',
    ), 1, 1)

    fig.append_trace(go.Scatter(
        x=y_company, y=x,
        mode='lines+markers',
        line_color='rgb(128, 0, 128)',
        name='단지별 기업 수 (log 분석)',
    ), 1, 2)

    fig.append_trace(go.Scatter(
        x=y_employ, y=x,
        mode='lines+markers',
        line_color='rgb(0, 0, 128)',
        name='단지별 종사자 수 (log 분석)',
    ), 1, 2)
    
    
    fig.append_trace(go.Bar(
    x=y_money,
    y=x,
    marker=dict(
        color='rgba(50, 171, 96, 0.6)',
        line=dict(
            color='rgba(50, 171, 96, 1.0)',
            width=1),
    ),
    name='단지별 수출액 (log 분석)',
    orientation='h',
    ), 1, 2)

    fig.update_layout(
        font=dict(
            family="Arial",
            size=18,
            color="#777777"),
        title=dict(
        text='전국 산업단지 시급도,수출액,기업수 상대분석',
        x=0.05,
        y=0.98,
        font=dict(
            family="Arial",
            size=40,
            color="#777777"
            )
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 1],
            tickmode='linear'
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            showticklabels=False,
            linecolor='rgba(102, 102, 102, 0.8)',
            domain=[0, 1],
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0, 0.55],
            range=[0,15]
        ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.58, 1],
            range=[0,20],
            side='bottom',
            dtick=5,
        ),
        legend=dict(xanchor="right", yanchor="bottom",y=0.01, font_size=20),
        margin=dict(l=5, r=5, t=33, b=1),
        paper_bgcolor='#F9F9F9',
        plot_bgcolor='#F9F9F9'
    )

    #그래프 라벨
    annotations = []

    y_s = np.round(y_score)
    y_nw = np.rint(y_company)

    #매출액, 기업수 라벨 입력
    for ydn, yd, xd in zip(y_nw, y_s, x):
        annotations.append(dict(xref='x2', yref='y2',
                                y=xd, x=ydn - 20000,
                                text='{:,}'.format(ydn),
                                font=dict(family='Arial', size=12,
                                          color='rgb(128, 0, 128)'),
                                showarrow=False))
        annotations.append(dict(xref='x1', yref='y1',
                                y=xd, x=yd + 3,
                                text=str(yd),
                                font=dict(family='Arial', size=1,
                                          color='rgb(50, 171, 96)'),
                                showarrow=False))

    fig.update_layout(annotations=annotations)
    return fig

def Main_map(input_df):
    '''
    Description :
    데이터 프레임을 input값으로 받아,
    전국 산업단지 시급도, 수출액, 기업수 상대분석 그래프 생성

    Parameters :  
    input_df = 분류할 데이터프레임. ['산업단지', '매출액_2021', '매출액_2020','매출액_2019','Score']칼럼을 포함 
    return : 
    Plotly Express의 scatter_mapbox(전국산업단지 시급도 분포도)
    '''


    #산업단지를 시급성 기준으로 정렬 후 5등분하여 1~5등급으로 등급 분류
    df_grade = input_df[['산업단지', 'Score']].groupby('산업단지').sum()
    df_grade = pd.DataFrame({'산업단지': list(df_grade.index), 'Score':df_grade['Score']})
    df_grade = df_grade.sort_values(by=['Score'], axis=0, ascending=False)

    df_grade1_sandan = df_grade[0 : round(len(df_grade)*0.2)]
    df_grade2_sandan = df_grade[round(len(df_grade)*0.2) : round(len(df_grade)*0.4)]
    df_grade3_sandan = df_grade[round(len(df_grade)*0.4) : round(len(df_grade)*0.6)]
    df_grade4_sandan = df_grade[round(len(df_grade)*0.6) : round(len(df_grade)*0.8)]
    df_grade5_sandan = df_grade[round(len(df_grade)*0.8) : round(len(df_grade))]

    pd.set_option('mode.chained_assignment',  None)
    df_grade1_sandan['산단등급'] = 1
    df_grade2_sandan['산단등급'] = 2
    df_grade3_sandan['산단등급'] = 3
    df_grade4_sandan['산단등급'] = 4
    df_grade5_sandan['산단등급'] = 5

    df_grade_sandan = pd.concat([df_grade1_sandan, df_grade2_sandan, df_grade3_sandan, df_grade4_sandan, df_grade5_sandan])

    #산단별 기업등급 데이터 프레임에 위경도 정보 결합
    df_grade_sandan['marker_size'] = 1 / (df_grade_sandan['산단등급']**2)
    df_grade_sandan = df_grade_sandan.reset_index(drop=True)

    df_sandan_loc = pd.merge(df_grade_sandan, df_sandan_location, how='left', left_on='산업단지', right_on='name')
    
    lat = 36.065
    lon = 127.686
    zoom_size = 5.7

   
    fig_sandan = px.scatter_mapbox(df_sandan_loc,
                            mapbox_style='carto-positron',
                            lat="latitude", lon="longitude",
                            zoom=zoom_size, center = {"lat": lat, "lon": lon},
                            color='산단등급',
                            size = 'marker_size',
                            size_max=50,
                            opacity=0.3,
                            )

    fig_sandan.update_layout(
                            legend=dict(
                                orientation='h'
                                ),
                            title=dict(
                                text='< 시급성 분포 Map >',
                                x=0.2,
                                y=0.08,
                                font_size=30
                                ),
                            font=dict(
                                family="Arial",
                                size=15,
                                color="#777777"
                                ),
                            margin={"r":0,"t":20,"l":0,"b":120},
                            paper_bgcolor='#F9F9F9',
                            plot_bgcolor='#F9F9F9',
                                )
    return fig_sandan


def ChangeInExport_industry(df, sandan_name):
    '''
    Description :
    데이터 프레임과 함께 산단이름을 입력받아, 
    특정 산업단지 내 수출액 변화 추이 그래프 생성

    Parameters :  
    input_df = 분류할 데이터프레임. ['산업단지','대분류','매출액_2016','매출액_2017','매출액_2018',
    '매출액_2019','매출액_2020','매출액_2021']칼럼을 포함 
    return : 
    graph_objects의 Figure()객체(수출액 변화 추이 그래프)
    '''

    df_temp_sandan=df[['산업단지','대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp_sandan=df_temp_sandan.groupby(['산업단지','대분류']).sum().reset_index()

    #수출액(매출액)합을 기준으로 상위 5개 업종을 분류
    dff_bar = df_temp_sandan[df_temp_sandan['산업단지'] == sandan_name]
    dff_bar=dff_bar.sort_values(by=['매출액_2021'],ascending=False)
    dff_bar=dff_bar.head()
    text = dff_bar.iloc[0,1]

    industry_list=[]
    value_list=[]

    #수출액과 매출액 
    for i in range(len(dff_bar)):
        industry_list.append(dff_bar.iloc[i,:][1])
        value_list.append(list(dff_bar.iloc[i,:][2:]))

    fig_temp=go.Figure()

    #상위 수출액(매출액) 5개 산업단지의 2016~2021년의 수출액 변화 추이 그래프 생성
    for i in range(5):
        fig_temp.add_trace(go.Scatter(x=[2016,2017,2018,2019,2020,2021], y=value_list[i], name=industry_list[i], mode='lines+markers',
                line=dict(color=colors_map[i], width=2))) # Line에 옵션 선택
    fig_temp.update_layout(
            title=dict(
            text='%s 분야별 수출액 변화추이' % sandan_name,
            x=0.02,
            y=0.98,
            font_size=40),
            font=dict(
                family="Arial",
                size=30,
                color="#777777"
                ),
            legend=dict(xanchor="right", yanchor="bottom",x = 0.7,y=0.7, font_size=20,bgcolor='rgba(0,0,0,0.01)'),
            margin=dict(l=10, r=10, t=60, b=5),
            paper_bgcolor='#F9F9F9',
            plot_bgcolor='#F9F9F9',
            xaxis=dict(
                    title="연도별",
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    showgrid=True,
                    dtick=1),
            yaxis=dict(
                    title="매출액 (단위:$)",
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    showgrid=True),
            hovermode="x unified"
            )
    return fig_temp, text

def ChangeInExport_sandan(df):
    '''
    Description :
    데이터 프레임과 input값으로, 
    산업단지 별 수출액 변화추이 그래프 생성

    Parameters :  
    input_df = 분류할 데이터프레임. ['산업단지','대분류','매출액_2016','매출액_2017','매출액_2018',
    '매출액_2019','매출액_2020','매출액_2021']칼럼을 포함 
    return : 
    graph_objects의 Figure()객체(수출액 변화 추이 그래프)
    '''

    df_sandan_sales = df[['산업단지','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_sandan_sales = df_sandan_sales.groupby(['산업단지']).sum().reset_index()
     #수출액(매출액)합을 기준으로 상위 5개 산업단지를 분류
    df_sandan_sales = df_sandan_sales.sort_values(by=['매출액_2021'],ascending=False)[:5]
    
    industry_list=[]
    value_list=[]

    for i in range(len(df_sandan_sales)):
        industry_list.append(df_sandan_sales.iloc[i,:][0])
        value_list.append(list(df_sandan_sales.iloc[i,:][1:]))
    
    fig_temp=go.Figure()
    #상위 수출액(매출액) 5개 업종의 2016~2021년의 수출액 변화 추이 그래프 생성
    for i in range(5):
        fig_temp.add_trace(go.Scatter(x=[2016,2017,2018,2019,2020,2021], y=value_list[i], name=industry_list[i], mode='lines+markers',
                line=dict(color=colors_map[i], width=2))) 

    fig_temp.update_layout(
            title=dict(
            text='%s 산업단지별 수출액 변화추이' % '전국',
            x=0.02,
            y=0.98,
            font_size=40),
            font=dict(
                family="Arial",
                size=20,
                color="#777777"
                ),
            legend=dict(xanchor="right", yanchor="bottom",x = 0.7, y=0.7, font_size=20,bgcolor='rgba(0,0,0,0.01)'),
            margin=dict(l=10, r=10, t=60, b=5),
            paper_bgcolor='#F9F9F9',
            plot_bgcolor='#F9F9F9',
            xaxis=dict(
                    title="연도별",
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    showgrid=True,
                    dtick=1),
            yaxis=dict(
                    title="매출액 (단위:$)",
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    showgrid=True),
            hovermode="x unified"
            )
    
    return fig_temp
#-----------------------------------------------------------------------------------------------------------------------
#dash server지정 
#-----------------------------------------------------------------------------------------------------------------------
from dash_html_components import Br
import flask
from flask import Flask

# from flask import render_template
# import dash_bootstrap_components as dbc


# flask server 
application = flask.Flask(__name__)

# dash app with flask server
dash_app1 = Dash(__name__, server=application, url_base_pathname='/dashapp1/', 
        meta_tags=[{"name": "viewport", "content": "width=device-width"}],
        external_stylesheets=[dbc.themes.BOOTSTRAP])
dash_app2 = Dash(__name__, server=application, url_base_pathname='/dashapp2/',
        meta_tags=[{"name": "viewport", "content": "width=device-width"}],
        external_stylesheets=[dbc.themes.BOOTSTRAP])

# # flask app
@application.route('/')
def index():
    return flask.redirect(flask.url_for('/dashapp1/'))

dash_app1.title = "ESG Danger Management Monitoring Service."
dash_app2.title = "ESG Danger Management Monitoring Service. (page2)"
# server = app.server

#-----------------------------------------------------------------------------------------------------------------------
#웹상에 보여질 레이아웃 설정
#-----------------------------------------------------------------------------------------------------------------------
sidebar1 = html.Div(
    [ 
        
        html.Div(
            [ 
                html.Div(
                    [   #왼쪽상단 로고     
                        html.Img(
                            src=dash_app1.get_asset_url("dash-logo.png"),
                            id="plotly-image",
                            style={
                                "height": 100,
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-half column",
                    style={"width": "auto", 'height' : '100px'},
                ),
                        #title
                    html.Div(
                            [
                                html.H3(
                                    "한국산업단지 ESG 대응",
                                    style={"margin-bottom": "0px", 'font-size' : '1.45vh'},
                                ),
                                html.H5(
                                    "Monitoring Service", style={"margin-top": "0px", 'font-size' : '1.25vh'}
                                ),
                            ],
                    className="one-half column",
                    id="title",
                    style={"margin-top": "0px", 'font-size' : 24, 'width':'50%'},
                ),
                ],
            className= "mini_container",
            style={"background-color":  '#DBF6C6',"width": "auto", 'height' : '150px'},
            ),



        html.Div(
            [   
                 #데이터 선택 메뉴(기업규모, EU수출여부, 업종 별)
                html.P(
                    [   
                        html.H3(
                            "▼ Settings",
                            style={"margin-bottom": "0px"},
                        ),
                        
                        html.Hr(style = {'borderWidth': "0.3vh", "color": "#808080", 'margin-top':10, 'margin-bottom':10}),
                        
                        html.Button("▼ 기업 규모별 구분 : \n", className="control_label", id = 'button_size',style ={'border':0, 'font-size':'24px'}, n_clicks=0),
                        dbc.Collapse(
                            dcc.RadioItems(
                                id="well_status_selector",
                                options=
                                [
                                    {"label": "대기업 ", "value": "대기업"},
                                    {"label": "중견기업 ", "value": "중견기업"},
                                    {"label": "중소기업 ", "value": "중소기업"},
                                ],
                                value="중소기업",
                                className="mini_container", 
                                style = {'background-color' : '#F5F5F5'}
                            ),
                            id = 'collapse_size',
                            is_open = False
                        ),
                        html.P(),

                        html.Button("▼ 수출여부 : \n", className="control_label", id = 'button_eu',style ={'border':0, 'font-size':'24px'}, n_clicks=0),
                        dbc.Collapse(
                            dcc.Checklist(
                                ['EU','US'],
                                [None],
                                id="eu_check",
                                className="mini_container",
                                style = {'background-color' : '#F5F5F5'}
                            ),
                            id = 'collapse_eu',
                            is_open = False
                        ),
                        html.P(),

                        html.Button("▼ 업종 별 구분 : \n", className="control_label", id = 'button_code',style ={'border':0, 'font-size':'24px'}, n_clicks=0),
                        dbc.Collapse(
                            [
                                html.Div(
                                    dcc.Checklist(
                                        id="all-or-none",
                                        options=[{"label": "전체", "value": "전체"}],
                                        value=["전체"],
                                        labelStyle={},
                                    ),
                                    style = {'margin-left':'20px'}
                                ),

                                dcc.Checklist(
                                    options =[
                                        {'label':' A. 농업, 임업 및 어업', 'value':'농업, 임업 및 어업'}, 
                                        {'label':' B. 광업', 'value':'광업'}, 
                                        {'label':' C. 제조업', 'value':'제조업'}, 
                                        {'label':' D. 전기, 가스, 증기 및 공기 조절 공급원', 'value':'전기, 가스, 증기 및 공기 조절 공급원'}, 
                                        {'label':' E. 수도, 하수 및 폐기물 처리, 원료 재생업', 'value':'수도, 하수 및 폐기물 처리, 원료 재생업'}, 
                                        {'label':' F. 건설업', 'value':'건설업'}, 
                                        {'label':' G. 도매 및 소매업', 'value':'도매 및 소매업'}, 
                                        {'label':' H. 운수 및 창고업', 'value':'운수 및 창고업'}, 
                                        {'label':' I. 숙박 및 음식점업', 'value':'숙박 및 음식점업'},
                                        {'label':' J. 정보통신업', 'value':'정보통신업'},
                                        {'label':' K. 금융 및 보험업', 'value':'금융 및 보험업'},
                                        {'label':' L. 부동산업', 'value':'부동산업'},
                                        {'label':' M. 전문, 과학 및 기술 서비스업', 'value':'전문, 과학 및 기술 서비스업'},
                                        {'label':' N. 사업시설 관리, 사업 지원 및 임대 서비스업', 'value':'사업시설 관리, 사업 지원 및 임대 서비스업'},
                                        {'label':' O. 공공 행정, 국방 및 사회보장 행정', 'value':'공공 행정, 국방 및 사회보장 행정'},
                                        {'label':' P. 교육 서비스업', 'value':'교육 서비스업'},
                                        {'label':' Q. 보건업 및 사회복지 서비스업', 'value':'보건업 및 사회복지 서비스업'},
                                        {'label':' R. 예술, 스포츠 및 여가관련 서비스업', 'value':'예술, 스포츠 및 여가관련 서비스업'},
                                        {'label':' S. 협회 및 단체, 수리 및 기타 개인 서비스업', 'value':'협회 및 단체, 수리 및 기타 개인 서비스업'},
                                        {'label':' 그 외', 'value':None},        
                                    ],

                                    value = [
                                        '농업, 임업 및 어업',
                                        '광업',
                                        '제조업',
                                        '전기, 가스, 증기 및 공기 조절 공급원',
                                        '수도, 하수 및 폐기물 처리, 원료 재생업',
                                        '건설업',
                                        '도매 및 소매업',
                                        '운수 및 창고업',
                                        '숙박 및 음식점업',
                                        '정보통신업',
                                        '금융 및 보험업',
                                        '부동산업',
                                        '전문, 과학 및 기술 서비스업',
                                        '사업시설 관리, 사업 지원 및 임대 서비스업',
                                        '공공 행정, 국방 및 사회보장 행정',
                                        '교육 서비스업',
                                        '보건업 및 사회복지 서비스업',
                                        '예술, 스포츠 및 여가관련 서비스업',
                                        '협회 및 단체, 수리 및 기타 개인 서비스업',
                                        None
                                    ],
                                    id="well_statuses",
                                    className="mini_container",
                                    style={"height":850, "overflow":"auto", 'background-color' : '#F5F5F5', 'font-size' : '23px'}
                                ),
                            ],
                            id = 'collapse_code',
                            is_open = False
                        ),
                    ],
                    className="pretty_container three columns",
                    id="cross-filter-options",
                    style={'color':'#777777', "width": "98%", 'height' : 'auto', 'font-size' : '25px'}
                ),

                ],

            ),
    ]
)

content1 = html.Div(
    [ 
        #상단 전국 산업단지 상대분석 그래프 레이아웃
        html.Div(

                [
                    dcc.Graph(figure=Main_map(df),
                            style={'width':'25%',"height":1010,'float':'left'}
                            ),
                    dcc.Graph(figure=Main_graph(df),
                            style={'width':'70%',"height":1000,'margin-left':'25%'})
                ],
                id="Main_container",
                className="pretty_container",
                style={'color':'#777777','height':1030, 'width': '100%'}

            ),
            

                    #기업 등급별 매출액, 기업 수 그래프, 텍스트
                            html.Div(
                                [   
                                    #총 수출액 텍스트
                                    html.Div(
                                        [
                                            html.P(id="total_exports", style={'font': '', 'fontSize': 45}), 
                                            html.P("총 수출액 ( 단위 : $ )",
                                            style={'fontSize': 25})
                                        ],
                                        id="export",
                                        className="mini_container",
                                    ),
                                    #총 기업수 텍스트
                                    html.Div(
                                        [
                                            html.H6(id="total_companies", style={'font': '', 'fontSize': 45}),
                                            html.P("총 기업 수 ( 단위 : 개 )",
                                            style={'fontSize': 25})
                                        ],
                                        id="company",
                                        className="mini_container",
                                    ),
                                    #총 종업원 수 텍스트
                                    html.Div(
                                        [
                                            html.H6(id="total_employees", style={'font': '', 'fontSize': 45}),
                                            html.P("총 종업원 수 ( 단위 : 명 )",
                                            style={'fontSize': 25})
                                        ],
                                        id="employee",
                                        className="mini_container",
                                    )
                                ],
                                id="info-container",
                                className="row container-display",
                                style={'color':'#777777','width': '100%'}
                            ),
                            #산업단지 분석결과 텍스트
                            html.Div(
                                [
                                    html.P("선택하신 조건으로 AI 분석결과", style = {'display':'inline_block','float':'left', 'margin':'5px 10px 0px 30px'}),
                                    dcc.Dropdown([1, 2, 3, 4, 5, '전체'], 1, id='dropdown_grade', clearable=False, style = {'display':'inline_block','float':'left', 'width': '120px', 'height':45}),
                                    html.P(children = "등급 산업단지는 -입니다.", id = 'grade_text', style = {'display':'inline_block','float':'left', 'margin':'5px 0px 0px 0px'})
                                ],
                                id="Recommended_text",
                                className="pretty_container",
                                style={'color':'#777777','width': '100%', 'height':100, 'font-size':'30px'}
                            ),
                            #매출액, 기업수 그래프
                            html.Div(
                                [
                                    dcc.Graph(id="count_graph",style = {"height": 600,'width' : '90%', 'margin-bottom':'10%'})
                                ],
                                id="countGraphContainer",
                                className="pretty_container",
                                style={'color':'#777777','width': '100%', 'height':650}
                            ),              

    ],
                        className="row flex-display"
)



#레이아웃 설정
dash_app1.layout = html.Div(
    [   
                html.Div(
                    [html.A(
                        html.Button("산단별 시급도", id="-button1", style={'width': '250px', 'height': '80px', 'font-size': '30px', 'float':'left', 'margin-left': '20px', 'color':'#3ba706', 'border-color':'#3ba706'}),
                        href="/dashapp1/",style={'margin-top': ''}),
                    html.A(
                        html.Button("기업별 시급도", id="-button2", n_clicks=0, style={'width': '250px', 'height': '80px', 'font-size': '30px', 'float':'left', 'margin-left': '40px'}),
                        href="/dashapp2/",style={'margin-top': ''}),

                    html.A(
                        html.Button("빅리더 AI 아카데미", id="learn-more-button",style={'width': '300px', 'height': '80px', 'font-size': '30px', 'float':'right', 'margin-bottom': '20px'}),
                        href="https://bigleader.net/", style={'margin-top': ''}
                        )
                    ],
                id="page-button"
                ),
         
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(sidebar1, width='2'),
                        dbc.Col(content1, width='10')
                    ]
                ),
            ],
            fluid=True
        ),

        dcc.Store(id="aggregate_data"),
        html.Div(id="output-clientside"),
    
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)




dash_app1.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)


#-----------------------------------------------------------------------------------------------------------------------
#레이아웃 업데이트를 위한 콜백함수 정의
#-----------------------------------------------------------------------------------------------------------------------

@dash_app1.callback(
    Output("well_statuses", "value"),
    [Input("all-or-none", "value")],
    [State("well_statuses", "options")],
)
def select_all_none(all_selected, options):
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none

@dash_app1.callback(
    Output('count_graph', 'figure'),
    Output('grade_text', 'children'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('dropdown_grade','value'),
    Input('eu_check','value'))
def update_map(size_type, code_value, grade, eu_select):
    '''
    Description :
    전국 산업단지 매출액, 기업수 그래프 콜백함수

    Parameters :
    size_type = 기업규모(ex '대기업', '중견기업', '중소기업')
    code_value = 산업단지 업종명('')
    grade = 산업단지 등급(1~5)
    eu_select = EU수출여부(ex '여')
    
    return :
    Plotly Express의 make_subplots(산업단지 매출액, 기업 수 그래프),
    산업단지 분석결과 텍스트를 반환
    '''

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    if code_value != []:
        fig, text = entire_EDA(df_condition, grade)
    else:
        text = "등급 산업단지는 -------- 입니다."
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
    return fig, text
    
@dash_app1.callback(
    Output('total_exports', 'children'),
    Output('total_companies', 'children'),
    Output('total_employees', 'children'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'))
def update_text(size_type, code_value, eu_select):
    '''
    Description :
    산업단지 총 수출액, 총 기업수, 총 종사자수 텍스트 콜백함수

    Parameters :
    size_type = 기업규모(ex '대기업', '중견기업', '중소기업')
    code_value = 산업단지 업종명('')
    eu_select = EU수출여부(ex '여')
    
    return :
    산업단지 총 매출액, 기업 수, 종사자 수 텍스트를 반환 
    '''
    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    data_money=int(df_condition['매출액_2021'].sum())
    data_people=df_condition['종사자수_2021'].sum()
    data_company=df_condition.shape[0]

    return '{:,.0f}'.format(data_money), int(data_company), int(data_people)

@dash_app1.callback(
    Output("collapse_size", "is_open"),
    Output('button_size', 'children'),
    [Input("button_size", "n_clicks")],
    [State("collapse_size", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 기업 규모별 구분 : \n"
        else:
            text = "▼ 기업 규모별 구분 : \n"
        return not is_open, text
    return is_open, text

@dash_app1.callback(
    Output("collapse_eu", "is_open"),
    Output("button_eu", "children"),
    [Input("button_eu", "n_clicks")],
    [State("collapse_eu", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 수출여부 : \n"
        else:
            text = "▼ 수출여부 : \n",
        return not is_open, text
    return is_open, text

@dash_app1.callback(
    Output("collapse_code", "is_open"),
    Output("button_code", "children"),
    [Input("button_code", "n_clicks")],
    [State("collapse_code", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 업종 별 구분 : \n"
        else:
            text = "▼ 업종 별 구분 : \n",
        return not is_open, text
    return is_open, text

# --------------------------------------------------------------------------------------------------------

# df_company_grade = df.sort_values(by=['Score'], axis=0, ascending=False)
# df_company_grade = df_company_grade.head(10)

# df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')

# fig_sandan = px.scatter_mapbox(df_company_loc,
#                         mapbox_style='carto-positron', 
#                         lat="latitude", lon="longitude",
#                         zoom=5.7, center = {"lat": 36.065, "lon": 127.686},
#                         # color='산단등급',
#                         size = 'Score',
#                         size_max=25,
#                         opacity=0.4,
#                         )
                        
# text = '전국 기업 시급성 분포'

# fig_sandan.update_layout(
#                         title=dict(
#                             text=text,
#                             x=0.02,
#                             y=0.98,
#                             font_size=30),
#                         font=dict(
#                             family="Arial",
#                             size=18,
#                             color="#777777"
#                         ),
#                         margin={"r":0,"t":40,"l":0,"b":0},
#                         paper_bgcolor='#F9F9F9',
#                         plot_bgcolor='#F9F9F9',
#                         )


# fig_company_candidate = go.Figure(go.Bar(
#             x=df_company_loc.매출액_2021,
#             y=df_company_loc.업종코드,
#             orientation='h'))


# fig_company_candidate.update_layout(
#                         title=dict(
#                             text='전국 기업 추천',
#                             x=0.02,
#                             y=0.98,
#                             font_size=40),
#                         font=dict(
#                             family="Arial",
#                             size=30,
#                             color="#777777"
#                         ),
#                         margin={"r":0,"t":40,"l":0,"b":0},
#                         paper_bgcolor='#F9F9F9',
#                         plot_bgcolor='#F9F9F9',
#                         )

# fig_bar = go.Figure(data=[go.Table(header=dict(values=['기업명', '업종분류'], height=70),
#             cells=dict(values=[df_company_loc.업종코드, df_company_loc.대분류], height=60))
#                 ])


# fig_bar.update_layout(
#                     # title=dict(
#                     #     text='전국 기업 추천',
#                     #     x=0.02,
#                     #     y=0.98,
#                     #     font_size=20),
#                     font=dict(
#                         family="Arial",
#                         size=30,
#                         color="#777777"
#                     ),
#                     margin={"r":0,"t":5,"l":0,"b":0},
#                     paper_bgcolor='#F9F9F9',
#                     plot_bgcolor='#F9F9F9',
#                     )



#--------------------------------------------------------------------------------------------------------
 
dash_app2.layout = html.Div(
    [
        html.Div(
            [html.A(
                html.Button("산단별 시급도", id="-button1", style={'width': '250px', 'height': '80px', 'font-size': '30px', 'float':'left', 'margin-left': '20px'}),
                href="/dashapp1/",style={'margin-top': ''}),
            html.A(
                html.Button("기업별 시급도", id="-button2", n_clicks=0, style={'width': '250px', 'height': '80px', 'font-size': '30px', 'float':'left', 'margin-left': '40px', 'color':'#3ba706', 'border-color':'#3ba706'}),
                href="/dashapp2/",style={'margin-top': ''}),

            html.A(
                html.Button("빅리더 AI 아카데미", id="learn-more-button",style={'width': '300px', 'height': '80px', 'font-size': '30px', 'float':'right', 'margin-bottom': '20px','margin-right': '5%'}),
                href="https://bigleader.net/", style={'margin-top': ''}
                )
            ],
            id="page-button"
        ),

        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(sidebar1, width='2'),
                        dbc.Col(
                            [
                                #상단 산업단지 분석
                                html.Div(
                                    [  
                                        #산업단지 검색 input창
                                        html.Div(
                                            [
                                                dcc.Input(id="search", type="text", placeholder="산업단지 검색", debounce=True, style = {
                                                    'height': '45px', 'width' : '15%', 'display':'inline_block','float':'left', 'margin':'15px 10px 0px 100px'})
                                            ]
                                        ),
                                        #산업단지 분석결과 텍스트
                                        html.P(children = "검색된 1등급 기업 갯수는 총 ", style = {'display':'inline_block','float':'left', 'margin':'7px 10px 0px 100px'}),
                                        html.P(children = "-", id = 'company_grade1_text', style = {'display':'inline_block','float':'left', 'margin':'7px 0px 0px 0px'}),
                                        html.P(children = "개 입니다.", style = {'display':'inline_block','float':'left', 'margin':'7px 0px 0px 0px'})
                                    ],
                                    className="pretty_container",
                                    id = "input_sandan_container",
                                    style={'height':100, 'fontSize':'35px', 'width':'95%'}
                                ),


                                html.Div(
                                    #기업 시급성 맵
                                    html.Div(
                                        dcc.Graph(id="individual_graph3",style={"height":1500}),
                                        className="pretty_container columns",
                                        style={"height":1620, 'width':'95%'},
                                    ),
                                    
                                    className="four columns",
                                    # id="cross-filter-options 2",

                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            [   

                                                #산업단지 수출액 비율 파이 그래프
                                                html.Div(
                                                    dcc.Graph(id="pie_graph1",figure=sales_pie(df),style={"height":700}),
                                                    className="pretty_container columns",
                                                    style={"height":750, 'width':'45.5%'},
                                                ),
                                                #산업단지 수출액 변화추이 그래프
                                                html.Div(
                                                    [dcc.Graph(id="bar_graph1",style={"height":700})],
                                                    className="pretty_container columns",
                                                    style={"height":750, 'width':'45.5%'},
                                                ),
                                                

                                            ],
                                            className="row flex-display",
                                        ),
                                        
                                        html.Div(
                                            [   
                                                #산업단지 시급성 막대 그래프
                                                html.Div(
                                                    dcc.Graph(id="pie_graph3",style={"height":700}),
                                                    className="pretty_container columns",
                                                    style={"height":750, 'width':'45.5%'},
                                                ),
                                                #산업단지 업종 그래프
                                                html.Div(
                                                    [dcc.Graph(id="bar_graph3",style={"height":700})],
                                                    className="pretty_container columns",
                                                    style={"height":750, 'width':'45.5%'},
                                                ),
                                            ],
                                            className="row flex-display",
                                        ),

                                        html.Div(
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Button("<<", id = "company_grade1_reset", style ={'width': '75px', 'display':'inline_block', 'font-size':30}, n_clicks=0),
                                                            html.Button("<", id = "company_grade1_leftbutton", style ={'width': '75px', 'display':'inline_block', 'font-size':30, 'margin-right':'5px'}, n_clicks=0),
                                                            html.Button("-", id = "button1", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button2", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button3", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button4", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button5", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button6", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button7", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button8", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button9", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button("-", id = "button10", style ={'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}),
                                                            html.Button(">", id = "company_grade1_rightbutton", style ={'width': '75px', 'display':'inline_block', 'font-size':30}, n_clicks=0),
                                                            html.Button(">>", id = "company_grade1_forward", style ={'width': '75px', 'display':'inline_block', 'font-size':30, 'margin-right':'5px'}, n_clicks=0),
                                                            # html.P("-", id = "company_grade1_text", style ={'display':'inline_block', 'float':'right'}),
                                                        ],
                                                        style={'margin-top':8, 'text-align':'center'},
                                                    )
                                                ],
                                                className="pretty_container columns",
                                                style={"height":80, 'width':'92%'},
                                            ),
                                            className="row flex-display",
                                        ),
                                    ],
                                    className="",
                                    id="cross-filter-options 2",
                                ),

                            ],
                            width='10'
                        )
                    ]
                ),
            ],
            fluid=True
        ),


    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@dash_app2.callback(
    Output('pie_graph1', 'figure'),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'))
def pie(search, size_type, code_value, eu_select):
    '''
    Description :
    산업단지별 수출액 비율 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 pie chart를 반환
    '''
    if code_value == []:
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
        text = "___"
        return fig
    #기업 페이지 초기화 기능도 넣음
    global current_page
    global page1
    current_page = 1
    page1 = 0

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_condition = Sandan_df(df_condition, sandan_name)
    
    if is_search:
        return sales_pie_sandan(df_condition)
    else:
        return sales_pie(df_condition)

@dash_app2.callback(
    Output('bar_graph1', 'figure'),
    # Output('input_text1', 'children'),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'))
def ChangeInExport(search, size_type, code_value, eu_select):
    '''
    Description :
    산업단지 별 수출액 변화추이 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 make_subplots객체(수출액 변화추이 그래프),
    산업단지 업종별 분석결과 텍스트를 반환
    '''
    if code_value == []:
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
        text = "___"
        return fig, text

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_condition = Sandan_df(df_condition, sandan_name)
    
    if is_search:
        fig_temp, text_upjong= ChangeInExport_industry(df_condition, sandan_name)
        text = text_upjong
        return fig_temp
    else:
        fig_temp = ChangeInExport_sandan(df_condition)
        text = '-'
        return fig_temp



@dash_app2.callback(
    Output("individual_graph3", "figure"),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'),
    Input("button1", "n_clicks"),
    Input("button2", "n_clicks"),
    Input("button3", "n_clicks"),
    Input("button4", "n_clicks"),
    Input("button5", "n_clicks"),
    Input("button6", "n_clicks"),
    Input("button7", "n_clicks"),
    Input("button8", "n_clicks"),
    Input("button9", "n_clicks"),
    Input("button10", "n_clicks"))
def sandan_search(search, size_type, code_value, eu_select, button1, button2, button3, button4, button5, button6, button7, button8, button9, button10):
    '''
    Description :
    산업단지 시급성 분포 맵 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    size_type = 기업규모(ex '대기업', '중견기업', '중소기업')
    code_value = 산업단지 업종명('')
    
    return :
    Plotly Express의 scatter_mapbox(전국 산업단지 시급성 분포 맵)을 반환,
    특정 산업단지 검색결과가 존재할 시 Plotly Express의 choropleth_mapbox(특정 산업단지 확대 맵)을 반환
    '''
    if code_value == []:
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
        return fig

    lat = 36.065
    lon = 127.686
    zoom_size = 7

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_sandan = Sandan_df(df_condition, sandan_name)


    #특정 산업단지 검색결과가 존재할 시, 특정 산업단지를 크게 지도에 표시  
    if is_search:
        text = sandan_name + ' 지도'
        sandan_location = df_sandan_location[df_sandan_location['name'] == sandan_name]
        zoom_size = 11.5
        lat = float(sandan_location['latitude'].values[0])
        lon = float(sandan_location['longitude'].values[0])
        
        fig_sandan = px.choropleth_mapbox(df_sandan_loc, 
                        geojson=geo_data_sandan,
                        locations='산업단지',
                        color='산단등급',
                        range_color = [1,5],
                        featureidkey='properties.name',
                        mapbox_style="carto-positron",
                        zoom=zoom_size, center = {"lat": lat, "lon": lon},
                        opacity=0.8)
    #특정 산업단지 검색결과가 존재하지 않을 시 , 지도에 전국 산업단지 시급성 분포도를 표시
    else:
        df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)
        global current_page
        global page1
        df_company_grade = df_company_grade[df_company_grade['기업등급'] == 5]
        df_company_grade = df_company_grade.iloc[(page1+current_page-1)*10:(page1+current_page)*10]

        # df_company_grade = df_company_grade.head(100)
        # df_company_grade = df_company_grade.sort_values(by=['매출액_2021'], axis=0, ascending=False)
        # df_company_grade = df_company_grade.head(10)


        df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')

        fig_sandan = px.scatter_mapbox(df_company_loc,
                                mapbox_style='carto-positron', 
                                lat="latitude", lon="longitude",
                                zoom=5.7, center = {"lat": 36.065, "lon": 127.686},
                                color='업체명',
                                size = 'Score',
                                size_max=25,
                                opacity=0.4,
                                )
                                
        text = '전국 기업 시급성 분포'

    
    fig_sandan.update_layout(
                            title=dict(
                                text=text,
                                x=0.02,
                                y=0.98,
                                font_size=40),
                            font=dict(
                                family="Arial",
                                size=30,
                                color="#777777"
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=0.975,
                                xanchor="right",
                                x=1,
                                bgcolor='rgba(0,0,0,0.02)',
                                font=dict(
                                family="Courier",
                                size=20
                                ),
                            ),
                            margin={"r":0,"t":150,"l":0,"b":0},
                            paper_bgcolor='#F9F9F9',
                            plot_bgcolor='#F9F9F9',
                            )

    return fig_sandan


@dash_app2.callback(
    Output('pie_graph3', 'figure'),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'),
    Input("button1", "n_clicks"),
    Input("button2", "n_clicks"),
    Input("button3", "n_clicks"),
    Input("button4", "n_clicks"),
    Input("button5", "n_clicks"),
    Input("button6", "n_clicks"),
    Input("button7", "n_clicks"),
    Input("button8", "n_clicks"),
    Input("button9", "n_clicks"),
    Input("button10", "n_clicks"),)
def pie(search, size_type, code_value, eu_select, button1, button2, button3, button4, button5, button6, button7, button8, button9, button10):
    '''
    Description :
    산업단지별 수출액 비율 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 pie chart를 반환
    '''
    if code_value == []:
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
        return fig

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_condition = Sandan_df(df_condition, sandan_name)

    if is_search:
        df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)
        global current_page
        global page1
        df_company_grade = df_company_grade[df_company_grade['기업등급'] == 5]
        df_company_grade = df_company_grade.iloc[(page1+current_page-1)*10:(page1+current_page)*10]

        # df_company_grade = df_company_grade.head(100)
        # df_company_grade = df_company_grade.sort_values(by=['매출액_2021'], axis=0, ascending=False)
        # df_company_grade = df_company_grade.head(10)

        df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')
        fig_company_candidate = go.Figure(go.Bar(
                x=df_company_loc.매출액_2021,
                y=df_company_loc.업체명,
                marker = dict(color = '#d50801'),    
                orientation='h')
        )


        text = sandan_name +' 기업 추천'
        fig_company_candidate.update_layout(
                                title=dict(
                                    text=text,
                                    x=0.02,
                                    y=0.98,
                                    font_size=40),
                                font=dict(
                                    family="Arial",
                                    size=30,
                                    color="#777777"
                                ),
                                margin={"r":0,"t":60,"l":0,"b":0},
                                paper_bgcolor='#F9F9F9',
                                plot_bgcolor='#F9F9F9',  
                                yaxis=dict(autorange="reversed"),
                                          
                                )

        return fig_company_candidate
    else:
        df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)
        df_company_grade = df_company_grade[df_company_grade['기업등급'] == 5]
        df_company_grade = df_company_grade.iloc[(page1+current_page-1)*10:(page1+current_page)*10]

        # df_company_grade = df_company_grade.head(100)
        # df_company_grade = df_company_grade.sort_values(by=['매출액_2021'], axis=0, ascending=False)
        # df_company_grade = df_company_grade.head(10)

        df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')

        fig_company_candidate = go.Figure(go.Bar(
                x=df_company_loc.매출액_2021,
                y=df_company_loc.업체명,
                marker = dict(color = '#d50801'),
                orientation='h'
                )
        )


        fig_company_candidate.update_layout(
                                title=dict(
                                    text='전국 기업 추천',
                                    x=0.02,
                                    y=0.98,
                                    font_size=40),
                                font=dict(
                                    family="Arial",
                                    size=30,
                                    color="#777777"
                                ),
                                margin={"r":0,"t":60,"l":0,"b":0},
                                paper_bgcolor='#F9F9F9',
                                plot_bgcolor='#F9F9F9',
                                yaxis=dict(autorange="reversed"),

                                )
        return fig_company_candidate


@dash_app2.callback(
    Output('bar_graph3', 'figure'),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'),
    Input("button1", "n_clicks"),
    Input("button2", "n_clicks"),
    Input("button3", "n_clicks"),
    Input("button4", "n_clicks"),
    Input("button5", "n_clicks"),
    Input("button6", "n_clicks"),
    Input("button7", "n_clicks"),
    Input("button8", "n_clicks"),
    Input("button9", "n_clicks"),
    Input("button10", "n_clicks"),)
def ChangeInExport(search, size_type, code_value, eu_select, button1, button2, button3, button4, button5, button6, button7, button8, button9, button10):
    '''
    Description :
    산업단지 별 수출액 변화추이 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 make_subplots객체(수출액 변화추이 그래프),
    산업단지 업종별 분석결과 텍스트를 반환
    '''
    global current_page
    global page1

    if code_value == []:
        fig = dict({
            "data": [{"type": "bar",
                    "x": [],
                    "y": []}],
            "layout": {"title": {"text": "검색 결과가 존재하지 않습니다."}}
        })
        return fig

    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_condition = Sandan_df(df_condition, sandan_name)

    if is_search:
        df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)

        df_company_grade = df_company_grade[df_company_grade['기업등급'] == 5]
        df_company_grade = df_company_grade.iloc[(page1+current_page-1)*10:(page1+current_page)*10]
        # df_company_grade = df_company_grade.head(100)
        # df_company_grade = df_company_grade.sort_values(by=['매출액_2021'], axis=0, ascending=False)
        # df_company_grade = df_company_grade.head(10)

        df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')

        fig = go.Figure(data=[go.Table(header=dict(values=['기업명', '업종분류'], height=70),
                 cells=dict(values=[df_company_loc.업체명, df_company_loc.대분류], height=60))
                     ])



        fig.update_layout(
                            # title=dict(
                            #     text='전국 기업 추천',
                            #     x=0.02,
                            #     y=0.98,
                            #     font_size=20),
                            font=dict(
                                family="Arial",
                                size=30,
                                color="#777777"
                            ),
                            margin={"r":0,"t":20,"l":0,"b":0},
                            paper_bgcolor='#F9F9F9',
                            plot_bgcolor='#F9F9F9',
                            legend=dict(xanchor="right", yanchor="bottom",x = 0.7, y=0.7, font_size=20,bgcolor='rgba(0,0,0,0.01)')
                            )
        return fig
    
    else:
        df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)

        df_company_grade = df_company_grade[df_company_grade['기업등급'] == 5]
        df_company_grade = df_company_grade.iloc[(page1+current_page-1)*10:(page1+current_page)*10]
        # df_company_grade = df_company_grade.head(100)
        # df_company_grade = df_company_grade.sort_values(by=['매출액_2021'], axis=0, ascending=False)
        # df_company_grade = df_company_grade.head(10)

        df_company_loc = pd.merge(df_company_grade, df_sandan_location, how='left', left_on='산업단지', right_on='name')

        fig = go.Figure(data=[go.Table(header=dict(values=['기업명', '업종분류'], height=70),
                 cells=dict(values=[df_company_loc.업체명, df_company_loc.대분류], height=60))
                     ])



        fig.update_layout(
                            # title=dict(
                            #     text='전국 기업 추천',
                            #     x=0.02,
                            #     y=0.98,
                            #     font_size=20),
                            font=dict(
                                family="Arial",
                                size=30,
                                color="#777777"
                            ),
                            margin={"r":0,"t":20,"l":0,"b":0},
                            paper_bgcolor='#F9F9F9',
                            plot_bgcolor='#F9F9F9',
                            )
        return fig



# @dash_app2.callback(
#     Output("company_grade1_text", "children"),
#     [Output("button1", "children"),
#     Output("button2", "children"),
#     Output("button3", "children"),
#     Output("button4", "children"),
#     Output("button5", "children"),
#     Output("button6", "children"),
#     Output("button7", "children"),
#     Output("button8", "children"),
#     Output("button9", "children"),
#     Output("button10", "children")],
#     Input("company_grade1_leftbutton", "n_clicks"),
#     Input("company_grade1_rightbutton", "n_clicks"),
#     Input("company_grade1_reset", "n_clicks"),
#     Input("company_grade1_forward", "n_clicks"),
#     Input('search', 'value'),
#     Input('well_status_selector', 'value'),
#     Input('well_statuses','value'),
#     Input('eu_check','value'),
# )
# def CompanyGrade1Button(leftbutton, rightbutton, reset, forward, search, size_type, code_value, eu_select):
#     df_condition = ExportEU_df(df, eu_select)
#     df_condition = CompanySize_df(df_condition, size_type)
#     df_condition = df_condition[df_condition['대분류'].isin(code_value)]
#     df_condition = df_condition[df_condition['기업등급'] == 5]

#     sandan_name, is_search = SandanSearch_df(df_condition, search)
#     df_condition = Sandan_df(df_condition, sandan_name)

#     df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)
   
#     company_len = len(df_company_grade)
#     page_num = math.ceil(company_len/10.0)

#     button_text = ['-','-','-','-','-','-','-','-','-','-']
    
#     text = str(company_len)
    
#     global page1
#     if "company_grade1_leftbutton" == ctx.triggered_id:
#         if page1 > 0 :
#             page1 = page1 - 10
#     if "company_grade1_rightbutton" == ctx.triggered_id:
#         if page1+10 < page_num:
#             page1 = page1 + 10
    
#     if "company_grade1_reset" == ctx.triggered_id:
#         page1 = 0
#     if "company_grade1_forward" == ctx.triggered_id:
#         page1 = int((page_num-1)/10)*10

#     for i in range(page1, page_num):
#         if i > page1+9:
#             break
#         button_text[i-page1] = str(i+1)

#     return text, button_text[0], button_text[1], button_text[2], button_text[3], button_text[4], button_text[5], button_text[6], button_text[7], button_text[8], button_text[9]


global page1
page1 = 0
global currentpage_sum
currentpage_sum = 1
global cansee_currentpage
cansee_currentpage = True
global current_page
current_page = 1
@dash_app2.callback(
    Output("company_grade1_text", "children"),
    [Output("button1", "children"),
    Output("button2", "children"),
    Output("button3", "children"),
    Output("button4", "children"),
    Output("button5", "children"),
    Output("button6", "children"),
    Output("button7", "children"),
    Output("button8", "children"),
    Output("button9", "children"),
    Output("button10", "children")],
    Output("button1", "style"),
    Output("button2", "style"),
    Output("button3", "style"),
    Output("button4", "style"),
    Output("button5", "style"),
    Output("button6", "style"),
    Output("button7", "style"),
    Output("button8", "style"),
    Output("button9", "style"),
    Output("button10", "style"),
    Input("company_grade1_leftbutton", "n_clicks"),
    Input("company_grade1_rightbutton", "n_clicks"),
    Input("company_grade1_reset", "n_clicks"),
    Input("company_grade1_forward", "n_clicks"),
    Input("button1", "n_clicks"),
    Input("button2", "n_clicks"),
    Input("button3", "n_clicks"),
    Input("button4", "n_clicks"),
    Input("button5", "n_clicks"),
    Input("button6", "n_clicks"),
    Input("button7", "n_clicks"),
    Input("button8", "n_clicks"),
    Input("button9", "n_clicks"),
    Input("button10", "n_clicks"),
    Input('search', 'value'),
    Input('well_status_selector', 'value'),
    Input('well_statuses','value'),
    Input('eu_check','value'),
)
def PageButtonClick(leftbutton, rightbutton, reset, forward, button1, button2, button3, button4, button5, button6, button7, button8, button9, button10, search, size_type, code_value, eu_select):
    global currentpage_sum
    global current_page
    global cansee_currentpage
    global page1


    df_condition = ExportEU_df(df, eu_select)
    df_condition = CompanySize_df(df_condition, size_type)
    df_condition = df_condition[df_condition['대분류'].isin(code_value)]
    df_condition = df_condition[df_condition['기업등급'] == 5]

    sandan_name, is_search = SandanSearch_df(df_condition, search)
    df_condition = Sandan_df(df_condition, sandan_name)

    df_company_grade = df_condition.sort_values(by=['Score'], axis=0, ascending=False)
   
    company_len = len(df_company_grade)
    page_num = math.ceil(company_len/10.0)

    button_text = ['-','-','-','-','-','-','-','-','-','-']
    
    text = str(company_len)
    
    global page1
    if "company_grade1_leftbutton" == ctx.triggered_id:
        if page1 > 0 :
            page1 = page1 - 10
    if "company_grade1_rightbutton" == ctx.triggered_id:
        if page1+10 < page_num:
            page1 = page1 + 10
    
    if "company_grade1_reset" == ctx.triggered_id:
        page1 = 0
    if "company_grade1_forward" == ctx.triggered_id:
        page1 = int((page_num-1)/10)*10

    for i in range(page1, page_num):
        if i > page1+9:
            break
        button_text[i-page1] = str(i+1)



    buttoncolor1 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor2 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor3 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor4 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor5 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor6 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor7 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor8 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor9 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    buttoncolor10 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
    
    clickId = ctx.triggered_id

    if "button1" == clickId:
        current_page = 1
        currentpage_sum = page1 + current_page
        buttoncolor1 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button2" == clickId:
        current_page = 2
        currentpage_sum = page1 + current_page
        buttoncolor2 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button3" == clickId:
        current_page = 3
        currentpage_sum = page1 + current_page
        buttoncolor3 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button4" == clickId:
        current_page = 4
        currentpage_sum = page1 + current_page
        buttoncolor4 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button5" == clickId:
        current_page = 5
        currentpage_sum = page1 + current_page
        buttoncolor5 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button6" == clickId:
        current_page = 6
        currentpage_sum = page1 + current_page
        buttoncolor6 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button7" == clickId:
        current_page = 7
        currentpage_sum = page1 + current_page
        buttoncolor7 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button8" == clickId:
        current_page = 8
        currentpage_sum = page1 + current_page
        buttoncolor8 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button9" == clickId:
        current_page = 9
        currentpage_sum = page1 + current_page
        buttoncolor9 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    elif "button10" == clickId:
        current_page = 10
        currentpage_sum = page1 + current_page
        buttoncolor10 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
    else: 
        #버튼을 클릭하지 않고 다른 선택메뉴를 골랐을 경우
        if (("company_grade1_leftbutton" != clickId) & ("company_grade1_rightbutton" != clickId) &
                ("company_grade1_reset" != clickId) & ("company_grade1_forward" != clickId)):
            buttoncolor1 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            currentpage_sum = 1
    

    if (("company_grade1_rightbutton" == clickId) | ("company_grade1_leftbutton" == clickId) | ("company_grade1_reset" == clickId) | ("company_grade1_forward" == clickId)):

        cansee_currentpage = False
        for i in range(page1+1, page1+11):
            if (i == currentpage_sum):
                cansee_currentpage = True

        if cansee_currentpage:
            if current_page == 1:
                buttoncolor1 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 2:
                buttoncolor2 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 3:
                buttoncolor3 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 4:
                buttoncolor4 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 5:
                buttoncolor5 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 6:
                buttoncolor6 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 7:
                buttoncolor7 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 8:
                buttoncolor8 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 9:
                buttoncolor9 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
            if current_page == 10:
                buttoncolor10 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':35, 'color':'#3ba706'}
        else:
            buttoncolor1 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor2 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor3 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor4 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor5 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor6 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor7 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor8 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor9 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}
            buttoncolor10 = {'width': '75px', 'display':'inline_block', 'margin-right':10, 'border':0, 'font-size':24}

    return text, button_text[0], button_text[1], button_text[2], button_text[3], button_text[4], button_text[5], button_text[6], button_text[7], button_text[8], button_text[9], buttoncolor1, buttoncolor2, buttoncolor3, buttoncolor4, buttoncolor5, buttoncolor6, buttoncolor7, buttoncolor8, buttoncolor9, buttoncolor10

@dash_app2.callback(
    Output("well_statuses", "value"),
    [Input("all-or-none", "value")],
    [State("well_statuses", "options")],
)
def select_all_none(all_selected, options):
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none
    

@dash_app2.callback(
    Output("collapse_size", "is_open"),
    Output('button_size', 'children'),
    [Input("button_size", "n_clicks")],
    [State("collapse_size", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 기업 규모별 구분 : \n"
        else:
            text = "▼ 기업 규모별 구분 : \n"
        return not is_open, text
    return is_open, text

@dash_app2.callback(
    Output("collapse_eu", "is_open"),
    Output("button_eu", "children"),
    [Input("button_eu", "n_clicks")],
    [State("collapse_eu", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 수출여부 : \n"
        else:
            text = "▼ 수출여부 : \n",
        return not is_open, text
    return is_open, text

@dash_app2.callback(
    Output("collapse_code", "is_open"),
    Output("button_code", "children"),
    [Input("button_code", "n_clicks")],
    [State("collapse_code", "is_open")],
)
def toggle_left(n, is_open):
    if n:
        if is_open == False:
            text = "▲ 업종 별 구분 : \n"
        else:
            text = "▼ 업종 별 구분 : \n",
        return not is_open, text
    return is_open, text


#-----------------------------------------------------------------------------------------------------------------    
#서버 실행
#-----------------------------------------------------------------------------------------------------------------    

if __name__ == "__main__":
    application.debug = True
    application.run(host = "0.0.0.0", port ="5000")

