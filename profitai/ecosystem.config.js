module.exports = {
    apps: [{
      name: 'profitai',
      script: 'manage.py',
      args: 'runserver 0.0.0.0:8000',
      interpreter: 'python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    }],
  };
