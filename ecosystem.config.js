module.exports = {
  apps: [
    {
      name: "history-backend",
      script: "python",
      args: "main.py",
      cwd: "./backend",
      interpreter: "python"
    },
    {
      name: "history-frontend",
      script: "npm",
      args: "run dev",
      cwd: "./frontend"
    }
  ]
};