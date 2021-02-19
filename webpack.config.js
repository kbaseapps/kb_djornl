const path = require('path');
const webpack = require('webpack');

module.exports = {
  mode: 'development',
  entry: './report/kb_djornl.js',
  output: {
    path: path.resolve(__dirname, 'test_local/workdir/tmp/reports'),
  },

  plugins: [new webpack.ProgressPlugin()],

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
