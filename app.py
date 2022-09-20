
#필요 라이브러리
import dash
import dash_table
from dash import Dash, html, dcc, Input, Output, ClientsideFunction

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
import json

import seaborn as sns

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
colors_map = ['#0e0889', '#7f07a5', '#cb487a', '#f69740', '#f5ea27', '#9ccc0c', '#41b30c', '#0cb38c']

# 산업분류 리스트 만들기
industry_list = df['산업입주_대분류'].unique()

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
    df = 분류할 데이터프레임. ['산업단지','산업입주_대분류','매출액_2016','매출액_2017',
    '매출액_2018','매출액_2019','매출액_2020','매출액_2021']칼럼을 포함
    return :
    전국 산업단지별 수출액 비율을 나타낸 Plotly Express의 pie chart를 반환 
    '''

    #산업단지별 수출액(매출액)합 분류
    df_temp=df[['산업단지','산업입주_대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp=df_temp.groupby(['산업단지','산업입주_대분류']).sum().reset_index()

    dff_pie=df_temp.drop(['산업입주_대분류'],axis=1).groupby(['산업단지']).sum()
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
        font_size=20,),
        font=dict(
            family="Arial",
            size=13,
            color="#777777"
            ),
        legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=0.99,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0.02)',
                    font=dict(
                    family="Courier",
                    size=8.2,
                    ),
                ),
        margin=dict(l=10, r=10, t=108, b=5),
        paper_bgcolor='#F9F9F9',
        plot_bgcolor='#F9F9F9')
    return fig



def sales_pie_sandan(df_sandan):
    '''
    Description :
    데이터 프레임을 input값으로 받아,
    산업단지내 업종별 수출액 비율 그래프를 생성
    
    Parameters :
    df = 분류할 데이터프레임. ['산업단지','산업입주_대분류','매출액_2016','매출액_2017',
    '매출액_2018','매출액_2019','매출액_2020','매출액_2021']칼럼을 포함
    return :
    산업단지내 업종 별 수출액 비율을 나타낸 Plotly Express의 pie chart를 반환 
    '''

    df_temp=df_sandan[['산업단지','산업입주_대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp=df_temp.groupby(['산업단지','산업입주_대분류']).sum().reset_index()

    dff_pie=df_sandan.drop(['산업단지'],axis=1).groupby(['산업입주_대분류']).sum()
    dff_pie=dff_pie.sort_values(by=['매출액_2021'],ascending=False)[:8]

    title_text=df_sandan['산업단지'].values[0]
    fig = px.pie(dff_pie, names=dff_pie.index,
                 values='매출액_2021', hole=0.4, color_discrete_sequence=colors_map)
    fig.update_layout(
    title=dict(
    text='%s 분야별 수출액 비율' % title_text,
    x=0.02,
    y=0.98,
    font_size=20,),
    font=dict(
        family="Arial",
        size=13,
        color="#777777"
        ),
    legend=dict(
                orientation="h",
                yanchor="bottom",
                y=0.99,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.02)',
                font=dict(
                family="Courier",
                size=8.2,
                ),
            ),
    margin=dict(l=10, r=10, t=108, b=5),
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
        title=dict(
        text='전국 산업단지 매출액  &  기업 수',
        x=0.02,
        y=0.98,
        font=dict(
            family="Arial",
            size=23,
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
        legend=dict(xanchor="right", yanchor="bottom",y=0.01, font_size=10),
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
        title=dict(
        text='전국 산업단지 시급도,수출액,기업수 상대분석',
        x=0.05,
        y=0.98,
        font=dict(
            family="Arial",
            size=23,
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
            domain=[0, 0.35],
            range=[0,15]
        ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.38, 1],
            range=[0,20],
            side='bottom',
            dtick=5,
        ),
        legend=dict(xanchor="right", yanchor="bottom",y=0.01, font_size=10),
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
                                y=0.02,
                                font_size=20
                                ),
                            font=dict(
                                family="Arial",
                                size=9,
                                color="#777777"
                                ),
                            margin={"r":0,"t":20,"l":0,"b":33},
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
    input_df = 분류할 데이터프레임. ['산업단지','산업입주_대분류','매출액_2016','매출액_2017','매출액_2018',
    '매출액_2019','매출액_2020','매출액_2021']칼럼을 포함 
    return : 
    graph_objects의 Figure()객체(수출액 변화 추이 그래프)
    '''

    df_temp_sandan=df[['산업단지','산업입주_대분류','매출액_2016','매출액_2017','매출액_2018','매출액_2019','매출액_2020','매출액_2021']]
    df_temp_sandan=df_temp_sandan.groupby(['산업단지','산업입주_대분류']).sum().reset_index()

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
            font_size=18),
            font=dict(
                family="Arial",
                size=13,
                color="#777777"
                ),
            legend=dict(xanchor="right", yanchor="bottom",y=0.7, font_size=10,bgcolor='rgba(0,0,0,0.01)'),
            margin=dict(l=10, r=10, t=30, b=5),
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
    input_df = 분류할 데이터프레임. ['산업단지','산업입주_대분류','매출액_2016','매출액_2017','매출액_2018',
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
            font_size=18),
            font=dict(
                family="Arial",
                size=13,
                color="#777777"
                ),
            legend=dict(xanchor="right", yanchor="bottom",y=0.7, font_size=10,bgcolor='rgba(0,0,0,0.01)'),
            margin=dict(l=10, r=10, t=30, b=5),
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
        meta_tags=[{"name": "viewport", "content": "width=device-width"}])
