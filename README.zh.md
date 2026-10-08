# vLLM-HUST 补丁插件模板

用于创建**默认关闭、单一机制的运行时补丁插件**的 GitHub 模板:通过 `vllm.general_plugins` 入口,
在运行时替换宿主的一个函数,而不是拷贝一份改过的宿主代码。

它和 [`extension-template`](https://github.com/vLLM-HUST/extension-template) 互补:后者管扩展的
形态和 manifest,本模板管**怎么安全地给宿主函数打补丁,以及怎么证明补丁真的在起作用**。
结构里沉淀了真实抽取项目踩过的坑,见 [docs/PITFALLS.md](docs/PITFALLS.md)。

## 使用

1. 点击 **Use this template**,克隆新仓库。
2. 就地替换占位名:

   ```bash
   python tools/init_plugin.py --name my-plugin
   ```

   它会把 `example-plugin` / `example_plugin` / `EXAMPLE_PLUGIN` 全部改掉、重命名包目录,并删除这个
   工具。`--dry-run` 先预览,`--keep-tool` 保留工具。
3. 修改 `src/<module>/plugin.py`:四个 `TODO` 常量和 `_make_replacement`。
4. 把 `tests/fake_host.py` 换成你要替换的宿主代码的**逐字拷贝**,保留差分测试,它会在大量随机输入上
   对比你的替换和原函数。
5. `pip install -e ".[test]" && pytest`。
6. 按 [docs/REPORT_TEMPLATE.md](docs/REPORT_TEMPLATE.md) 写报告,只写**实测**结果,包括没用的部分。

## 包含什么

| 部分 | 作用 |
| --- | --- |
| 默认关闭的 `register()`,`..._ENABLE`、`..._KILL_SWITCH`(kill switch 优先) | 被发现的插件在被要求之前什么都不做,线上必须能一键关掉 |
| 源码守卫(`inspect.getsource`) | 宿主不认识或已优化时拒绝安装,不做推测性补丁 |
| 带 `pid` 的 `installed` 与 `runtime_effective` 事件 | "补丁装了"和"补丁跑了"是两件事,pid 说明是哪个进程 |
| `bootstrap.child_entry` | 让补丁进入宿主用 `spawn` 启动的进程 |
| 差分测试 | 运行时补丁证明行为等价最有力的证据 |
| `tools/init_plugin.py` | GitHub 模板不会替换变量 |
| `docs/PITFALLS.md`、`docs/REPORT_TEMPLATE.md` | 经验教训,以及要求同时写优势和局限的报告骨架 |

## 刻意不包含

没有压测框架、没有宿主相关代码、不下任何收益结论。补丁是否有用,要在真实服务路径上测,见 PITFALLS。
