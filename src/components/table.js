import React, {useState, useEffect} from 'react';
import { Col, message, Row, Table, Card } from 'antd';
import MyAvatar from './avatar';
import 'antd/dist/antd.css';
import QAmiss from './QA2';
import TablePanel from './TablePanel';
import ArrowRender from './arrow';
import PointRender from './changeNumber';
import RoundFloat from './resolveFloat';
import Trophy from './rankTrophy';
import expandObject from '../util/expandObject';
import './table.css'

const titleDir = {
    company: 'Company',
    repo: 'Repository',
    actor: 'ID',
}
const activityDataIndexDir = {
    company: 'name',
    repo: 'name',
    actor: 'name',
}
const openRankDataIndexDir = {
    company: 'name',
    repo: 'name',
    actor: 'name',
}
const activityColumns = (object)=>[
    {
        title: 'rank',
        dataIndex: 'rank',
        width: '5%',
        align: 'center',
        render: Trophy,
        fixed: 'left',
    },
    ...object=='actor'?
    [{
        title: 'Avatar',
        dataIndex: 'id',
        width: '5%',
        align: 'center',
        render: MyAvatar,
        fixed: 'left',
    }]:[],
    {
        title: '',
        dataIndex: 'rankDelta',
        render: ArrowRender,
        align:'left',
        width: '5%',
        fixed: 'left',
    },
    {
        title: titleDir[object],
        dataIndex: activityDataIndexDir[object],
        align:'center',
        width: '20%',
        render: function (text, row, index) {
            if (titleDir[object] !== 'Company') {
                return (
                    <a href={"https://github.com/"+text} target="_blank">{text}</a>
                )
            } else {
               return text
            }
        }
    },
    {
        title: 'Activity',
        dataIndex: 'value',
        align:'right',
        width: '20%',
    },
    {
        title:'',
        dataIndex:'valueDelta',
        width:'10%',
        align:'left',
        render: PointRender,
    }
];
const activityDetailColumns = (object)=>[
    {
        title: 'Rank',
        dataIndex: 'rank',
        width: '5%',
        align: 'center',
        render: Trophy,
        fixed: 'left',
    },
    ...object=='actor'?
    [{
        title: 'Avatar',
        dataIndex: 'id',
        width: '5%',
        align: 'center',
        render: MyAvatar,
        fixed: 'left',
    }]:[],
    {
        title: '',
        dataIndex: 'rankDelta',
        render: ArrowRender,
        align:'left',
        width: '5%',
        fixed: 'left',
    },
    {
        title: titleDir[object],
        dataIndex: activityDataIndexDir[object],
        align:'center',
        width: '5%',
        render: function (text, row, index) {
            if (titleDir[object] !== 'Company') {
                return (
                    <a href={"https://github.com/"+text} target="_blank">{text}</a>
                )
            } else {
               return text
            }
        }
    },
    {
        title: 'Activity',
        dataIndex: 'value',
        align:'right',
        width: '10%',
    },
    {
        title:'',
        dataIndex:'valueDelta',
        width:'10%',
        align:'left',
        render: PointRender,
    },
    {
        title:<p>Issue<br/>Comments</p>,
        dataIndex:'issue_comment',
        width:'10%',
        align:'center',
    },
    {
        title:<p>Open<br/>Issues</p>,
        dataIndex:'open_issue',
        width:'10%',
        align:'center',
    },
    {
        title:<p>Open<br/>Pulls</p>,
        dataIndex:'open_pull',
        width:'10%',
        align:'center',
    },
    {
        title:<p>Merge<br/>Pulls</p>,
        dataIndex:'merged_pull',
        width:'10%',
        align:'center',
    },
    {
        title:<p>PR<br/>Reviews</p>,
        dataIndex:'review_comment',
        width:'10%',
        align:'center',
    },
];
const open_rankColumns = (object)=>[
    {
        title: 'Rank',
        dataIndex: 'rank',
        width: '5%',
        render: Trophy,
        align: 'center',
        fixed: 'left',
    },
    ...object=='actor'?
    [{
        title: 'Avatar',
        dataIndex: 'id',
        width: '5%',
        align: 'center',
        render: MyAvatar,
        fixed: 'left',
    }]:[],
    {
        title: '',
        dataIndex: 'rankDelta',
        render: ArrowRender,
        align:'left',
        width: '5%',
        fixed: 'left',
    },
    {
        title: titleDir[object],
        dataIndex: openRankDataIndexDir[object],
        width: '5%',
        align:'center',
        render: function (text, row, index) {
            if (titleDir[object] !== 'Company') {
                return (
                    <a href={"https://github.com/"+text} target="_blank">{text}</a>
                )
            } else {
               return text
            }
        }
    },
    {
        title: 'Influence',
        dataIndex: 'value',
        width: '20%',
        align:'right',
        render:(text, row, index)=>{
            return RoundFloat(text)
        }
    },
    {
        title:'',
        dataIndex:'valueDelta',
        width:'10%',
        align: 'left',
        render: (text, row, index)=>{
            text = RoundFloat(text)
            return PointRender(text, row, index)
        },
    }
];
const solveDate = (year,month)=>{
    if(year===null&&month===null){
        return "not found";
    }
    if(month===null){
        return year+"年";
    }
    return year+"年"+(month+1)+"月";
}
function DateTitle(props){
    return (
        <h1>{solveDate(props.year,props.month)}</h1>
    );
}

