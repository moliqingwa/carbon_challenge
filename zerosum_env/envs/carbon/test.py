from zerosum_env import make

# 构建一个环境
env = make("carbon", debug=True, configuration={
    "actTimeout": 1000,
    "runTimeout": 96000,
    "agentTimeout": 6000,
    "episodeSteps": 5
})

# 选取random agent作为对手
# run 函数将会运行300轮
env.run(["other_agent", "terminal_agent"])

# 渲染对战画面(打开jupyter notebook运行此命令才能看到渲染画面)
print(env.render(mode="json"))
