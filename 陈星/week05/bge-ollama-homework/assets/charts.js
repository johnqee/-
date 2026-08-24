/* 作业报告图表：bge 检索余弦相似度对比 */
(function () {
  'use strict';

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name);
    return (v && v.trim()) || fallback;
  }

  var el = document.getElementById('chart-sim');
  if (!el) return;

  var chart = echarts.init(el, null, { renderer: 'svg' });

  var accent = cssVar('--accent', '#2563eb');
  var accent2 = cssVar('--accent2', '#0d9488');
  var ink = cssVar('--ink', '#1b2437');
  var muted = cssVar('--muted', '#5b6b84');
  var rule = cssVar('--rule', '#e3e9f2');

  var rows = [
    { label: '我今天心情很不错', score: 0.6896 },
    { label: '我喜欢深度学习', score: 0.3750 },
    { label: '我喜欢机器学习', score: 0.3489 }
  ];

  chart.setOption({
    animation: false,
    grid: { left: 24, right: 48, top: 12, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      confine: true,
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: rule,
      textStyle: { color: ink, fontSize: 13 },
      formatter: function (params) {
        var p = params[0];
        return '<b>' + p.name + '</b><br/>相似度：' + p.value.toFixed(4);
      }
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 0.8,
      axisLabel: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: rows.map(function (r) { return r.label; }),
      axisLabel: { color: ink, fontSize: 13 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    series: [
      {
        name: '余弦相似度',
        type: 'bar',
        data: rows.map(function (r, i) {
          return {
            value: r.score,
            itemStyle: {
              color: i === 0 ? accent : '#c3d2f3',
              borderRadius: i === 0 ? [0, 6, 6, 0] : [0, 4, 4, 0]
            },
            label: {
              show: true,
              position: 'right',
              color: i === 0 ? accent2 : muted,
              fontWeight: i === 0 ? 700 : 400,
              fontSize: 13,
              formatter: function (p) { return p.value.toFixed(4); }
            }
          };
        }),
        barWidth: 26,
        showBackground: true,
        backgroundStyle: { color: cssVar('--bg2', '#ffffff'), borderColor: rule, borderWidth: 1, borderRadius: 6 }
      }
    ]
  });

  window.addEventListener('resize', function () { chart.resize(); });
})();