function MyTable(props){
    const [state, setState] = useState({
        object:'company',
        index:'activity',
        region:'chinese',
        columns: activityColumns('company'),
        showDetail:false,
        hasDetail:true,
        data: [],
        showSize: 25,
        loading: true,
        url: '',// base + index + object + region + yearmonth + .json
        base: "https://xlab-open-source.oss-cn-beijing.aliyuncs.com/open_leaderboard/",
        year: null,// 字符串格式
        month: null,// 整数格式，0表示1月，1表示2月..., null for year type time
        type: 'month',
    });

    // 请求一次数据更新表格。如果还没读取好配置文件则不请求数据。
    useEffect(()=>{
        if(props.year==null && props.month==null){
            console.log('the first loading');
            return;
        }
        updateDate({
            year: String(props.year),
            month:props.month
        });
    },[props]);

    const expandData = ()=>{
        setState({
            ...state,
            showSize: state.showSize + 25,
        })
    }
    
    const updateDate = (newstate) => {
        console.log('table update',newstate);
        // 先获取原先的表格属性
        let { base, object, index, region, month, year, columns, showDetail, hasDetail, type } = state;
        // 然后把表格改为加载中的状态
        setState({...state,...newstate,loading: true});
        // 如果 newstate 有对应的属性，则进行更新
        if(newstate.hasOwnProperty('object')) object = newstate.object;
        if(newstate.hasOwnProperty('index')) index = newstate.index;
        if(newstate.hasOwnProperty('region')) region = newstate.region;
        if(newstate.hasOwnProperty('month')) month = newstate.month;
        if(newstate.hasOwnProperty('year')) year = newstate.year;
        if(newstate.hasOwnProperty('showDetail')) showDetail = newstate.showDetail;
        if(newstate.hasOwnProperty('type')) type = newstate.type;
        // 根据 index 和 showDetail 改变表格的 columns 格式
        if(index=='activity'){
            columns = activityColumns(object);
            hasDetail = true;
        }
        if(index=='activity' && showDetail == true){
            columns = activityDetailColumns(object)
            hasDetail =  true;
        }
        if(index=='open_rank'){
            columns = open_rankColumns(object);
            hasDetail = false;
            showDetail = false;
        }
        // 如果是年份数据，则把 month 置为 null。
        // TODO：待验证，如果从年份数据切换到月份数据，似乎会自动回到原来 month 值？
        if(type == 'year'){
            month = null;
        }
        // 以当前的属性构造请求 url
        let url = base + index + '/' + object + '/' + region + '/';
        if(month===null){
            url += year + '.json';
        }
        else{
            url += year + (1+month)+ '.json';
        }
        console.log(url);
        // fetch 异步请求
        fetch(url)
        .then(res => {
            // Todo：最好的情况是在日期选择器中，只显示可以查询的日期，
            if(res.status==404){
                message.warning('No relevant results yet');
                return '';
            }
            return res.json();
        })
        .then(data => {
            data = data.data;
            let dataSource = [];
            // 预处理数据，对新上榜单数据进行特殊标记处理
            data.map((obj)=>{
                obj = expandObject(obj);
                if(obj.rankDelta==0 && obj.value == obj.valueDelta){
                    obj.rankDelta = -10000000;
                    obj.valueDelta = 0;
                }
                dataSource.push(obj);
            });
            console.log(dataSource);

            // 更新属性和表格数据
            setState({
                ...state,
                ...newstate,
                loading: false,
                columns: columns,
                showDetail: showDetail,
                hasDetail: hasDetail,
                data: dataSource,
            });
        })
        .catch(err => {
            console.log('hi!' + err);
            setState({
                ...state,
                ...newstate,
                loading: false,
                columns:columns,
                data: [],
            });
        })
    };

    const {t} = props;
    const {object, index, region, data, columns, loading, showSize, showDetail, hasDetail, month, year, type} = state;
    return (
        <div className='table'>
            <div className='table-content'>
                <Card style={{
                    width:'100%',
                    background: '#FFFFFF',
                    boxShadow:'0px 15px 20px 15px #F7F7FF',
                }}>
                    <TablePanel 
                        type={type} 
                        setState={updateDate} 
                        object={object} 
                        index={index} 
                        region={region} 
                        hasDetail={hasDetail} 
                        showDetail={showDetail} 
                        month={month} year={year}
                    />
                    <Table
                        // Todo
                        // scroll={{ x: 1500, y: 300 }}
                        columns={columns}
                        rowKey={record => record.rank}
                        dataSource={data.slice(0,Math.min(showSize,data.length))}
                        pagination={false}
                        loading={loading}
                        scroll={{x:'max-content'}}
                    />
                    <Row style={{marginTop:'10px'}} >
                        <Col span={12}>
                            <Row justify='start'>
                                <Col>
                                    {  
                                        showSize<data.length?
                                        <a style={{
                                            color:'#FFCC19',
                                            fontSize:'18px',}}
                                            onClick={expandData}>
                                                {t('showMore')+'>>'}
                                        </a>:
                                        <span style={{
                                            color:'gray',
                                            fontSize:'18px',}}>
                                            {t('noMore')}
                                        </span>
                                    }
                                    
                                </Col>
                            </Row>
                        </Col>
                        <Col span={12}>
                            <Row justify='end'>
                                <Col>
                                    <QAmiss />
                                </Col>
                            </Row>
                        </Col>
                    </Row>
                </Card>
            </div>
        </div> 
    )
}

export default MyTable;