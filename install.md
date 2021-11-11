# Carbon Challenge

### python版本 : 3.9

### 先安装requirements.txt中的所有依赖:

[flask, gym, ipython, jsonschema, numpy, requests, wheel]

``pip install -r requirements.txt -i https://mirror.baidu.com/pypi/simple``
## 运行方式:
若本地pyhon默认2.7, 可用python3运行
### 本地运行命令：

``python -m zerosum_env.main run --environment carbon --agents random random --display html --out test.html``

### http-server模式运行命令:

``python -m zerosum_env.main http-server``

默认端口 127.0.0.1:8000

可以访问:

http://127.0.0.1:8000/?action=run&environment=carbon&display=html&agents[]=random&agents[]=random

## jupyter-notebook 运行及训练

### MAC or Linux 用户
执行 setupAndInstall.sh


打开 jupyter-notebook
```python
from zerosum_env import make
env = make("carbon")

# 运行例子
env.run(["random", "random"])

# 训练例子
trainer = env.train([None, "random"])
obs = trainer.reset()
for _ in range(100):
    env.render()
    action = [{}, {}] # 给出智能体的动作
    obs, reward, done, info = trainer.step(action)
    if done:
        obs = trainer.reset()

# 评估例子
from zerosum_env import evaluate

def agent():
  return {}
# Which agents to run repeatedly.  Same as env.run(agents)
agents = ["random", agent]

# How many times to run them.
num_episodes = 2

rewards, jsons, htmls, errors = evaluate("carbon", agents, num_episodes=num_episodes)
# 查看rewards可以看到每一局评估，每个选手最后的黄金数量

```

### Windows用户
cmd窗口 执行 setupAndInstall.bat


打开 jupyter-notebook
```python
from zerosum_env import make
env = make("carbon")

# 运行例子
env.run(["random", "random"])

# 训练例子
trainer = env.train([None, "random"])
obs = trainer.reset()
for _ in range(100):
    env.render()
    action = [{}, {}] # 给出智能体的动作
    obs, reward, done, info = trainer.step(action)
    if done:
        obs = trainer.reset()

# 评估例子
from zerosum_env import evaluate

def agent():
  return {}
# Which agents to run repeatedly.  Same as env.run(agents)
agents = ["random", agent]

# How many times to run them.
num_episodes = 2

rewards, jsons, htmls, errors = evaluate("carbon", agents, num_episodes=num_episodes)
# 查看rewards可以看到每一局评估，每个选手最后的黄金数量

# render例子
# 建议在 carbon.ipynb 修改，资源文件有特定路径
env = make("carbon", debug=True)
env.run([agent, "random"])
env.render(mode="ipython", width=1000, height=800) 

```