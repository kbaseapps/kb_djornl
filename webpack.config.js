const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: './report/kb_djornl.js',
  output: {
    path: path.resolve(__dirname, 'test_local/workdir/tmp/reports'),
  },

  plugins: [
    new webpack.ProgressPlugin(),
    new HtmlWebpackPlugin({
      filename: 'index.html',
      template: './report/index.html',
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
        exclude: /node_modules/,
        include: [path.resolve(__dirname, 'report')],
        loader: 'babel-loader',
        test: /\.js$/,
      },
    ],
  },

  devServer: {
    contentBase: path.join(__dirname, 'test_local/workdir/tmp/reports'),
    host: 'localhost',
    open: true,
  },
};
