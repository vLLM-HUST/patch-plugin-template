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
   python tools/init_plugin.py \
     --name my-plugin \
     --maintainer-name "Your Name" \
     --maintainer-github your-login \
     --advisor-status unknown
   ```

   它会把 `example-plugin` / `example_plugin` / `EXAMPLE_PLUGIN` 全部改掉、重命名包目录,并删除这个
   工具。`--dry-run` 先预览,`--keep-tool` 保留工具。只有在确认不存在指导老师角色时才使用
   `--advisor-status none`;尚未确认时使用 `unknown`。两者不能混用。
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
| Manifest `0.3-experimental` 加独占的 `resource_claims` | 让管理器在启动前就拒绝两个替换同一宿主函数的插件。测试会检查声明、入口点和 `plugin.py` 三者一致 |
| 差分测试 | 运行时补丁证明行为等价最有力的证据 |
| `tools/init_plugin.py` | GitHub 模板不会替换变量 |
| `docs/PITFALLS.md`、`docs/REPORT_TEMPLATE.md` | 经验教训,以及要求同时写优势和局限的报告骨架 |
| `MOD_METADATA.json` | 公开主仓、直接负责人、指导关系状态、生命周期边界、适用范围和已资格化证据 |

## 仓库元数据契约

`MOD_METADATA.json` 是 MOD 的机器可读摘要,必须与 README 和 extension manifest 保持一致。
从模板生成的仓库在送审前必须写清:

- `vLLM-HUST` 下的公开 canonical repository,不把私有来源仓库或本地路径写成主仓;
- 至少一位直接负责人;
- 指导关系明确为 `none`、`unknown`,或 `declared` 且列出姓名和关系;GitHub 账号在已知时填写,不得猜测;
- `default_enabled: false`、启用契约和回滚契约;
- 单一机制范围与 workload-qualified 证据;
- 任何性能结论都绑定父仓与依赖提交、dirty 状态、硬件、模型、运行环境、图模式、
  入口命令、重复次数和 evidence label。

可保留历史来源提交哈希,但不得把私有组织描述成 canonical home。microbenchmark、simulation、
replay 和 projected profile 必须按真实证据类型标注,不能改写为线上端到端收益。

## Manifest 版本

manifest 是 `vllm-hust-extension-v0.3.json`(`0.3-experimental`),扩展管理器会优先找它,其次才是 `v0.2`。
0.3 保留 0.2 的全部字段,新增 `resource_claims` 和 `requires_extensions`,这两个字段在 0.2 下不合法。
0.3 目前处于兼容性冻结,不是稳定的 v1 承诺,详见 [`extension-manager`](https://github.com/vLLM-HUST/extension-manager)
的 `docs/manifest-0.3-experimental.md`。

示例独占声明了 `example-host.worker.compute`。**要和 `plugin.py` 里四个 `TODO` 常量一起改**:声明没有指向你
真正替换的函数时,测试会失败。

## 刻意不包含

没有压测框架、没有宿主相关代码、不下任何收益结论。补丁是否有用,要在真实服务路径上测,见 PITFALLS。
