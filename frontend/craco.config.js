const { addAfterLoader, loaderByName } = require('@craco/craco');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Find all postcss-loader instances and add @tailwindcss/postcss plugin
      const oneOfRules = webpackConfig.module.rules.find(rule => rule.oneOf)?.oneOf || [];

      oneOfRules.forEach(rule => {
        if (!rule.use) return;
        const uses = Array.isArray(rule.use) ? rule.use : [rule.use];

        uses.forEach(use => {
          if (use.loader && use.loader.includes('postcss-loader')) {
            const postcssOptions = use.options?.postcssOptions;
            if (postcssOptions) {
              const existingPlugins = postcssOptions.plugins || [];
              postcssOptions.plugins = [
                require('@tailwindcss/postcss'),
                ...existingPlugins,
              ];
            }
          }
        });
      });

      return webpackConfig;
    },
  },
};
