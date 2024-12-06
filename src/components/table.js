import React, { useState, useEffect } from 'react';
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
import { t } from 'i18next';
import './table.css';

const activityColumns = (object, boardType, t_month) => [
  {
    title: t('rank'),
    dataIndex: 'rank',
    width: '5%',
    align: 'center',
    render: Trophy,
    fixed: 'left',
  },
  ...(object == 'actor'
    ? [
        {
          title: t('avatar'),
          dataIndex: 'id',
          width: '5%',
          align: 'center',
          render: MyAvatar,
          fixed: 'left',
        },
      ]
    : []),
  {
    title: '',
    dataIndex: 'rankDelta',
    render: ArrowRender,
    align: 'left',
    width: '5%',
    fixed: 'left',
  },
  {
    title: t(object),
    dataIndex: 'name',
    align: 'center',
    width: '20%',
    render: function (text, row, index) {
      if (object !== 'company') {
        return (
          <a
            href={'https://github.com/' + text}
            target="_blank"
            rel="noreferrer"
          >
            {text}
          </a>
        );
      } else {
        return text;
      }
    },
  },
  ...(object != 'repo' || boardType == 'region'
    ? [
        {
          title: t('insight_board'),
          dataIndex: 'name',
          align: 'center',
          width: '10%',
          render: function (text, row, index) {
            return dashboard(text, index, t_month, object);
          },
        },
      ]
    : []),
  {
    title: t('activity'),
    dataIndex: 'value',
    align: 'right',
    width: '20%',
  },
  {
    title: '',
    dataIndex: 'valueDelta',
    width: '10%',
    align: 'left',
    render: PointRender,
  },
];
const activityDetailColumns = (object, boardType, t_month) => [
  {
    title: t('rank'),
    dataIndex: 'rank',
    width: '5%',
    align: 'center',
    render: Trophy,
    fixed: 'left',
  },
  ...(object == 'actor'
    ? [
        {
          title: t('avatar'),
          dataIndex: 'id',
          width: '5%',
          align: 'center',
          render: MyAvatar,
          fixed: 'left',
        },
      ]
    : []),
  {
    title: '',
    dataIndex: 'rankDelta',
    render: ArrowRender,
    align: 'left',
    width: '5%',
    fixed: 'left',
  },
  {
    title: t(object),
    dataIndex: 'name',
    align: 'center',
    width: '5%',
    render: function (text, row, index) {
      if (object !== 'company') {
        return (
          <a
            href={'https://github.com/' + text}
            target="_blank"
            rel="noreferrer"
          >
            {text}
          </a>
        );
      } else {
        return text;
      }
    },
  },
  ...(object != 'repo' || boardType == 'region'
    ? [
        {
          title: t('insight_board'),
          dataIndex: 'name',
          align: 'center',
          width: '10%',
          render: function (text, row, index) {
            return dashboard(text, index, t_month, object);
          },
        },
      ]
    : []),
  {
    title: t('activity'),
    dataIndex: 'value',
    align: 'center',
    width: '10%',
  },
  {
    title: '',
    dataIndex: 'valueDelta',
    width: '10%',
    align: 'left',
    render: PointRender,
  },
  {
    title: t('issue_comments'),
    dataIndex: 'issue_comment',
    width: '10%',
    align: 'center',
  },
  {
    title: t('open_issues'),
    dataIndex: 'open_issue',
    width: '10%',
    align: 'center',
  },
  {
    title: t('open_pulls'),
    dataIndex: 'open_pull',
    width: '10%',
    align: 'center',
  },
  {
    title: t('merge_pulls'),
    dataIndex: 'merged_pull',
    width: '10%',
    align: 'center',
  },
  {
    title: t('pr_reviews'),
    dataIndex: 'review_comment',
    width: '10%',
    align: 'center',
  },
];
const open_rankColumns = (object, boardType, t_month) => [
  {
    title: t('rank'),
    dataIndex: 'rank',
    width: '5%',
    render: Trophy,
    align: 'center',
    fixed: 'left',
  },
  ...(object == 'actor'
    ? [
        {
          title: t('avatar'),
          dataIndex: 'id',
          width: '5%',
          align: 'center',
          render: MyAvatar,
          fixed: 'left',
        },
      ]
    : []),
  {
    title: '',
    dataIndex: 'rankDelta',
    render: ArrowRender,
    align: 'left',
    width: '5%',
    fixed: 'left',
  },
  {
    title: t(object),
    dataIndex: 'name',
    width: '20%',
    align: 'center',
    render: function (text) {
      if (object !== 'company') {
        return (
          <a
            href={'https://github.com/' + text}
            target="_blank"
            rel="noreferrer"
          >
            {text}
          </a>
        );
      } else {
        return text;
      }
    },
  },
  ...(object != 'repo' || boardType == 'region'
    ? [
        {
          title: t('insight_board'),
          dataIndex: 'name',
          align: 'center',
          width: '10%',
          render: function (text, row, index) {
            return dashboard(text, index, t_month, object);
          },
        },
      ]
    : []),
  {
    title: t('influence'),
    dataIndex: 'value',
    width: '20%',
    align: 'right',
    render: (text, row, index) => {
      return RoundFloat(text);
    },
  },
  {
    title: '',
    dataIndex: 'valueDelta',
    width: '10%',
    align: 'left',
    render: (text, row, index) => {
      text = RoundFloat(text);
      return PointRender(text, row, index);
    },
  },
];
const solveDate = (year, month) => {
  if (year === null && month === null) {
    return 'not found';
  }
  if (month === null) {
    return year + '年';
  }
  return year + '年' + (month + 1) + '月';
};

