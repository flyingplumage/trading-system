const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = function override(config, env) {
  // 生产环境添加打包分析
  if (env === 'production') {
    config.plugins.push(
      new BundleAnalyzerPlugin({
        analyzerMode: 'static', // 生成静态 HTML 报告
        reportFilename: 'bundle-report.html', // 报告文件名
        openAnalyzer: false, // 不自动打开浏览器
        generateStatsFile: true, // 生成 stats.json
        statsFilename: 'bundle-stats.json',
      })
    );
  }
  
  return config;
};
