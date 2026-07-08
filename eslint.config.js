// ESLint flat config (ESLint 9+) — 宽松规则, 仅捕获明显错误, 不强加风格
// (风格交给 Prettier; 这里只做正确性检查)
import globals from 'globals';

export default [
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      'no-undef': 'error',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-cond-assign': 'error',
      'no-constant-condition': 'warn',
      'no-debugger': 'error',
      'no-dupe-keys': 'error',
      'no-empty': 'warn',
      'no-redeclare': 'error',
      'no-unreachable': 'error',
      'no-use-before-define': 'off', // dashboard.js 用函数提升
      'eqeqeq': ['warn', 'smart'],
    },
    ignores: ['**/node_modules/**', '**/venv/**'],
  },
];
