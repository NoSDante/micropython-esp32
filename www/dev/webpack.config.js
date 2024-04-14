const path = require('path');
const TerserPlugin = require("terser-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");


module.exports = {
    mode: 'production',
    //devtool: "source-map",
    devtool: "eval",


    entry: {
        script: './src/index.js',
        style: './src/css/style.css'
    },

    output: {
        path: path.resolve(__dirname, 'build'),
        filename: "js/[name].js",
    },


    optimization: {
        minimize: true,
        minimizer: [
            new TerserPlugin({
                terserOptions: {
                    compress: true,
                    format: {
                        comments: false,
                    },
                },
                extractComments: true,
                test: /\.js(\?.*)?$/i
            }, ),
        ],
    },

    module: {
        rules: [{
                test: /\.css$/i,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },
            {
                test: /\.html$/,
                use: 'raw-loader'
            }
        ],

    },

    plugins: [
        new CleanWebpackPlugin(),
        new MiniCssExtractPlugin({ filename: "css/[name].css" }),
        new HtmlWebpackPlugin({
            title: 'ESP32 Webinterface',
            favicon: './src/favicon.ico',
            template: './src/index.html',
            filename: 'index.html'
        }),
        new CopyPlugin({
            patterns: [{
                    from: path.resolve(__dirname, 'src/img'),
                    to: "img"
                },
                // {
                //     from: path.resolve(__dirname, 'src/favicon.ico'),
                //     to: "[name].ico"
                // },
                // js: node_modules
                {
                    from: path.resolve(__dirname, 'node_modules/jquery/dist/jquery.min.js'),
                    to: "dist/js/[name].js",
                },
                {
                    from: path.resolve(__dirname, 'node_modules/@popperjs/core/dist/umd/popper.min.js'),
                    to: "dist/js/[name].js",
                },
                {
                    from: path.resolve(__dirname, 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js'),
                    to: "dist/js/[name].js",
                },
                {
                    from: path.resolve(__dirname, 'node_modules/@fortawesome/fontawesome-free/js/fontawesome.min.js'),
                    to: "dist/js/[name].js",
                },
                {
                    from: path.resolve(__dirname, 'src/js/solid.slim.min.js'),
                    to: "js/[name].js",
                },
                {
                    from: path.resolve(__dirname, 'node_modules/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.concat.min.js'),
                    to: "dist/js/[name].js",
                },
                // css: node_modules
                {
                    from: path.resolve(__dirname, 'node_modules/bootstrap/dist/css/bootstrap.min.css'),
                    to: "dist/css/[name].css",
                },
                {
                    from: path.resolve(__dirname, 'node_modules/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.css'),
                    to: "dist/css/[name].css",
                }
            ],
            options: {
                concurrency: 100,
            },
        }),
    ]
}