dash_app2 = Dash(__name__, server=application, url_base_pathname='/dashapp2/',
        meta_tags=[{"name": "viewport", "content": "width=device-width"}])

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

#레이아웃 default style 지정
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview"
)

#레이아웃 설정
dash_app1.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        html.Div(id="output-clientside"),

        #head 작성
        html.Div(

            [   
                html.Div(
                    html.A(
                        html.Button("페이지2", id="-button"),
                        href="/dashapp2/",
                    )
                ),
                    
                #왼쪽상단 로고
                html.Div(
                    [       
                        html.Img(
                            src=dash_app1.get_asset_url("dash-logo.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                #title
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "한국산업단지 ESG 대응",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Monitoring Service", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                #빅리더 홈페이지 링크
                html.Div(
                    [
                        html.A(
                            html.Button("빅리더 AI 아카데미", id="learn-more-button"),
                            href="https://bigleader.net/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        #상단 전국 산업단지 상대분석 그래프 레이아웃
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(figure=Main_map(df),
                                style={'width':400,"height":650,'float':'left'},
                                ),
                         dcc.Graph(figure=Main_graph(df),
                                style={'width':'80%',"height":650,'margin-left':430})
                    ],
                    id="Main_container",
                    className="ten columns"),
            ],
            className="pretty_container twelve columns",
            style={'height':680}
        ),
        #중단 기업 등급별 매출액, 기업 수 분석 
        html.Div(
            [
                #데이터 선택 메뉴(기업규모, EU수출여부, 업종 별)
                html.Div(
                    [
                        html.P("기업 규모별 구분 : \n", className="control_label"),
                        dcc.RadioItems(
                            id="well_status_selector",
                            options=
                            [
                                {"label": "대기업 ", "value": "대기업"},
                                {"label": "중견기업 ", "value": "중견기업"},
                                {"label": "중소기업 ", "value": "중소기업"},
                            ],
                            value="중소기업",
                            className="dcc_control"
                        ),
                        html.P("수출여부 : \n", className="control_label"),
                        dcc.Checklist(
                            ['EU','US'],
                            [None],
                            id="eu_check",
                            className="dcc_control",
                            style={}
                        ),
                        html.P("업종 별 구분 : \n", className="control_label"),
                        dcc.Checklist(
                            industry_list,
                            industry_list,
                            id="well_statuses",
                            className="dcc_control",
                            style={"height":400, "overflow":"auto"}
                        )
                    ],
                    className="pretty_container three columns",
                    id="cross-filter-options",
                    style={'color':'#777777'}
                ),

                #기업 등급별 매출액, 기업 수 그래프, 텍스트
                html.Div(
                    [
                        html.Div(
                            [   
                                #총 수출액 텍스트
                                html.Div(
                                    [
                                        html.H5(id="total_exports"), 
                                        html.P("총 수출액 ( 단위 : $ )",
                                        style={'fontSize': 14})
                                    ],
                                    id="export",
                                    className="mini_container",
                                ),
                                #총 기업수 텍스트
                                html.Div(
                                    [
                                        html.H6(id="total_companies"),
                                         html.P("총 기업 수 ( 단위 : 개 )",
                                         style={'fontSize': 14})
                                    ],
                                    id="company",
                                    className="mini_container",
                                ),
                                #총 종업원 수 텍스트
                                html.Div(
                                    [
                                        html.H6(id="total_employees"),
                                         html.P("총 종업원 수 ( 단위 : 명 )",
                                         style={'fontSize': 14})
                                    ],
                                    id="employee",
                                    className="mini_container",
                                )
                            ],
                            id="info-container",
                            className="row container-display",
                            style={'color':'#777777'}
                        ),
                        #산업단지 분석결과 텍스트
                        html.Div(
                            [
                                html.P("선택하신 조건으로 AI 분석결과", style = {'display':'inline_block','float':'left', 'margin':'5px 10px 0px 30px'}),
                                dcc.Dropdown([1, 2, 3, 4, 5, '전체'], 1, id='dropdown_grade', clearable=False, style = {'display':'inline_block','float':'left', 'width': '70px'}),
                                html.P(children = "등급 산업단지는 -입니다.", id = 'grade_text', style = {'display':'inline_block','float':'left', 'margin':'5px 0px 0px 0px'})
                            ],
                            id="Recommended_text",
                            className="pretty_container",
                        ),
                        #매출액, 기업수 그래프
                        html.Div(
                            [
                                dcc.Graph(id="count_graph")
                            ],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="nine columns",
                ),
            ],
            className="row flex-display",
        ),
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
    df_condition = df_condition[df_condition['산업입주_대분류'].isin(code_value)]

    fig, text = entire_EDA(df_condition, grade)
    
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
    df_condition = df_condition[df_condition['산업입주_대분류'].isin(code_value)]

    data_money=int(df_condition['매출액_2021'].sum())
    data_people=df_condition['종사자수_2021'].sum()
    data_company=df_condition.shape[0]

    return '{:,.0f}'.format(data_money), int(data_company), int(data_people)

# --------------------------------------------------------------------------------------------------------

dash_app2.layout = html.Div(
    [
        html.Div(
            [   
                #왼쪽상단 로고
                html.Div(
                    [       
                        html.Img(
                            src=dash_app2.get_asset_url("dash-logo.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                #title
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "한국산업단지 ESG 대응",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Monitoring Service", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                #빅리더 홈페이지 링크
                html.Div(
                    [
                        html.A(
                            html.Button("빅리더 AI 아카데미", id="learn-more-button"),
                            href="https://bigleader.net/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),

        #상단 산업단지 분석
        html.Div(
            [  
                #산업단지 검색 input창
                html.Div(
                    [
                        dcc.Input(id="search", type="text", placeholder="산업단지 검색", debounce=True, style = {'display':'inline_block','float':'left'})
                    ]
                ),
                #산업단지 분석결과 텍스트
                html.P(children = "산업단지 분석 결과 우선 지원 업종은", style = {'display':'inline_block','float':'left', 'margin':'0px 10px 0px 100px'}),
                html.P(children = "-", id = 'input_text2', style = {'display':'inline_block','float':'left', 'margin':'0px 0px 0px 0px'}),
                html.P(children = "입니다.", style = {'display':'inline_block','float':'left', 'margin':'0px 0px 0px 0px'})
            ],
            className="pretty_container twelve columns",
            id = "input_sandan_container",
            style={'height':70, 'fontSize':'22px' }
        ),
        html.Div(
            [   
                #산업단지 시급성 맵
                html.Div(
                    dcc.Graph(id="individual_graph2",style={"height":400}),
                    className="pretty_container four columns",
                ),
                #산업단지 수출액 비율 파이 그래프
                html.Div(
                    dcc.Graph(id="pie_graph2",figure=sales_pie(df),style={"height":400}),
                    className="pretty_container four columns",

                ),
                #산업단지 수출액 변화추이 그래프
                html.Div(
                    [dcc.Graph(id="bar_graph2",style={"height":400})],
                    className="pretty_container four columns",
                ),
                

            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@dash_app2.callback(
    Output("individual_graph2", "figure"),
    Input('search', 'value'))
def sandan_search(search):
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
    lat = 36.065
    lon = 127.686
    zoom_size = 5.7

    sandan_name, is_search = SandanSearch_df(df_grade_sandan, search)
    df_sandan = Sandan_df(df_grade_sandan, sandan_name)

    #특정 산업단지 검색결과가 존재할 시, 특정 산업단지를 크게 지도에 표시  
    if is_search:
        sandan_location = df_sandan_location[df_sandan_location['name'] == sandan_name]
        zoom_size = 10
        lat = float(sandan_location['latitude'].values[0])
        lon = float(sandan_location['longitude'].values[0])
        
        fig_sandan = px.choropleth_mapbox(df_sandan, 
                        geojson=geo_data_sandan,
                        locations='산업단지',
                        color='산단등급',
                        range_color = [1,5],
                        featureidkey='properties.name',
                        mapbox_style="carto-positron",
                        zoom=zoom_size, center = {"lat": lat, "lon": lon},
                        opacity=0.8)
        text = sandan_name + ' 시급성'
    #특정 산업단지 검색결과가 존재하지 않을 시 , 지도에 전국 산업단지 시급성 분포도를 표시
    else:
        fig_sandan = px.scatter_mapbox(df_sandan_loc,
                                mapbox_style='carto-positron', 
                                lat="latitude", lon="longitude",
                                zoom=zoom_size, center = {"lat": lat, "lon": lon},
                                color='산단등급',
                                size = 'marker_size',
                                size_max=50,
                                opacity=0.3,
                                )
        text = '전국 산업단지 시급성 분포'
    
    fig_sandan.update_layout(
                            title=dict(
                                text=text,
                                x=0.02,
                                y=0.98,
                                font_size=20),
                            font=dict(
                                family="Arial",
                                size=9,
                                color="#777777"
                            ),
                            margin={"r":0,"t":40,"l":0,"b":0},
                            paper_bgcolor='#F9F9F9',
                            plot_bgcolor='#F9F9F9',
                            )

    return fig_sandan


@dash_app2.callback(
    Output('pie_graph2', 'figure'),
    Input('search', 'value'))
def pie(search):
    '''
    Description :
    산업단지별 수출액 비율 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 pie chart를 반환
    '''
    sandan_name, is_search = SandanSearch_df(df, search)
    df_condition = Sandan_df(df, sandan_name)
    if is_search:
        return sales_pie_sandan(df_condition)
    else:
        return sales_pie(df)

@dash_app2.callback(
    Output('bar_graph2', 'figure'),
    Output('input_text2', 'children'),
    Input('search', 'value'))
def ChangeInExport(search):
    '''
    Description :
    산업단지 별 수출액 변화추이 그래프 콜백함수

    Parameters :
    search = 검색창에 입력한 문자열
    
    return :
    Plotly Express의 make_subplots객체(수출액 변화추이 그래프),
    산업단지 업종별 분석결과 텍스트를 반환
    '''
    sandan_name, is_search = SandanSearch_df(df, search)
    df_condition = Sandan_df(df, sandan_name)
    
    if is_search:
        fig_temp, text_upjong= ChangeInExport_industry(df_condition, sandan_name)
        text = text_upjong
        return fig_temp, text  
    else:
        fig_temp = ChangeInExport_sandan(df_condition)
        text = '-'
        return fig_temp, text  


#-----------------------------------------------------------------------------------------------------------------    
#서버 실행
#-----------------------------------------------------------------------------------------------------------------    

if __name__ == "__main__":
    # application.debug = True
    application.run(host='0.0.0.0', port = "5000")