function dashboard(text, index, t_month, object) {
  if (object === 'repo' && index < 300) {
    let [org_name, repo_name] = text.split('/');
    const t_month_copy = t_month + ' ' + '00:00:00';
    let params = {
      org_name,
      repo_name,
      t_month_copy,
      t_month,
      org_repo: `${org_name}/${repo_name}`,
    };
    return (
      <a
        href={
          'https://dataease.x-lab.info/link/v5wLKVcF?attachParams=' +
          btoa(JSON.stringify(params))
        }
        target="_blank"
        rel="noreferrer"
      >
        <img
          alt="dashboard"
          src="/pics/dashboard.png"
          style={{ height: '20px', width: '20px' }}
        />
      </a>
    );
  } else if (object === 'company' && index < 130) {
    console.log('text', text);
    let params = {
      communityName: text,
    };
    let jsonString = JSON.stringify(params);
    return (
      <a
        href={
          'https://dataease.x-lab.info/link/9X2VqE9V?attachParams=' +
          btoa(jsonString)
        }
        target="_blank"
        rel="noreferrer"
      >
        <img
          alt="dashboard"
          src="/pics/dashboard.png"
          style={{ height: '20px', width: '20px' }}
        />
      </a>
    );
  } else if (object === 'actor' && index < 300) {
    // 在这里添加 'actor' 的特定逻辑\

    let params = {
      actor_login: text,
    };
    let jsonString = JSON.stringify(params);
    console.log(
      'actor_login_text',
      'https://dataease.x-lab.info/link/SToKUlSU?attachParams=' +
        btoa(jsonString)
    );
    return (
      <a
        href={
          'https://dataease.x-lab.info/link/SToKUlSU?attachParams=' +
          btoa(jsonString)
        }
        target="_blank"
        rel="noreferrer"
      >
        <img
          alt="dashboard"
          src="/pics/dashboard.png"
          style={{ height: '20px', width: '20px' }}
        />
      </a>
    );
  }
  return null;
}

function DateTitle(props) {
  return <h1>{solveDate(props.year, props.month)}</h1>;
}

