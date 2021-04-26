const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    main: './report/kb_djornl.js',
    test: './report/test.js',
  },
  output: {
    path: path.resolve(__dirname, 'test_local/workdir/tmp/reports'),
  },
  plugins: [
    new webpack.ProgressPlugin(),
    new HtmlWebpackPlugin({
      chunks: ['main'],
      filename: 'index.html',
      template: './report/index.html',
    }),
    new HtmlWebpackPlugin({
      chunks: ['test'],
      filename: 'tests.html',
      title: 'kb_djornl tests',
    }),
  ],

  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          {
            loader: 'style-loader',
          },
          {
            loader: 'css-loader',
            options: {
              sourceMap: true,
            },
          },
        ],
      },
      {
        test: /tests\.js$/,
        use: 'mocha-loader',
        exclude: /node_modules/,
      },
      {
        exclude: /node_modules/,
        include: [path.resolve(__dirname, 'report')],
        loader: 'babel-loader',
        test: /\.js$/,
      },
    ],
  },
  devtool: 'source-map',
  devServer: {
    contentBase: path.join(__dirname, 'test_local/workdir/tmp/reports'),
    host: 'localhost',
  },
};
