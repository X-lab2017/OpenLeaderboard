import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

// 图表预留空位，保证数据完整渲染
function yAxisMin(value) {
  return value.min * 0.92;
}
function yAxisMax(value) {
  return value.max * 1.08;
}

const Trend = (trendData) => {
  const chartRef = useRef(null);
  let lineColor =
    trendData[trendData.length - 1] > trendData[0] ? '#FA4444' : '#05B169';
  useEffect(() => {
    const chartDom = chartRef.current;
    const myChart = echarts.init(chartDom, null, { width: 240, height: 60 });

    const option = {
      xAxis: {
        type: 'category',
        data: [],
        show: false,
      },
      yAxis: {
        type: 'value',
        show: false,
        min: yAxisMin,
        max: yAxisMax,
      },
      series: [
        {
          data: trendData,
          type: 'line',
          smooth: false,
          lineStyle: {
            color: lineColor,
          },
          symbol: 'none',
        },
      ],
    };

    myChart.setOption(option);

    return () => {
      myChart.dispose(); // 销毁图表实例
    };
  }, []);

  return <div ref={chartRef} style={{ width: '100%', height: '60px' }} />;
};

export default Trend;
