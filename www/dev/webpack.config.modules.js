const path = require('path');
const TerserPlugin = require("terser-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
    mode: 'production',
    //devtool: "source-map",
    devtool: "eval",

    // entry: {
    //     app: ['./src/script.js', './src/index.js']
    //         //app: ['./src/script.js']
    // },

    entry: {
        //bundle: './src/index.js',
        //styles: './src/styles.js',
        script: './src/script.js',
        style: './src/style.css',

    },

    output: {
        path: path.resolve(__dirname, 'build'),
        filename: "js/[name].js"
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
        }, ],
    },

    plugins: [
        new MiniCssExtractPlugin({ filename: "css/[name].css" }),
        new CopyPlugin({
            patterns: [
                // js: node_modules
                {
                    from: path.resolve(__dirname, './node_modules/jquery/dist/jquery.min.js'),
                    to: "dist/js/v1.js"
                },
                {
                    from: path.resolve(__dirname, './node_modules/@popperjs/core/dist/umd/popper.min.js'),
                    to: "dist/js/v12.js",
                },
                {
                    from: path.resolve(__dirname, './node_modules/bootstrap/dist/js/bootstrap.bundle.min.js'),
                    to: "dist/js/v123.js"
                },
                {
                    from: path.resolve(__dirname, './node_modules/@fortawesome/fontawesome-free/js/fontawesome.min.js'),
                    to: "dist/js/asd.js"
                },
                {
                    from: path.resolve(__dirname, './node_modules/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.concat.min.js'),
                    to: "dist/js/v1234.js"
                },
                // css: node_modules
                {
                    from: path.resolve(__dirname, './node_modules/bootstrap/dist/css/bootstrap.min.css'),
                    to: "dist/css/v12345.js"
                },
                {
                    from: path.resolve(__dirname, './node_modules/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.concat.min.css'),
                    to: "dist/css/v123456.js"
                }
            ],
            options: {
                concurrency: 100,
            },
        }),
    ]
}