function MyTable(props) {
  const [state, setState] = useState({
    object: 'company',
    index: 'activity',
    region: 'chinese',
    showDetail: false,
    hasDetail: true,
    data: [],
    showSize: 25,
    loading: true,
    url: '', // base + index + object + region + yearmonth + .json
    base: 'https://oss.x-lab.info/open_leaderboard/',
    year: null, // 字符串格式
    month: null, // 整数格式，0表示1月，1表示2月..., null for year type time
    type: 'month',
    search: null,
    boardType: 'region',
    purpose: 'academic',
    appDomain: 'application_software',
    llm: 'Application_Development_Framework',
  });

  // 请求一次数据更新表格。如果还没读取好配置文件则不请求数据。
  useEffect(() => {
    if (props.year == null && props.month == null) {
      console.log('the first loading');
      return;
    }
    updateDate({
      year: String(props.year),
      month: props.month,
    });
  }, [props]);

  const updateDate = (newstate) => {
    console.log('table update', newstate);
    // 先获取原先的表格属性
    let {
      base,
      object,
      index,
      region,
      month,
      year,
      columns,
      showDetail,
      hasDetail,
      type,
      search,
      boardType,
      purpose,
      appDomain,
      llm,
    } = state;
    // 然后把表格改为加载中的状态
    setState({ ...state, ...newstate, loading: true });
    // 如果 newstate 有对应的属性，则进行更新
    if (newstate.hasOwnProperty('object')) object = newstate.object;
    if (newstate.hasOwnProperty('index')) index = newstate.index;
    if (newstate.hasOwnProperty('region')) region = newstate.region;
    if (newstate.hasOwnProperty('month')) month = newstate.month;
    if (newstate.hasOwnProperty('year')) year = newstate.year;
    if (newstate.hasOwnProperty('showDetail')) showDetail = newstate.showDetail;
    if (newstate.hasOwnProperty('type')) type = newstate.type;
    if (newstate.hasOwnProperty('search')) search = newstate.search;
    if (newstate.hasOwnProperty('boardType')) boardType = newstate.boardType;
    if (newstate.hasOwnProperty('purpose')) purpose = newstate.purpose;
    if (newstate.hasOwnProperty('appDomain')) appDomain = newstate.appDomain;
    if (newstate.hasOwnProperty('llm')) llm = newstate.llm;

    //获取数据大屏的‘t_month’参数
    let myyear = newstate.year == null ? state.year : newstate.year;
    let mymonth = newstate.month == null ? state.month : newstate.month;

    mymonth = ('' + (1 + mymonth)).padStart(2, '0');
    let t_month = `${myyear}-${mymonth}-01`;

    // 根据 index 和 showDetail 改变表格的 columns 格式
    if (index == 'activity') {
      columns = activityColumns(object, boardType, t_month);
      hasDetail = true;
    }
    if (index == 'activity' && showDetail == true) {
      columns = activityDetailColumns(object, boardType, t_month);
      hasDetail = true;
    }
    if (index == 'open_rank') {
      columns = open_rankColumns(object, boardType, t_month);
      hasDetail = false;
      showDetail = false;
    }
    // 如果是年份数据，则把 month 置为 null。
    // TODO：待验证，如果从年份数据切换到月份数据，似乎会自动回到原来 month 值？
    if (type == 'year') {
      month = null;
    }

    let url = base + index + '/' + object;
    // 以当前的属性构造请求 url
    if (object != 'repo' || boardType == 'region') {
      url = url + '/' + region + '/';
    } else {
      if (boardType == 'appDomain')
        url = url + '/' + 'application_domain' + '/' + appDomain + '/';
      else if (boardType == 'llm') url = url + '/' + 'LLM' + '/' + llm + '/';
      else if (boardType == 'purpose')
        url = url + '/' + 'purpose' + '/' + purpose + '/';
    }

    if (month === null) {
      url += year + '.json';
    } else {
      url += year + (1 + month) + '.json';
    }
    console.log(url);
    // fetch 异步请求
    fetch(url)
      .then((res) => {
        // Todo：最好的情况是在日期选择器中，只显示可以查询的日期，
        if (res.status == 404) {
          message.warning(t('no_result'));
          return '';
        }
        return res.json();
      })
      .then((data) => {
        data = data.data;
        let dataSource = [];
        // 预处理数据，对新上榜单数据进行特殊标记处理
        data.map((obj) => {
          obj = expandObject(obj);
          if (obj.rankDelta == 0 && obj.value == obj.valueDelta) {
            obj.rankDelta = -10000000;
            obj.valueDelta = 0;
          }
          dataSource.push(obj);
        });
        console.log(dataSource);

        //搜索特定数据
        let queryData;
        if (search) {
          queryData = dataSource.filter((dataSource) => {
            let reg = new RegExp(search.trim(), 'i');
            return reg.test(dataSource.name);
          });
          if (queryData.length == 0) {
            message.warning(t('no_result'));
          } else {
            dataSource = queryData;
          }
        }

        // 更新属性和表格数据
        setState({
          ...state,
          ...newstate,
          loading: false,
          columns: columns,
          showDetail: showDetail,
          hasDetail: hasDetail,
          data: dataSource,
          region: region,
          boardType: boardType,
          purpose: purpose,
          appDomain: appDomain,
          llm: llm,
        });
      })
      .catch((err) => {
        console.log('hi!' + err);
        setState({
          ...state,
          ...newstate,
          loading: false,
          columns: columns,
          data: [],
        });
      });
  };
  const {
    object,
    index,
    region,
    data,
    columns,
    loading,
    showSize,
    showDetail,
    hasDetail,
    month,
    year,
    type,
    boardType,
    purpose,
    appDomain,
    llm,
  } = state;
  return (
    <div className="table">
      <div className="table-content">
        <Card
          style={{
            width: '100%',
            background: '#FFFFFF',
            boxShadow: '0px 15px 20px 15px #F7F7FF',
          }}
        >
          <TablePanel
            type={type}
            setState={updateDate}
            object={object}
            index={index}
            region={region}
            hasDetail={hasDetail}
            showDetail={showDetail}
            month={month}
            year={year}
            boardType={boardType}
            purpose={purpose}
            appDomain={appDomain}
            llm={llm}
          />
          <Table
            // Todo
            // scroll={{ x: 1500, y: 300 }}
            columns={columns}
            rowKey={(record) => record.rank}
            dataSource={data}
            pagination={{ position: ['bottomRight'], pageSize: showSize }}
            loading={loading}
            scroll={{ x: 'max-content' }}
          />
          <Row style={{ marginTop: '10px' }}>
            <Col span={24}>
              <Row justify="end">
                <Col>
                  <QAmiss />
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      </div>
    </div>
  );
}

export default MyTable;
